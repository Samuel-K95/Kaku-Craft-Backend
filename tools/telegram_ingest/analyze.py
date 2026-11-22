"""Caption heuristics + optional Cloudflare Workers AI vision enrichment."""

from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .parse_export import ExportAlbum, resolve_photo
from .price_rules import price_for, production_days_for

CATEGORY_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("keychain-dolls", ("key chain", "keychain", "key-chain")),
    ("baby", ("baby hat", "baby cardigan", "baby sweater", "baby")),
    ("cardigans", ("cardigan", "shrug", "two way")),
    ("sweaters", ("sweater", "crop top", "crochet top", "sleeve crop", "swimsuit", "top")),
    ("beanies", ("beanie", "hat")),
    ("handbags", ("handbag", "bag", "purse")),
    ("scarves", ("scarf", "wrap")),
    ("gloves", ("glove", "mitten")),
    ("socks", ("sock", "bootie", "slipper")),
    ("blankets", ("blanket", "throw")),
    ("small-dolls", ("doll", "amigurumi")),
]

CF_MODEL = "@cf/meta/llama-4-scout-17b-16e-instruct"
ALLOWED_SLUGS = {slug for slug, _ in CATEGORY_KEYWORDS}


@dataclass
class AnalyzedProduct:
    source_key: str
    name: str
    category_slug: str
    description: str
    price: int
    production_days: int
    size_note: str
    photo_rel_paths: list[str]
    caption: str
    analysis_source: str
    social_links: dict[str, str]


def _clean_caption(caption: str) -> str:
    text = re.sub(r"https?://\S+", " ", caption or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_price(caption: str) -> int | None:
    match = re.search(r"price\s*(\d+)\s*(?:birr)?", caption or "", re.I)
    if match:
        return int(match.group(1))
    return None


def _guess_category(caption: str) -> str:
    lower = (caption or "").lower()
    for slug, keywords in CATEGORY_KEYWORDS:
        if any(k in lower for k in keywords):
            return slug
    return "cardigans"


def _guess_name(caption: str, category_slug: str) -> str:
    text = _clean_caption(caption)
    if not text or text.lower().startswith("http"):
        pretty = category_slug.replace("-", " ").title()
        return f"Handcrafted {pretty}"

    # Prefer first meaningful clause before Order/Price/Dm
    first = re.split(r"\b(?:Order|Price|Dm)\b", text, maxsplit=1, flags=re.I)[0].strip(" -–|")
    first = re.sub(r"^custom made\s+", "", first, flags=re.I).strip()
    first = re.sub(r"\s+", " ", first).strip(" .,")
    if first:
        # Title-ish without destroying intentional casing much
        return first[0].upper() + first[1:]
    return text[:80]


def _build_description(name: str, caption: str, category_slug: str) -> str:
    clean = _clean_caption(caption)
    base = (
        f"{name} — handmade crochet from ከኩ craft (Keku craft). "
        f"Custom orders welcome; choose your colors and fit."
    )
    if clean and not clean.lower().startswith("http"):
        return f"{clean}. {base}"
    return f"{base} Category: {category_slug.replace('-', ' ')}."


def _cf_credentials() -> tuple[str, str] | None:
    account = os.environ.get("CF_ACCOUNT_ID", "").strip()
    token = os.environ.get("CF_API_TOKEN", "").strip()
    if account and token:
        return account, token
    return None


def _call_workers_ai(image_path: Path, caption: str) -> dict[str, Any] | None:
    creds = _cf_credentials()
    if not creds:
        return None
    account_id, token = creds
    if not image_path.exists():
        return None

    b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
    prompt = (
        "You classify handmade crochet/jewelry product photos for an Ethiopian shop. "
        "Return ONLY compact JSON with keys: "
        "name (string), category_slug (one of: "
        + ", ".join(sorted(ALLOWED_SLUGS))
        + "), description (1-2 sentences), price_etb (integer guess if unknown), "
        "production_days (integer 3-30). "
        f"Caption context: {caption[:400]!r}"
    )
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            }
        ],
        "max_tokens": 400,
    }
    url = (
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}"
        f"/ai/run/{CF_MODEL}"
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None

    result = body.get("result") or {}
    raw = result.get("response") or result.get("text") or ""
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return None
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def analyze_album(
    album: ExportAlbum,
    export_dir: str | Path,
    use_ai: bool = True,
    fallback_category: str | None = None,
) -> AnalyzedProduct:
    caption = album.caption or ""
    thin_caption = (not caption.strip()) or caption.strip().lower().startswith("http")
    category = _guess_category(caption) if not thin_caption else (fallback_category or "keychain-dolls")
    name = _guess_name(caption, category)
    caption_price = _extract_price(caption)
    analysis_source = "caption" if not thin_caption else "heuristic"

    ai_data: dict[str, Any] | None = None
    # Call Workers AI for thin captions or missing prices.
    if use_ai and (thin_caption or not caption_price):
        first_photo = album.photo_rel_paths[0] if album.photo_rel_paths else ""
        if first_photo:
            ai_data = _call_workers_ai(resolve_photo(export_dir, first_photo), caption)

    ai_days = None
    if ai_data:
        analysis_source = "caption+workers_ai"
        ai_slug = str(ai_data.get("category_slug") or "").strip()
        if ai_slug in ALLOWED_SLUGS and thin_caption:
            category = ai_slug
        ai_name = str(ai_data.get("name") or "").strip()
        if ai_name and thin_caption:
            name = ai_name
        if not caption_price:
            try:
                caption_price = int(ai_data.get("price_etb") or 0) or None
            except (TypeError, ValueError):
                caption_price = None
        try:
            ai_days = int(ai_data.get("production_days") or 0) or None
        except (TypeError, ValueError):
            ai_days = None

    # Thin captions without AI: stable studio name
    if thin_caption and not ai_data:
        name = f"Studio Piece {album.source_key.split('-')[-1]}"
        analysis_source = "heuristic"

    price = price_for(category, caption_price)
    days = production_days_for(category, ai_days)
    description = _build_description(name, caption, category)
    if ai_data and ai_data.get("description") and (
        not caption.strip() or caption.strip().lower().startswith("http")
    ):
        description = str(ai_data["description"]).strip()

    social: dict[str, str] = {"telegram": "https://t.me/keku_craft"}
    # Preserve tiktok link from caption when present
    tiktok = re.search(r"https?://(?:vm|vt|www)\.tiktok\.com/\S+", caption or "")
    if tiktok:
        social["tiktok"] = tiktok.group(0).rstrip(").,")

    return AnalyzedProduct(
        source_key=album.source_key,
        name=name[:180],
        category_slug=category,
        description=description,
        price=price,
        production_days=days,
        size_note="Medium, Large, XL, XXL",
        photo_rel_paths=list(album.photo_rel_paths),
        caption=caption,
        analysis_source=analysis_source,
        social_links=social,
    )


def analyze_albums(
    albums: list[ExportAlbum],
    export_dir: str | Path,
    use_ai: bool = True,
) -> list[AnalyzedProduct]:
    results: list[AnalyzedProduct] = []
    prev_category: str | None = None
    for album in albums:
        item = analyze_album(
            album,
            export_dir,
            use_ai=use_ai,
            fallback_category=prev_category,
        )
        results.append(item)
        prev_category = item.category_slug
    return results


def analyzed_to_dict(item: AnalyzedProduct) -> dict[str, Any]:
    return asdict(item)

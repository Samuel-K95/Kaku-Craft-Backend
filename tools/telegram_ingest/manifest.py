"""Read/write reviewable ingest manifest JSON."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analyze import AnalyzedProduct, analyzed_to_dict


def default_manifest_path(tool_root: str | Path | None = None) -> Path:
    root = Path(tool_root) if tool_root else Path(__file__).resolve().parent
    out = root / "out"
    out.mkdir(parents=True, exist_ok=True)
    return out / "manifest.json"


def write_manifest(
    products: list[AnalyzedProduct],
    export_dir: str | Path,
    path: str | Path | None = None,
) -> Path:
    target = Path(path) if path else default_manifest_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "export_dir": str(Path(export_dir).resolve()),
        "count": len(products),
        "products": [analyzed_to_dict(p) for p in products],
    }
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return target


def read_manifest(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "products" not in data:
        raise ValueError(f"Invalid manifest: {path}")
    return data

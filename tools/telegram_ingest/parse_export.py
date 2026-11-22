"""Parse Telegram Desktop HTML export into photo albums + captions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path


@dataclass
class ExportAlbum:
    source_key: str
    message_ids: list[str] = field(default_factory=list)
    photo_rel_paths: list[str] = field(default_factory=list)
    caption: str = ""
    date_hint: str = ""


class _TelegramExportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.albums: list[ExportAlbum] = []
        self._in_message = False
        self._message_id = ""
        self._message_classes: list[str] = []
        self._in_text = False
        self._text_buf: list[str] = []
        self._current_photos: list[str] = []
        self._current_caption = ""
        self._pending_group: ExportAlbum | None = None
        self._capture_href = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k: (v or "") for k, v in attrs}
        classes = attr.get("class", "").split()

        if tag == "div" and "message" in classes and "default" in classes:
            self._flush_message()
            self._in_message = True
            self._message_id = attr.get("id", "")
            self._message_classes = classes
            self._current_photos = []
            self._current_caption = ""
            self._text_buf = []
            return

        if not self._in_message:
            return

        if tag == "div" and "text" in classes:
            self._in_text = True
            self._text_buf = []
            return

        if self._in_text and tag in {"br", "div", "p"}:
            self._text_buf.append(" ")
            return

        if tag == "a" and "photo_wrap" in classes:
            href = attr.get("href", "")
            if href.startswith("photos/") and "_thumb" not in href:
                self._current_photos.append(href.replace("\\", "/"))

    def handle_endtag(self, tag: str) -> None:
        if tag == "div" and self._in_text:
            raw = "".join(self._text_buf)
            text = re.sub(r"\s+", " ", raw).strip()
            if text:
                self._current_caption = text
            self._in_text = False
            self._text_buf = []

    def handle_data(self, data: str) -> None:
        if self._in_text:
            self._text_buf.append(data)

    def _flush_message(self) -> None:
        if not self._in_message:
            return
        self._in_message = False
        if not self._current_photos:
            return

        is_joined = "joined" in self._message_classes
        msg_num = self._message_id.replace("message", "") or "0"
        has_caption = bool(self._current_caption.strip())

        # Same Telegram media album: joined follow-ups without their own caption.
        # A joined message that carries a caption is a new product post.
        if is_joined and self._pending_group is not None and not has_caption:
            self._pending_group.photo_rel_paths.extend(self._current_photos)
            self._pending_group.message_ids.append(msg_num)
            return

        # Start a new album / product
        if self._pending_group is not None:
            self.albums.append(self._pending_group)

        self._pending_group = ExportAlbum(
            source_key=f"tg:msg-{msg_num}",
            message_ids=[msg_num],
            photo_rel_paths=list(self._current_photos),
            caption=self._current_caption,
        )

    def close(self) -> None:
        self._flush_message()
        if self._pending_group is not None:
            self.albums.append(self._pending_group)
            self._pending_group = None
        super().close()


def parse_export(export_dir: str | Path) -> list[ExportAlbum]:
    """Return albums with full-res photos (skips channel avatar-only noise)."""
    root = Path(export_dir).resolve()
    html_path = root / "messages.html"
    if not html_path.exists():
        raise FileNotFoundError(f"messages.html not found in {root}")

    parser = _TelegramExportParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    parser.close()

    albums: list[ExportAlbum] = []
    for album in parser.albums:
        # Drop channel profile photo (photo_1) with no product caption
        photos = [
            p
            for p in album.photo_rel_paths
            if not re.search(r"photo_1@", Path(p).name)
            or album.caption
        ]
        # Prefer excluding pure avatar message (id message6 style / photo_1 only, empty caption)
        if not photos:
            continue
        if (
            len(photos) == 1
            and "photo_1@" in photos[0]
            and not album.caption.strip()
        ):
            continue
        album.photo_rel_paths = photos
        albums.append(album)

    return albums


def resolve_photo(export_dir: str | Path, rel_path: str) -> Path:
    return Path(export_dir).resolve() / rel_path

"""
Parse a Telegram Desktop HTML export, analyze products, upsert into the DB.

Tooling lives in Backend/tools/telegram_ingest/ (separate from the Django apps).
"""

from __future__ import annotations

import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

BACKEND_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = BACKEND_ROOT.parent
TOOLS_ROOT = BACKEND_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from telegram_ingest.analyze import analyze_albums  # noqa: E402
from telegram_ingest.manifest import default_manifest_path, read_manifest, write_manifest  # noqa: E402
from telegram_ingest.parse_export import parse_export  # noqa: E402
from telegram_ingest.upsert_django import upsert_manifest  # noqa: E402


class Command(BaseCommand):
    help = "Ingest Telegram Desktop export photos into products (analyze + upsert)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--export",
            type=str,
            default=str(WORKSPACE_ROOT / "ChatExport_2026-11-22"),
            help="Path to Telegram HTML export folder (contains messages.html).",
        )
        parser.add_argument(
            "--manifest",
            type=str,
            default="",
            help="Manifest JSON path (default: tools/telegram_ingest/out/manifest.json).",
        )
        parser.add_argument(
            "--analyze-only",
            action="store_true",
            help="Parse + analyze and write manifest; do not touch the database.",
        )
        parser.add_argument(
            "--upsert",
            action="store_true",
            help="Upsert products from a freshly built or existing manifest.",
        )
        parser.add_argument(
            "--from-manifest",
            action="store_true",
            help="Skip parse/analyze; upsert using --manifest only.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print upsert actions without writing.",
        )
        parser.add_argument(
            "--no-ai",
            action="store_true",
            help="Disable Cloudflare Workers AI (caption heuristics only).",
        )

    def handle(self, *args, **options):
        export_dir = Path(options["export"]).resolve()
        if not export_dir.exists():
            raise CommandError(f"Export folder not found: {export_dir}")

        manifest_path = (
            Path(options["manifest"]).resolve()
            if options["manifest"]
            else default_manifest_path(TOOLS_ROOT / "telegram_ingest")
        )

        do_analyze = not options["from_manifest"]
        do_upsert = options["upsert"] or (not options["analyze_only"] and not options["from_manifest"])

        if options["analyze_only"]:
            do_upsert = False
        if options["from_manifest"]:
            do_analyze = False
            do_upsert = True

        if not do_analyze and not do_upsert:
            raise CommandError("Nothing to do. Use --analyze-only and/or --upsert.")

        if do_analyze:
            if not (export_dir / "messages.html").exists():
                raise CommandError(f"messages.html missing in {export_dir}")
            self.stdout.write(f"Parsing export: {export_dir}")
            albums = parse_export(export_dir)
            self.stdout.write(self.style.SUCCESS(f"  Found {len(albums)} photo albums"))
            products = analyze_albums(albums, export_dir, use_ai=not options["no_ai"])
            path = write_manifest(products, export_dir, manifest_path)
            self.stdout.write(self.style.SUCCESS(f"  Wrote manifest: {path}"))
            for p in products[:8]:
                self.stdout.write(
                    f"    • {p.source_key} | {p.category_slug} | {p.price} ETB | {p.name}"
                )
            if len(products) > 8:
                self.stdout.write(f"    … and {len(products) - 8} more")

        if do_upsert:
            if not manifest_path.exists():
                raise CommandError(f"Manifest not found: {manifest_path}. Run --analyze-only first.")
            manifest = read_manifest(manifest_path)
            self.stdout.write(
                f"{'Dry-run upsert' if options['dry_run'] else 'Upserting'} "
                f"{manifest.get('count', 0)} products from {manifest_path}"
            )
            results = upsert_manifest(manifest, dry_run=options["dry_run"])
            created = sum(1 for r in results if r["action"] == "create")
            updated = sum(1 for r in results if r["action"] == "update")
            for r in results:
                self.stdout.write(
                    f"  [{r['action']}] {r.get('slug', r['source_key'])} "
                    f"— {r['name']} ({r['category']}) {r['price']} ETB"
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Done. create={created} update={updated} dry_run={options['dry_run']}"
                )
            )

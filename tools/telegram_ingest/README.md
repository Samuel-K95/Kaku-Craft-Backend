# Telegram export → product ingest

Standalone tooling under `Backend/tools/` (not mixed into Django apps) that parses a Telegram Desktop HTML export, builds a reviewable manifest, and upserts into Django.

## Prerequisites

- Telegram export folder with `messages.html` + `photos/` (e.g. workspace `ChatExport_2026-11-22/`)
- Backend venv with Django deps
- Optional: Cloudflare Workers AI for thin/TikTok-only captions

```bash
set CF_ACCOUNT_ID=...
set CF_API_TOKEN=...
```

Vision model: `@cf/meta/llama-4-scout-17b-16e-instruct`  
Docs: https://developers.cloudflare.com/workers-ai/

## Commands (from Backend/)

```powershell
# Parse + analyze → tools/telegram_ingest/out/manifest.json
.\.venv\Scripts\python.exe manage.py ingest_telegram_export --export "..\ChatExport_2026-11-22" --analyze-only

# Dry-run upsert
.\.venv\Scripts\python.exe manage.py ingest_telegram_export --export "..\ChatExport_2026-11-22" --upsert --dry-run

# Real upsert
.\.venv\Scripts\python.exe manage.py ingest_telegram_export --export "..\ChatExport_2026-11-22" --upsert

# Skip Workers AI (caption heuristics only)
.\.venv\Scripts\python.exe manage.py ingest_telegram_export --export "..\ChatExport_2026-11-22" --upsert --no-ai
```

Seed categories first if needed:

```powershell
.\.venv\Scripts\python.exe manage.py seed_categories
```

## Outputs

- `tools/telegram_ingest/out/manifest.json` — editable before upsert
- Products keyed by `source_key` (`tg:msg-<id>`) for idempotent re-runs
- Size variants: Medium, Large, XL, XXL (2 stock each by default)

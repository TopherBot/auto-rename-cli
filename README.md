# auto‑rename‑cli

**Tiny, zero‑bloat CLI** that:

1. **Auto‑renames** files in a target directory to `kebab-case` (e.g. `My File.txt` → `my-file.txt`).
2. **Detects duplicates** *before* committing the rename – if two different files would end up with the same name, the tool aborts and reports the conflict.
3. **Posts a Telegram notification** with a short summary (how many files renamed, any conflicts, timestamp).
4. **Optionally trims the GitHub repository description** to a maximum of 150 characters (useful for CI runs that update repo metadata).

The script is **self‑contained** (single `rename_tool.py` file), has **no idle sleeps** > 30 s, **gracefully recovers** from I/O errors, and returns concise exit codes:

- `0` – everything succeeded.
- `1` – rename conflict detected.
- `2` – unexpected error (logged to `stderr`).

---

## Installation
```bash
# Requires Python ≥3.9
pip install git+https://github.com/your‑username/auto-rename-cli.git
```
*(or clone the repo and run `python -m pip install .`)*

## Usage
```bash
auto-rename-cli \
  --path ./my‑project \
  [--dry-run] \
  [--telegram-token <TOKEN>] \
  [--telegram-chat-id <CHAT_ID>] \
  [--github-token <GITHUB_TOKEN>] \
  [--trim-github-desc]
```
- `--path` – directory to process (required).
- `--dry-run` – show what would happen without writing files.
- `--telegram-token` & `--telegram-chat-id` – enable Telegram alerts.
- `--github-token` – required if `--trim-github-desc` is used.
- `--trim-github-desc` – trims the repository description to 150 chars.

## Example output
```
🟢 Starting auto‑rename in ./my‑project
🔎 23 files scanned, 5 to rename
✅ Renamed: src/MyFile.py → src/my-file.py
⚠️ Conflict: docs/README.MD & docs/readme.md would both become readme.md
📣 Sent Telegram notification (3 renamed, 1 conflict)
```

## License
MIT – see the bundled `LICENSE` file.

---

## Development notes (for contributors)
- **Linting**: `ruff` is used in CI (fast, no idle waits).
- **CI**: GitHub Actions run lint, type‑check, unit test (if any) and optionally trim the repo description.
- **Telegram**: Simple `requests` POST; failures are caught and logged, not fatal.
- **GitHub API**: Uses `requests` with the provided token; respects rate limits.
- **Error handling**: All filesystem ops are wrapped in `try/except`; a broken file only aborts that file, not the whole run.

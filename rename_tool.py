#!/usr/bin/env python3
"""auto‑rename‑cli – tiny file‑renamer with duplicate detection and Telegram alerts.

Features:
- Convert filenames to kebab‑case (lowercase, spaces/underscores → hyphens).
- Detect name collisions before renaming.
- Send a concise Telegram message.
- Optionally truncate the GitHub repo description.

Author: TopherBot <topherbot@proton.me>
License: MIT
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import requests

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def kebab_case(name: str) -> str:
    """Return a kebab‑case version of *name* (preserves extension)."""
    stem, ext = os.path.splitext(name)
    # Replace spaces/underscores with hyphens, collapse multiple hyphens, lower.
    new_stem = re.sub(r"[\s_]+", "-", stem)
    new_stem = re.sub(r"-+", "-", new_stem).lower()
    return f"{new_stem}{ext.lower()}"

def collect_targets(root: Path) -> List[Path]:
    """Return a flat list of all files under *root* (recursively)."""
    return [p for p in root.rglob("*") if p.is_file()]

def build_rename_map(files: List[Path]) -> Tuple[Dict[Path, Path], List[Tuple[Path, Path]]]:
    """Create a mapping of original → new paths.
    Returns (rename_map, conflicts).
    """
    rename_map: Dict[Path, Path] = {}
    seen: Dict[Path, Path] = {}
    conflicts: List[Tuple[Path, Path]] = []

    for f in files:
        new_name = kebab_case(f.name)
        new_path = f.with_name(new_name)
        if new_path == f:
            continue  # already ok
        if new_path in seen:
            conflicts.append((f, seen[new_path]))
        else:
            rename_map[f] = new_path
            seen[new_path] = f
    return rename_map, conflicts

def perform_renames(rename_map: Dict[Path, Path], dry_run: bool) -> List[Tuple[Path, Path]]:
    """Execute the renames. Returns a list of (old, new) that succeeded."""
    succeeded: List[Tuple[Path, Path]] = []
    for src, dst in rename_map.items():
        try:
            if dry_run:
                print(f"🟡 DRY‑RUN: {src} → {dst}")
            else:
                src.rename(dst)
                print(f"✅ Renamed: {src} → {dst}")
            succeeded.append((src, dst))
        except Exception as e:
            print(f"❌ Failed to rename {src} → {dst}: {e}", file=sys.stderr)
    return succeeded

def send_telegram(token: str, chat_id: str, message: str) -> None:
    """Post *message* to Telegram. Errors are logged, not raised."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, data=payload, timeout=5)
        if not resp.ok:
            print(f"⚠️ Telegram API error: {resp.status_code} {resp.text}", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ Telegram request failed: {e}", file=sys.stderr)

def trim_github_desc(token: str, repo: str, max_len: int = 150) -> None:
    """Trim the description of *repo* (owner/repo) to *max_len* characters.
    Uses the GitHub REST API (v3)."""
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    # Get current description
    get_url = f"https://api.github.com/repos/{repo}"
    try:
        cur = requests.get(get_url, headers=headers, timeout=5).json()
        desc = cur.get("description", "") or ""
        if len(desc) <= max_len:
            return  # nothing to do
        new_desc = desc[:max_len].rstrip()
        patch_url = f"https://api.github.com/repos/{repo}"
        data = {"description": new_desc}
        resp = requests.patch(patch_url, json=data, headers=headers, timeout=5)
        if resp.ok:
            print(f"🔧 Trimmed GitHub description to {len(new_desc)} chars.")
        else:
            print(f"⚠️ Failed to trim GitHub description: {resp.status_code} {resp.text}", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ GitHub API error: {e}", file=sys.stderr)

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Auto‑rename files to kebab‑case, detect duplicates, and send Telegram alerts.")
    parser.add_argument("--path", required=True, help="Root directory to process.")
    parser.add_argument("--dry-run", action="store_true", help="Do not actually rename files.")
    parser.add_argument("--telegram-token", help="Telegram bot token.")
    parser.add_argument("--telegram-chat-id", help="Telegram chat ID for notifications.")
    parser.add_argument("--github-token", help="GitHub token for description trim.")
    parser.add_argument("--repo", help="GitHub repo identifier 'owner/name' (required if --trim-github-desc).")
    parser.add_argument("--trim-github-desc", action="store_true", help="Trim repo description to 150 chars.")

    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"❌ Provided path is not a directory: {root}", file=sys.stderr)
        return 2

    print(f"🟢 Starting auto‑rename in {root}")
    files = collect_targets(root)
    rename_map, conflicts = build_rename_map(files)

    print(f"🔎 {len(files)} files scanned, {len(rename_map)} to rename, {len(conflicts)} conflicts detected")

    if conflicts:
        for a, b in conflicts:
            print(f"⚠️ Conflict: {a} ↔ {b} would both become {kebab_case(a.name)}", file=sys.stderr)
        # Abort before any rename to avoid partial state
        return 1

    succeeded = perform_renames(rename_map, args.dry_run)

    # Build Telegram message
    if args.telegram_token and args.telegram_chat_id:
        msg = (
            f"*Auto‑rename report*\n"
            f"Processed: {len(files)} files\n"
            f"Renamed: {len(succeeded)}\n"
            f"Conflicts: {len(conflicts)}\n"
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        send_telegram(args.telegram_token, args.telegram_chat_id, msg)

    # Optional GitHub description trim
    if args.trim_github_desc:
        if not (args.github_token and args.repo):
            print("⚠️ --trim-github-desc requires --github-token and --repo", file=sys.stderr)
        else:
            trim_github_desc(args.github_token, args.repo)

    return 0

if __name__ == "__main__":
    sys.exit(main())

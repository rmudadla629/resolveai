"""Preview or reset fictional state without changing credentials or fixtures."""

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

RUNTIME = Path(__file__).resolve().parent.parent / "runtime"
STATE_FILES = ("reviews.sqlite3", "traces.sqlite3")


def preview():
    return [name for name in STATE_FILES if (RUNTIME / name).exists()]


def reset(confirmation, server_stopped):
    if confirmation != "RESET-DEMO" or not server_stopped:
        raise ValueError("Stop ResolveAI, then supply --server-stopped --confirm RESET-DEMO.")
    files = preview()
    if not files:
        return None
    # Preserve consistent SQLite backups before removing any sandbox state.
    destination = RUNTIME / "backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination.mkdir(parents=True, mode=0o700)
    for name in files:
        source = sqlite3.connect(f"file:{(RUNTIME / name).resolve()}?mode=ro", uri=True)
        target = sqlite3.connect(destination / name)
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()
    (destination / "manifest.json").write_text(json.dumps({"backed_up": files, "credentials_preserved": True}, indent=2) + "\n")
    for name in files:
        (RUNTIME / name).unlink()
        for suffix in ("-wal", "-shm", "-journal"):
            (RUNTIME / (name + suffix)).unlink(missing_ok=True)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm", help="Use RESET-DEMO to reset; omit for preview only")
    parser.add_argument("--server-stopped", action="store_true", help="Confirm you stopped ResolveAI")
    args = parser.parse_args()
    print("Demo state files:", ", ".join(preview()) or "none")
    print("Reset clears cancellations, review requests/audit events, and traces. It restores JSON fixture statuses.")
    print("Reviewer and customer credentials, JSON fixtures, and evaluation reports are preserved.")
    if args.confirm is None:
        print("Preview only. Stop ResolveAI before running with --server-stopped --confirm RESET-DEMO.")
        return
    try:
        backup = reset(args.confirm, args.server_stopped)
    except ValueError as error:
        parser.error(str(error))
    print(f"Demo reset. Backup: {backup}" if backup else "No demo state to reset.")


if __name__ == "__main__":
    main()

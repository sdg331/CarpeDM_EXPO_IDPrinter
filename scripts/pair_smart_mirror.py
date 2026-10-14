"""Prepare private matching bridge settings without printing shared secrets."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import secrets
import shutil
from urllib.parse import urlsplit

from dotenv import dotenv_values, set_key

ROOT = Path(__file__).resolve().parent.parent


def base_url(value: str) -> str:
    parts = urlsplit(value)
    parts.port
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password or parts.path not in {"", "/"} or parts.query or parts.fragment:
        raise ValueError("Use a server base URL without credentials or paths")
    return value.rstrip("/")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kiosk-url", required=True)
    parser.add_argument("--mirror-url")
    parser.add_argument("--mirror-repo", type=Path, required=True)
    args = parser.parse_args()
    kiosk_url = base_url(args.kiosk_url)
    mirror_url = base_url(args.mirror_url) if args.mirror_url else None
    mirror_env = args.mirror_repo.resolve() / "poc/backend/.env"
    if not mirror_env.parent.is_dir():
        raise SystemExit("MirrorTing poc/backend directory is missing")
    kiosk_env = ROOT / ".env"
    private = Path.home() / ".local/share/mirrorting-private"
    private.mkdir(parents=True, exist_ok=True)
    private.chmod(0o700)
    backup = private / "kiosk-env-before-bridge-20261013"
    if kiosk_env.exists() and not backup.exists():
        shutil.copy2(kiosk_env, backup)
        backup.chmod(0o600)
    existing = dotenv_values(kiosk_env)
    token = existing.get("KIOSK_BRIDGE_TOKEN") or secrets.token_urlsafe(48)
    if len(token) < 32:
        token = secrets.token_urlsafe(48)
    kiosk_env.touch(exist_ok=True)
    mirror_env.touch(exist_ok=True)
    kiosk_env.chmod(0o600)
    mirror_env.chmod(0o600)
    set_key(str(kiosk_env), "KIOSK_BRIDGE_TOKEN", token)
    set_key(str(kiosk_env), "KIOSK_HOST", "0.0.0.0")
    if mirror_url:
        set_key(str(kiosk_env), "KIOSK_MIRRORTING_URL", mirror_url)
    set_key(str(mirror_env), "MIRROR_TING_IDPRINTER_BASE_URL", kiosk_url)
    set_key(str(mirror_env), "MIRROR_TING_IDPRINTER_BRIDGE_TOKEN", token)
    print("Matching private bridge settings prepared; no credentials printed.")
    print("Kiosk bridge:", kiosk_url)
    print("MirrorTing server:", mirror_url or "awaiting the actual server address")
    print("MirrorTing settings file:", mirror_env)
    print("Restart both servers after applying their environment files.")


if __name__ == "__main__":
    main()

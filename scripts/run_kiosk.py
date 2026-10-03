"""Start one kiosk worker with project-local configuration on any OS."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> None:
    from dotenv import load_dotenv
    import uvicorn

    load_dotenv(ROOT / ".env", override=False)
    parser = argparse.ArgumentParser(description="MIRRORTING WORKS kiosk server")
    parser.add_argument("--host", default=os.getenv("KIOSK_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=os.getenv("KIOSK_PORT", "8002"))
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    os.chdir(ROOT)
    # Temporary profile/preview storage belongs to this one process.
    uvicorn.run("backend.app:app", host=args.host, port=args.port, workers=1,
                proxy_headers=False, access_log=False)


if __name__ == "__main__":
    main()

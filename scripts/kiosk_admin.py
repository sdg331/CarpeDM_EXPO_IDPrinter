"""Local operator commands. No network admin endpoint or visitor credentials."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def public_operation(operation: dict) -> dict:
    # Never print stored visitor information, tokens, or report content.
    allowed = ("operation_id", "kind", "status", "retryable", "error_code", "created_at", "updated_at")
    return {key: operation.get(key) for key in allowed if key in operation}


def main() -> int:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=False)
    from backend.store import KioskStore, StoreError

    parser = argparse.ArgumentParser(description="키오스크 로컬 운영 도구")
    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser("operation", help="작업 상태 확인 (개인정보 제외)")
    status.add_argument("operation_id")
    resolve = commands.add_parser("resolve-print", help="실물 확인 후 결과 불명 출력 작업 해소")
    resolve.add_argument("operation_id")
    resolve.add_argument("--outcome", required=True, choices=("printed", "not_printed"))
    resolve.add_argument("--confirm-checked", action="store_true", help="실제 종이를 확인했고 결과를 확정함")
    purge = commands.add_parser("purge-expired", help="설정된 보관 기간이 지난 방문자 정보 삭제")
    purge.add_argument("--confirm", action="store_true", help="만료된 개인정보 삭제 실행")
    args = parser.parse_args()
    store = KioskStore()
    store.init()

    try:
        if args.command == "operation":
            op = store.get_operation(args.operation_id)
            if op is None:
                print("해당 작업을 찾을 수 없습니다.", file=sys.stderr)
                return 1
            print(json.dumps(public_operation(op), ensure_ascii=False, indent=2))
        elif args.command == "resolve-print":
            if not args.confirm_checked:
                parser.error("실제 출력물을 확인한 후 --confirm-checked를 지정하세요")
            op = store.resolve_unknown_operation(args.operation_id, outcome=args.outcome)
            print(json.dumps(public_operation(op), ensure_ascii=False, indent=2))
            print("키오스크에서 작업 상태 다시 확인을 누르세요. not_printed는 자동 인쇄하지 않습니다.")
        else:
            if not args.confirm:
                parser.error("만료된 방문자 정보 삭제를 실행하려면 --confirm을 지정하세요")
            hours = float(os.getenv("KIOSK_SESSION_RETENTION_HOURS", "24"))
            result = store.purge_expired(retention_hours=hours)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (StoreError, ValueError, LookupError, RuntimeError) as exc:
        print(f"작업을 처리하지 못했습니다 ({type(exc).__name__}). 현재 상태와 작업 ID를 확인하세요.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env bash
set -euo pipefail
KIOSK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KIOSK_PYTHON="$KIOSK_ROOT/.venv/bin/python"
if [ ! -x "$KIOSK_PYTHON" ]; then
  echo "Python 환경이 없습니다. README의 설치 절차를 먼저 실행하세요." >&2
  exit 1
fi
exec "$KIOSK_PYTHON" "$KIOSK_ROOT/scripts/run_kiosk.py" "$@"

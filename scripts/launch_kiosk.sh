#!/usr/bin/env bash
set -euo pipefail
KIOSK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$KIOSK_ROOT"
systemctl --user start mirrorting-idprinter.service
for KIOSK_ATTEMPT in {1..30}; do
  if curl --noproxy '*' --fail --silent --max-time 2 http://127.0.0.1:8002/api/health >/dev/null; then
    break
  fi
  sleep 1
done
curl --noproxy '*' --fail --silent --max-time 2 http://127.0.0.1:8002/api/health >/dev/null
exec chromium --kiosk --ozone-platform=wayland --touch-events=enabled \
  --disable-features=Translate --no-first-run --no-default-browser-check \
  --disable-session-crashed-bubble --use-fake-ui-for-media-stream \
  --autoplay-policy=no-user-gesture-required \
  --user-data-dir="$HOME/.config/chromium-mirrorting-kiosk-latest" \
  http://127.0.0.1:8002/

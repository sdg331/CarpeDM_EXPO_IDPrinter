#!/usr/bin/env bash
# YuNet(얼굴 검출) · SFace(128차원 임베딩) 모델을 models/에 캐시한다.
# 전시장에는 인터넷이 없으므로 최초 1회만 받아두고 이후에는 오프라인으로 동작한다.
# 파이 이관 시에도 이 스크립트를 그대로 쓴다.
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p models

ZOO="https://github.com/opencv/opencv_zoo/raw/main/models"

fetch() {
  local url="$1" out="models/$2" min="$3"
  if [ -f "$out" ] && [ "$(wc -c <"$out")" -ge "$min" ]; then
    echo "skip  $2 (이미 있음)"
    return
  fi
  echo "받는 중  $2"
  curl -fsSL "$url" -o "$out"

  # git-lfs 포인터가 내려온 경우를 걸러낸다(수백 바이트짜리 텍스트).
  local size
  size="$(wc -c <"$out")"
  if [ "$size" -lt "$min" ]; then
    echo "실패: $2 가 $size 바이트뿐이다. LFS 포인터일 수 있다." >&2
    head -c 200 "$out" >&2; echo >&2
    rm -f "$out"
    exit 1
  fi
  echo "완료  $2 ($size 바이트)"
}

fetch "$ZOO/face_detection_yunet/face_detection_yunet_2023mar.onnx" \
      "face_detection_yunet_2023mar.onnx" 100000

fetch "$ZOO/face_recognition_sface/face_recognition_sface_2021dec.onnx" \
      "face_recognition_sface_2021dec.onnx" 30000000

echo
ls -lh models/

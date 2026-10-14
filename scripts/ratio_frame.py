"""Bounded subprocess: one frame from stdin, no photo/landmark persistence."""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backend.face_ratios import FaceRatioEngine, RatioError, load_references, rank_ratios


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gender", choices=["any", "male", "female"], default="any")
    parser.add_argument("--box", type=float, nargs=4)
    parser.add_argument("--landmarks-only", action="store_true")
    args = parser.parse_args()
    try:
        raw = sys.stdin.buffer.read(8 * 1024 * 1024 + 1)
        if len(raw) > 8 * 1024 * 1024:
            raise RatioError("IMAGE_TOO_LARGE")
        image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise RatioError("INVALID_IMAGE")
        if args.box and (not np.isfinite(args.box).all() or min(args.box[2:]) <= 0):
            raise RatioError("LANDMARK_QUALITY_FAILED")
        references = None if args.landmarks_only else load_references()
        engine = FaceRatioEngine()
        try:
            features, landmarks = engine.extract(image, target_box=args.box, landmarks_only=args.landmarks_only)
        finally:
            engine.close()
        result = {} if args.landmarks_only else rank_ratios(features, references, args.gender)
        result.update(ok=True, landmarks=np.round(landmarks, 5).tolist())
    except RatioError as exc:
        result = {"ok": False, "error": str(exc)}
    except Exception:
        result = {"ok": False, "error": "LANDMARK_ENGINE_UNAVAILABLE"}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

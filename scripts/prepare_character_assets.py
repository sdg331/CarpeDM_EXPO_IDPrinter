#!/usr/bin/env python3
"""Normalize selected portraits for display without rotating or reshaping faces."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.face import FaceEngine

SIZE = (1086, 1448)
HEAD_MARGIN = .05
FACE_HEIGHT = .45


def head_top(image: np.ndarray) -> int:
    height, width = image.shape[:2]
    # shortcut: dark-haired portraits on pale backgrounds; use segmentation for light hair/backgrounds.
    gray = cv2.cvtColor(image[:height // 2, width // 5:width * 4 // 5], cv2.COLOR_BGR2GRAY)
    rows = np.flatnonzero((gray < 190).sum(axis=1) >= 12)
    if not len(rows):
        raise ValueError("Cannot locate hair against the background")
    return int(rows[0])


def framing_transform(row: np.ndarray, width: int, height: int, top: int) -> np.ndarray:
    eyes = row[4:8].reshape(2, 2).mean(axis=0)
    if row[3] <= 0 or not 0 < eyes[0] < width or not 0 < eyes[1] < height:
        raise ValueError("Invalid face geometry")
    if not 0 <= top < eyes[1]:
        raise ValueError("Invalid hair geometry")
    # Keep the crown visible while covering both side edges and the photo bottom.
    scale = max(FACE_HEIGHT * SIZE[1] / row[3],
                SIZE[0] / (2 * min(eyes[0], width - eyes[0])),
                (1 - HEAD_MARGIN) * SIZE[1] / (height - top))
    return np.array([[scale, 0, SIZE[0] / 2 - scale * eyes[0]],
                     [0, scale, HEAD_MARGIN * SIZE[1] - scale * top]], np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    ids = [f"char_{i:02d}" for i in range(1, 9)]
    if sorted(p.stem for p in args.source.glob("char_*.png")) != ids:
        parser.error("Source must contain exactly char_01.png through char_08.png")
    if args.source.resolve() == args.destination.resolve():
        parser.error("Preserve originals: source and destination must differ")
    engine = FaceEngine()
    prepared, records = [], []
    for cid in ids:
        image = cv2.imread(str(args.source / f"{cid}.png"))
        if image is None:
            raise ValueError(f"Unreadable source: {cid}")
        _, detection = engine.embed_single(image, strict=True)
        height, width = image.shape[:2]
        top = head_top(image)
        matrix = framing_transform(detection.row, width, height, top)
        result = cv2.warpAffine(image, matrix, SIZE, flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_REPLICATE)
        _, after = engine.embed_single(result, strict=True)
        eyes = after.row[4:8].reshape(2, 2).mean(axis=0)
        assert abs(eyes[0] / SIZE[0] - .5) < .015, cid
        measured_top = head_top(result) / SIZE[1]
        assert abs(measured_top - HEAD_MARGIN) < .01, cid
        assert abs(after.row[3] / SIZE[1] - FACE_HEIGHT) < .03, cid
        prepared.append((cid, result))
        records.append({"id": cid, "transform": matrix.tolist(),
                        "source_sha256": hashlib.sha256((args.source / f"{cid}.png").read_bytes()).hexdigest(),
                        "eye_height": float(eyes[1] / SIZE[1]),
                        "head_margin": measured_top,
                        "face_height": float(after.row[3] / SIZE[1]), "rotation": False})
    args.destination.mkdir(parents=True, exist_ok=True)
    for cid, image in prepared:
        Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)).save(args.destination / f"{cid}.png")
        Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)).resize((192, 256), Image.Resampling.LANCZOS).save(args.destination / f"{cid}.webp")
    (args.destination / "framing.json").write_text(json.dumps(records, indent=2) + "\n")
    print(f"Prepared {len(prepared)} portraits; uniform scale/translation, no rotation")


if __name__ == "__main__":
    main()

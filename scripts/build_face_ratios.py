"""Build geometry references from the current public eight character images."""
import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backend.face_ratios import FaceRatioEngine, FEATURE_NAMES, MODEL_SHA256, REFERENCES, SCHEMA, sha256


def main():
    genders = json.loads((ROOT / "assets/characters/genders.json").read_text())
    engine = FaceRatioEngine()
    rows = []
    try:
        for cid in sorted(genders):
            path = ROOT / "assets/characters" / f"{cid}.png"
            features, _ = engine.extract(cv2.imread(str(path)))
            rows.append({"id": cid, "gender": genders[cid], "sourceSha256": sha256(path),
                         "features": features.tolist()})
            print(f"{cid}: 478 landmarks, {len(features)} ratios", flush=True)
    finally:
        engine.close()
    data = {"schema": SCHEMA, "featureNames": FEATURE_NAMES,
            "modelSha256": MODEL_SHA256, "genderSha256": sha256(ROOT / "assets/characters/genders.json"),
            "characters": rows, "calibrated": False}
    temporary = REFERENCES.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(REFERENCES)
    print("Saved assets/face_ratios.json; experimental, not likeness accuracy validation")


if __name__ == "__main__":
    main()

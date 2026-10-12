#!/usr/bin/env python3
"""Evaluate LFW selection concentration with disjoint calibration/evaluation people.

Uses one image per identity. Writes aggregate diagnostics only; never installs
LFW photos or calibration into production assets. No likeness ground truth exists.
"""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backend.face import FaceEngine, MultipleFacesError, NoFaceError, Prototypes


def summarize(scores, ids):
    ordered = np.sort(scores, axis=1)
    margins = ordered[:, -1] - ordered[:, -2]
    counts = np.bincount(scores.argmax(axis=1), minlength=len(ids))
    return dict(n=len(scores), counts=dict(zip(ids, counts.tolist())),
                used=int(np.count_nonzero(counts)),
                largest_share=float(counts.max() / len(scores)),
                mean_margin=float(margins.mean()),
                fragile_count=int((margins < .02).sum()),
                fragile_share=float((margins < .02).mean()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    identities = {}
    for path in sorted(args.directory.rglob("*.jpg")):
        identities.setdefault(path.parent.name, path)
    if len(identities) < 1000:
        parser.error("Expected at least 1000 distinct LFW identity directories")
    paths = list(identities.values())
    np.random.default_rng(20261011).shuffle(paths)
    paths = paths[:1000]
    assert not {p.parent.name for p in paths[:200]} & {p.parent.name for p in paths[200:]}
    engine = FaceEngine()
    vectors = [[], []]
    failures = [Counter(), Counter()]
    for index, path in enumerate(paths):
        split = int(index >= 200)
        image = cv2.imread(str(path))
        if image is None:
            failures[split]["unreadable"] += 1
            continue
        try:
            vector, _ = engine.embed_single(image, strict=True)
        except (NoFaceError, MultipleFacesError) as exc:
            failures[split][type(exc).__name__] += 1
            continue
        vectors[split].append(vector)
        if (index + 1) % 100 == 0:
            print(f"Processed {index + 1}/1000", flush=True)
    if not vectors[0] or not vectors[1]:
        raise SystemExit("No usable faces in calibration or evaluation split")
    calibration, evaluation = [np.asarray(v, np.float32) for v in vectors]
    proto = Prototypes.load(ROOT / "assets/prototypes.npz")
    domain_path = ROOT / "assets/domain_mean.npz"
    mu_current = None
    if domain_path.exists():
        with np.load(domain_path, allow_pickle=False) as domain:
            mu_current = domain["mu_real"].astype(np.float32)
    result = dict(dataset="jessicali9530/lfw-dataset", seed=20261011,
                  sampling="one photo per identity, 200 calibration / 800 evaluation",
                  selected_manifest_sha256=hashlib.sha256("\n".join(str(p.relative_to(args.directory)) for p in paths).encode()).hexdigest(),
                  prototypes_sha256=hashlib.sha256((ROOT / "assets/prototypes.npz").read_bytes()).hexdigest(),
                  calibration_n=len(calibration), evaluation_n=len(evaluation),
                  failures=[dict(f) for f in failures], style_n=proto.style_n,
                  production_calibrated=mu_current is not None)
    for label, scores in (
        ("raw", [proto.raw_scores(v) for v in evaluation]),
        ("production", [proto.match_scores(v, mu_current) for v in evaluation]),
        ("heldout_calibration", [proto.match_scores(v, calibration.mean(axis=0)) for v in evaluation]),
    ):
        result[label] = summarize(np.asarray(scores), proto.ids)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

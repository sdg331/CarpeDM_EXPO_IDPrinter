"""Fit public-face domain/distribution correction; save aggregate statistics only."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backend.face import FaceEngine, NoFaceError, MultipleFacesError
from backend.face_ratios import (BALANCE, BALANCE_METHOD, FEATURE_NAMES, MODEL_SHA256, REFERENCES,
                                FaceRatioEngine, RatioError, balanced_errors, load_references, sha256)


def fit_balance(train, references):
    vectors = np.array([row["features"] for row in references["characters"]])
    data = {"method": BALANCE_METHOD, "featureNames": FEATURE_NAMES,
            "modelSha256": MODEL_SHA256, "referencesSha256": sha256(REFERENCES),
            "realMean": train.mean(0).tolist(), "realScale": np.maximum(train.std(0), .015).tolist(),
            "characterMean": vectors.mean(0).tolist(),
            "characterScale": np.maximum(vectors.std(0), .015).tolist(),
            "bias": {}, "likenessValidated": False}
    costs = balanced_errors(train[:, None, :], vectors[None, :, :], data).mean(2)
    for gender in ("any", "male", "female"):
        eligible = [i for i, row in enumerate(references["characters"])
                    if gender == "any" or row["gender"] == gender]
        c = costs[:, eligible]
        # Entropy-regularized equal prior, learned on fitting people only.
        # This is distribution balancing, not human likeness supervision.
        def objective(bias):
            logits = -(c + bias) / .15
            normalizer = logsumexp(logits, axis=1)
            probabilities = np.exp(logits - normalizer[:, None])
            return float(.15 * normalizer.mean() + bias.mean()), 1 / len(eligible) - probabilities.mean(0)
        fit = minimize(objective, np.zeros(len(eligible)), jac=True, method="L-BFGS-B",
                       options={"gtol": 1e-9, "maxiter": 1000})
        if not fit.success or not np.isfinite(fit.x).all():
            raise ValueError("Distribution fitting failed")
        data["bias"][gender] = fit.x.tolist()
    return data


def counts(features, references, balance=None):
    vectors = np.array([row["features"] for row in references["characters"]])
    result = {}
    for gender in ("any", "male", "female"):
        indices = [i for i, row in enumerate(references["characters"])
                   if gender == "any" or row["gender"] == gender]
        if balance is None:
            costs = (((features[:, None, :] - vectors) / np.maximum(vectors.std(0), .03)) ** 2).mean(2)
        else:
            costs = balanced_errors(features[:, None, :], vectors[None, :, :], balance).mean(2)
        eligible_costs = costs[:, indices]
        if balance is not None:
            eligible_costs = eligible_costs + balance["bias"][gender]
        winners = np.asarray(indices)[eligible_costs.argmin(1)]
        tally = Counter(references["characters"][i]["id"] for i in winners)
        result[gender] = {references["characters"][i]["id"]: tally[references["characters"][i]["id"]]
                          for i in indices}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--faces", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=640)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not args.faces.is_dir() or not 512 <= args.limit <= 2000:
        parser.error("An existing public face directory and limit 512..2000 are required")
    unique = {}
    for path in sorted(args.faces.rglob("*.jpg")):
        unique.setdefault(path.parent.name, path)
    paths = list(unique.values())
    np.random.default_rng(20261013).shuffle(paths)
    paths = paths[:args.limit]
    references = load_references()
    engine, sface = FaceRatioEngine(), FaceEngine()
    diagnostic, pool, failures = [], [], Counter()
    try:
        for index, path in enumerate(paths):
            try:
                image = cv2.imread(str(path))
                sface.embed_single(image)
                features, _ = engine.extract(image)
                (diagnostic if index < 128 else pool).append(features)
            except (RatioError, NoFaceError, MultipleFacesError) as exc:
                failures[str(exc) if isinstance(exc, RatioError) else type(exc).__name__] += 1
            if (index + 1) % 128 == 0:
                print(f"Processed {index + 1}/{len(paths)} public faces", flush=True)
    finally:
        engine.close()
    # Disjoint people: old diagnostic set, 100 validation people, remaining fit.
    validation, train = np.array(pool[:100]), np.array(pool[100:])
    if len(validation) != 100 or len(train) < 200 or not diagnostic:
        raise ValueError("Not enough valid independent public faces; balance was not replaced")
    balance = fit_balance(train, references)
    report = {"method": BALANCE_METHOD, "source": "public LFW local cache", "seed": 20261013,
              "selected": len(paths), "fitCount": len(train), "validationCount": len(validation),
              "diagnosticCount": len(diagnostic), "failures": dict(failures), "likenessValidated": False,
              "fitAfter": counts(train, references, balance),
              "validationBefore": counts(validation, references),
              "validationAfter": counts(validation, references, balance),
              "diagnosticBefore": counts(np.array(diagnostic), references),
              "diagnosticAfter": counts(np.array(diagnostic), references, balance)}
    for gender, distribution in report["validationAfter"].items():
        maximum_share = max(distribution.values()) / len(validation)
        if min(distribution.values()) == 0 or maximum_share > (.35 if gender == "any" else .5):
            raise ValueError("Held-out distribution gate failed; balance was not replaced")
    balance["sample"] = {key: report[key] for key in ("source", "seed", "selected", "fitCount", "validationCount")}
    for path, data in ((args.report, report), (BALANCE, balance)):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2) + "\n")
        temporary.replace(path)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()

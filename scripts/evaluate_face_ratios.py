"""Public reference robustness + optional LFW diagnostics; not likeness accuracy."""
import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backend.face_ratios import FaceRatioEngine, RatioError, load_references, rank_ratios
from backend.face import FaceEngine, Prototypes, NoFaceError, MultipleFacesError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--faces", type=Path)
    parser.add_argument("--limit", type=int, default=128)
    args = parser.parse_args()
    if not 1 <= args.limit <= 1000:
        parser.error("limit must be between 1 and 1000")
    if args.faces and not args.faces.is_dir():
        parser.error("Public face directory does not exist")
    references = load_references()
    ratio = FaceRatioEngine()
    sface = FaceEngine()
    proto = Prototypes.load(ROOT / "assets/prototypes.npz")
    rows = []
    failures = Counter()
    used_ratio, used_sface = Counter(), Counter()
    times, agreements = [], []
    try:
        for row in references["characters"]:
            image = cv2.imread(str(ROOT / "assets/characters" / f"{row['id']}.png"))
            for name, changed in [("original",image),("flip",cv2.flip(image,1)),
                                  ("bright",cv2.convertScaleAbs(image,alpha=1.2)),
                                  ("dim",cv2.convertScaleAbs(image,alpha=.8))]:
                try:
                    vector, _ = ratio.extract(changed)
                    ranked = rank_ratios(vector,references,balanced=False)
                    rows.append({"id":row["id"],"variant":name,"top":ranked["characterId"],"margin":ranked["margin"]})
                except RatioError as exc:
                    rows.append({"id":row["id"],"variant":name,"error":str(exc)})
        selected = []
        if args.faces:
            unique = {}
            for path in sorted(args.faces.rglob("*.jpg")):
                unique.setdefault(path.parent.name,path)
            selected = list(unique.values())
            np.random.default_rng(20261013).shuffle(selected)
            selected = selected[:args.limit]
        for index,path in enumerate(selected):
            image = cv2.imread(str(path))
            try:
                embedding, _ = sface.embed_single(image)
                started = time.perf_counter()
                vector, _ = ratio.extract(image)
                times.append((time.perf_counter()-started)*1000)
                ranked = rank_ratios(vector,references)
                sface_id = proto.ids[int(proto.match_scores(embedding).argmax())]
                used_ratio[ranked["characterId"]] += 1
                used_sface[sface_id] += 1
                agreements.append(sface_id == ranked["characterId"])
            except (RatioError, NoFaceError, MultipleFacesError) as exc:
                failures[str(exc) if isinstance(exc,RatioError) else type(exc).__name__] += 1
            if (index+1)%32 == 0:
                print(f"Processed {index+1}/{len(selected)} public faces",flush=True)
    finally:
        ratio.close()
    result = {"experimental":True,"calibrated":False,"likenessGroundTruth":False,
              "opencvVersion":cv2.__version__,"references":rows,
              "referenceMatches":sum(r.get("top")==r["id"] for r in rows),
              "publicFaces":{"selected":len(selected),"compared":len(agreements),"failures":dict(failures),
                             "ratioCounts":dict(used_ratio),"sfaceCounts":dict(used_sface),
                             "agreementShare":float(np.mean(agreements)) if agreements else None,
                             "ratioInferenceMedianMs":float(np.median(times)) if times else None}}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="references"},indent=2))


if __name__ == "__main__":
    main()

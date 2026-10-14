"""Experimental landmark geometry; no identity, gender or accuracy prediction."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "models/face_landmarker.task"
REFERENCES = ROOT / "assets/face_ratios.json"
BALANCE = ROOT / "assets/face_ratio_balance.json"
BALANCE_METHOD = "domain-balanced-zscore-v1"
MODEL_SHA256 = "64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff"
SCHEMA = 1
FEATURE_NAMES = ["face_aspect", "jaw_width", "eye_spacing", "eye_width", "eye_aspect",
                 "nose_width", "nose_length", "mouth_width", "lower_face"]
FEATURE_LABELS = ["얼굴 길이", "턱 너비", "눈 간격", "눈 너비", "눈 모양",
                  "코 너비", "코 길이", "입 너비", "하관 길이"]
# Equal feature weights are an uncalibrated experimental baseline.
WEIGHTS = np.full(len(FEATURE_NAMES), 1 / len(FEATURE_NAMES))


class RatioError(Exception):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ratio_features(points: np.ndarray, width: int, height: int) -> np.ndarray:
    """Pixel distances remove camera scale and roll; oblique faces are rejected."""
    points = np.asarray(points, dtype=float)
    if points.shape != (478, 2) or not np.isfinite(points).all() or min(width, height) < 16:
        raise RatioError("LANDMARK_QUALITY_FAILED")
    p = points * [width, height]
    distance = lambda a, b: float(np.linalg.norm(p[a] - p[b]))
    face_width = distance(234, 454)
    left_eye = (p[33] + p[133]) / 2
    right_eye = (p[362] + p[263]) / 2
    eye_axis = right_eye - left_eye
    eye_span = float(np.linalg.norm(eye_axis))
    if face_width < 40 or eye_span < 12:
        raise RatioError("LANDMARK_QUALITY_FAILED")
    nose_offset = abs(float((p[1] - (left_eye + right_eye) / 2) @ (eye_axis / eye_span))) / eye_span
    if nose_offset > .25:
        raise RatioError("FACE_NOT_FRONTAL")
    eye_width = (distance(33, 133) + distance(362, 263)) / 2
    if eye_width <= 1:
        raise RatioError("LANDMARK_QUALITY_FAILED")
    values = np.array([
        distance(10, 152) / face_width,
        distance(172, 397) / face_width,
        eye_span / face_width,
        eye_width / face_width,
        (distance(159, 145) + distance(386, 374)) / (2 * eye_width),
        distance(98, 327) / face_width,
        distance(168, 2) / face_width,
        distance(61, 291) / face_width,
        distance(2, 152) / face_width,
    ])
    if not np.isfinite(values).all() or (values <= 0).any():
        raise RatioError("LANDMARK_QUALITY_FAILED")
    return values


class FaceRatioEngine:
    def __init__(self):
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        if not MODEL.is_file() or sha256(MODEL) != MODEL_SHA256:
            raise RatioError("LANDMARK_MODEL_UNAVAILABLE")
        self.mp = mp
        options = vision.FaceLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(MODEL), delegate=python.BaseOptions.Delegate.CPU),
            running_mode=vision.RunningMode.IMAGE, num_faces=10,
            min_face_detection_confidence=.5, min_face_presence_confidence=.5,
        )
        self.model = vision.FaceLandmarker.create_from_options(options)

    def close(self):
        self.model.close()

    def extract(self, bgr: np.ndarray, *, target_box=None, landmarks_only=False):
        if bgr is None or bgr.ndim != 3:
            raise RatioError("INVALID_IMAGE")
        height, width = bgr.shape[:2]
        scale = min(1, 640 / max(height, width))
        small = cv2.resize(bgr, (round(width * scale), round(height * scale)))
        result = self.model.detect(self.mp.Image(image_format=self.mp.ImageFormat.SRGB,
                                                data=cv2.cvtColor(small, cv2.COLOR_BGR2RGB)))
        if not result.face_landmarks:
            raise RatioError("NO_PERSON")
        if target_box is None and len(result.face_landmarks) != 1:
            raise RatioError("MULTIPLE_PEOPLE")
        candidates = [np.array([[point.x, point.y] for point in face]) for face in result.face_landmarks]
        if target_box is not None:
            x, y, w, h = target_box
            def overlap(points):
                left, top = points.min(0); right, bottom = points.max(0)
                area = max(0, min(x+w, right)-max(x, left)) * max(0, min(y+h, bottom)-max(y, top))
                union = w*h + (right-left)*(bottom-top) - area
                return area / max(union, 1e-9)
            points = max(candidates, key=overlap)
            # Never switch to a different bystander if the selected face failed.
            if overlap(points) < .15:
                raise RatioError("LANDMARK_QUALITY_FAILED")
        else:
            points = candidates[0]
        return None if landmarks_only else ratio_features(points, width, height), points


def load_references() -> dict:
    try:
        data = json.loads(REFERENCES.read_text())
        ids = [f"char_{i:02d}" for i in range(1, 9)]
        genders = json.loads((ROOT / "assets/characters/genders.json").read_text())
        vectors = np.array([row["features"] for row in data["characters"]], dtype=float)
        if (data["schema"] != SCHEMA or data["featureNames"] != FEATURE_NAMES or
                [row["id"] for row in data["characters"]] != ids or
                vectors.shape != (8, len(FEATURE_NAMES)) or not np.isfinite(vectors).all() or (vectors <= 0).any() or
                data["genderSha256"] != sha256(ROOT / "assets/characters/genders.json") or
                any(row["gender"] != genders[row["id"]] for row in data["characters"]) or
                data["modelSha256"] != MODEL_SHA256 or not MODEL.is_file() or sha256(MODEL) != MODEL_SHA256 or
                any(row["sourceSha256"] != sha256(ROOT / "assets/characters" / f"{row['id']}.png")
                    for row in data["characters"])):
            raise ValueError("Stale references")
        return data
    except (OSError, KeyError, TypeError, ValueError):
        raise RatioError("RATIO_REFERENCES_UNAVAILABLE") from None


def load_balance() -> dict:
    """Only aggregate public-data statistics; never visitor counters or photos."""
    try:
        data = json.loads(BALANCE.read_text())
        if (data["method"] != BALANCE_METHOD or data["featureNames"] != FEATURE_NAMES or
                data["referencesSha256"] != sha256(REFERENCES) or
                data["modelSha256"] != MODEL_SHA256 or data["likenessValidated"] is not False):
            raise ValueError("Stale balance")
        for key in ("realMean", "realScale", "characterMean", "characterScale"):
            values = np.asarray(data[key], dtype=float)
            if values.shape != (9,) or not np.isfinite(values).all() or (values <= 0).any():
                raise ValueError("Invalid domain statistics")
        for gender, count in (("any", 8), ("male", 4), ("female", 4)):
            values = np.asarray(data["bias"][gender], dtype=float)
            if values.shape != (count,) or not np.isfinite(values).all():
                raise ValueError("Invalid candidate correction")
        return data
    except (OSError, KeyError, TypeError, ValueError):
        raise RatioError("RATIO_REFERENCES_UNAVAILABLE") from None


def balanced_errors(features: np.ndarray, vectors: np.ndarray, balance: dict) -> np.ndarray:
    # Match positions within each domain, rather than cartoon eye size itself.
    real = np.clip((features - balance["realMean"]) / balance["realScale"], -3, 3)
    characters = (vectors - balance["characterMean"]) / balance["characterScale"]
    return (characters - real) ** 2


def rank_ratios(features: np.ndarray, references: dict, gender: str = "any", *, balanced: bool = True) -> dict:
    if gender not in {"any", "male", "female"}:
        raise RatioError("INVALID_PREFERENCE")
    values = np.asarray(features, dtype=float)
    if values.shape != (len(FEATURE_NAMES),) or not np.isfinite(values).all() or (values <= 0).any():
        raise RatioError("LANDMARK_QUALITY_FAILED")
    rows = references["characters"]
    vectors = np.array([row["features"] for row in rows])
    # Scale each dimension with a floor; nearly identical reference values must
    # not turn tiny landmark noise into the dominant ranking factor.
    scales = np.maximum(vectors.std(axis=0), .03)
    errors = ((vectors - values) / scales) ** 2
    eligible = [i for i, row in enumerate(rows) if gender == "any" or row["gender"] == gender]
    if not eligible:
        raise RatioError("RATIO_REFERENCES_UNAVAILABLE")
    if balanced:
        correction = load_balance()
        errors = balanced_errors(values, vectors, correction)
        biases = np.asarray(correction["bias"][gender])
        costs = errors @ WEIGHTS
        # Fixed corrections learned offline. Repeated photos never rotate results.
        costs[eligible] += biases - biases.min()
        distances = np.sqrt(costs)
    else:
        distances = np.sqrt(errors @ WEIGHTS)
    order = sorted(eligible, key=lambda i: (distances[i], i))
    ranked = [{"characterId": rows[i]["id"], "distance": round(float(distances[i]), 4)} for i in order]
    closest_features = np.argsort(errors[order[0]], kind="stable")[:2]
    return {"characterId": rows[order[0]]["id"], "ranking": ranked,
            "margin": round(float(distances[order[1]] - distances[order[0]]), 4) if len(order) > 1 else 0,
            "closestFeatures": [FEATURE_LABELS[i] for i in closest_features],
            "experimental": True, "calibrated": False, "distributionCorrected": balanced}

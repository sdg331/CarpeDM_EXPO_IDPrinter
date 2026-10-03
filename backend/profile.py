"""Mode B local profile composition.

The captured frame is never written to disk.  YuNet supplies one face box and
five landmarks. OpenCV separates the visitor from the background and creates
a close-up 3:4 portrait, preserving the original face, neck, and clothing.
"""

from __future__ import annotations

import secrets
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable

import cv2
import numpy as np

from backend.face import Detection, FaceEngine, MultipleFacesError, NoFaceError

PROFILE_WIDTH = 720
PROFILE_HEIGHT = 960


class ProfileQualityError(ValueError):
    """The photo is valid, but not suitable for a reliable composite."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class ProfileComposer:
    """Build a local-only portrait while preserving the captured face pixels."""

    def generate(self, bgr: np.ndarray, engine: FaceEngine) -> bytes:
        detections = engine.detect(bgr)
        if not detections:
            raise NoFaceError("얼굴을 찾지 못했다")
        if len(detections) > 1:
            raise MultipleFacesError(len(detections))
        return self.compose(bgr, detections[0])

    def compose(self, bgr: np.ndarray, detection: Detection) -> bytes:
        if bgr.ndim != 3 or bgr.shape[2] != 3:
            raise ProfileQualityError("invalid_image")

        self._check_quality(bgr, detection)
        portrait, face_box = _normalized_portrait(bgr, detection)
        alpha = _segment_subject(portrait, face_box)
        result = _make_background()
        result = _alpha_blend(result, portrait, alpha)

        ok, encoded = cv2.imencode(
            ".png", result, [cv2.IMWRITE_PNG_COMPRESSION, 3]
        )
        if not ok:
            raise ProfileQualityError("composition_failed")
        return encoded.tobytes()

    @staticmethod
    def _check_quality(bgr: np.ndarray, detection: Detection) -> None:
        image_h, image_w = bgr.shape[:2]
        x, y, width, height = detection.box
        short_side = min(image_w, image_h)

        if detection.confidence < 0.65 or width <= 0 or height <= 0:
            raise ProfileQualityError("bad_position")
        face_ratio = width / short_side
        if width < 52 or height < 52 or not 0.08 <= face_ratio <= 0.55:
            raise ProfileQualityError("bad_position")
        if (
            x < 0
            or y < 0
            or x + width > image_w
            or y + height > image_h
            or x - width * 0.28 < 0
            or x + width * 1.28 > image_w
            or y - height * 0.28 < 0
            or y + height * 1.15 > image_h
        ):
            raise ProfileQualityError("bad_position")

        landmarks = detection.row[4:14].reshape(5, 2)
        eye_a, eye_b = landmarks[:2]
        eye_delta = eye_b - eye_a
        eye_distance = float(np.linalg.norm(eye_delta))
        if eye_distance < width * 0.18:
            raise ProfileQualityError("bad_position")
        roll = abs(float(np.degrees(np.arctan2(eye_delta[1], eye_delta[0]))))
        if roll > 20:
            raise ProfileQualityError("bad_position")

        roi = bgr[y : y + height, x : x + width]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        brightness = float(gray.mean())
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if brightness < 28 or brightness > 238 or sharpness < 10:
            raise ProfileQualityError("low_quality")


def _normalized_portrait(
    bgr: np.ndarray, detection: Detection
) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    """Uniformly scale/crop the source; never stretch or shear the face."""

    x, y, face_w, face_h = detection.box
    face_cx = x + face_w / 2
    face_cy = y + face_h / 2
    image_h, image_w = bgr.shape[:2]
    crop_w = min(
        max(face_w * 2.25, face_h * 1.85),
        image_w,
        image_h * PROFILE_WIDTH / PROFILE_HEIGHT,
    )
    crop_h = crop_w * PROFILE_HEIGHT / PROFILE_WIDTH
    # Tight source portraits must not acquire empty space below the shoulders.
    left = float(np.clip(face_cx - crop_w / 2, 0, image_w - crop_w))
    top = float(np.clip(face_cy - crop_h * 0.34, 0, image_h - crop_h))
    scale = PROFILE_WIDTH / crop_w

    transform = np.array(
        [[scale, 0.0, -left * scale], [0.0, scale, -top * scale]],
        dtype=np.float32,
    )
    portrait = cv2.warpAffine(
        bgr,
        transform,
        (PROFILE_WIDTH, PROFILE_HEIGHT),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )
    face_box = (
        (x - left) * scale,
        (y - top) * scale,
        face_w * scale,
        face_h * scale,
    )
    return portrait, face_box


def _subject_seed(
    shape: tuple[int, int], face_box: tuple[float, float, float, float]
) -> tuple[np.ndarray, np.ndarray]:
    """Return a GrabCut seed and a conservative geometry fallback mask."""

    image_h, image_w = shape
    fx, fy, fw, fh = face_box
    cx = int(round(fx + fw / 2))
    head_cy = int(round(fy + fh * 0.40))

    seed = np.full((image_h, image_w), cv2.GC_BGD, np.uint8)
    geometry = np.zeros((image_h, image_w), np.uint8)

    head_axes = (max(8, int(fw * 0.84)), max(8, int(fh * 0.94)))
    cv2.ellipse(seed, (cx, head_cy), head_axes, 0, 0, 360, cv2.GC_PR_FGD, -1)
    cv2.ellipse(geometry, (cx, head_cy), head_axes, 0, 0, 360, 255, -1)

    shoulder_y = int(round(fy + fh * 0.92))
    torso = np.array(
        [
            [cx - int(fw * 0.82), shoulder_y],
            [cx + int(fw * 0.82), shoulder_y],
            [min(image_w - 1, cx + int(fw * 1.55)), image_h - 1],
            [max(0, cx - int(fw * 1.55)), image_h - 1],
        ],
        dtype=np.int32,
    )
    cv2.fillConvexPoly(seed, torso, cv2.GC_PR_FGD)
    cv2.fillConvexPoly(geometry, torso, 255)

    sure_axes = (max(5, int(fw * 0.40)), max(5, int(fh * 0.43)))
    sure_center = (cx, int(round(fy + fh * 0.50)))
    cv2.ellipse(seed, sure_center, sure_axes, 0, 0, 360, cv2.GC_FGD, -1)
    cv2.ellipse(geometry, sure_center, sure_axes, 0, 0, 360, 255, -1)

    border = max(3, min(image_w, image_h) // 80)
    seed[:border, :] = cv2.GC_BGD
    seed[:, :border] = cv2.GC_BGD
    seed[:, -border:] = cv2.GC_BGD
    # A close-up's clothing continues through the bottom edge. Mark its
    # central region as foreground so GrabCut cannot discard the whole torso.
    torso_core = np.array([
        [cx - int(fw * 0.26), int(fy + fh * 1.02)],
        [cx + int(fw * 0.26), int(fy + fh * 1.02)],
        [min(image_w - border - 1, cx + int(fw * 0.60)), image_h - 1],
        [max(border, cx - int(fw * 0.60)), image_h - 1],
    ], dtype=np.int32)
    cv2.fillConvexPoly(seed, torso_core, cv2.GC_FGD)
    return seed, geometry


def _segment_subject(
    portrait: np.ndarray, face_box: tuple[float, float, float, float]
) -> np.ndarray:
    """Separate the visitor locally; fall back to a face-shaped soft mask."""

    small_w, small_h = PROFILE_WIDTH // 2, PROFILE_HEIGHT // 2
    small = cv2.resize(portrait, (small_w, small_h), interpolation=cv2.INTER_AREA)
    small_face = tuple(value * 0.5 for value in face_box)
    seed, geometry = _subject_seed((small_h, small_w), small_face)
    binary: np.ndarray

    try:
        background_model = np.zeros((1, 65), np.float64)
        foreground_model = np.zeros((1, 65), np.float64)
        cv2.grabCut(
            small,
            seed,
            None,
            background_model,
            foreground_model,
            3,
            cv2.GC_INIT_WITH_MASK,
        )
        binary = np.where(
            (seed == cv2.GC_FGD) | (seed == cv2.GC_PR_FGD), 255, 0
        ).astype(np.uint8)
        binary = _connected_to_face(binary, small_face)
        if cv2.countNonZero(binary) < small_w * small_h * 0.035:
            binary = geometry
    except cv2.error:
        binary = geometry

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    alpha = cv2.resize(binary, (PROFILE_WIDTH, PROFILE_HEIGHT), interpolation=cv2.INTER_LINEAR)
    alpha = cv2.GaussianBlur(alpha, (0, 0), sigmaX=5.5, sigmaY=5.5)

    # GrabCut must never punch holes through the visitor's face.
    fx, fy, fw, fh = face_box
    face_guard = np.zeros((PROFILE_HEIGHT, PROFILE_WIDTH), np.uint8)
    cv2.ellipse(
        face_guard,
        (int(fx + fw / 2), int(fy + fh / 2)),
        (max(5, int(fw * 0.43)), max(5, int(fh * 0.46))),
        0,
        0,
        360,
        255,
        -1,
    )
    return np.maximum(alpha, face_guard)


def _connected_to_face(
    mask: np.ndarray, face_box: tuple[float, float, float, float]
) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if count <= 1:
        return mask

    fx, fy, fw, fh = face_box
    cx = int(np.clip(fx + fw / 2, 0, mask.shape[1] - 1))
    cy = int(np.clip(fy + fh / 2, 0, mask.shape[0] - 1))
    label = int(labels[cy, cx])
    if label == 0:
        label = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return np.where(labels == label, 255, 0).astype(np.uint8)


def _make_background() -> np.ndarray:
    top = np.array([255, 248, 241], dtype=np.float32)
    bottom = np.array([246, 233, 220], dtype=np.float32)
    weight = np.linspace(0.0, 1.0, PROFILE_HEIGHT, dtype=np.float32)[:, None, None]
    row = top * (1.0 - weight) + bottom * weight
    return np.broadcast_to(row, (PROFILE_HEIGHT, PROFILE_WIDTH, 3)).copy().astype(np.uint8)


def _alpha_blend(
    background: np.ndarray, foreground: np.ndarray, alpha: np.ndarray
) -> np.ndarray:
    amount = alpha.astype(np.float32)[:, :, None] / 255.0
    mixed = foreground.astype(np.float32) * amount + background.astype(np.float32) * (
        1.0 - amount
    )
    return np.clip(mixed, 0, 255).astype(np.uint8)


@dataclass
class _StoredProfile:
    png: bytes
    expires_at: float
    operation_id: str | None
    owner: str | None = None
    fingerprint: str | None = None


class ProfileStore:
    """Small in-memory TTL store for generated composites only."""

    def __init__(
        self,
        ttl_seconds: int = 600,
        max_items: int = 8,
        clock: Callable[[], float] = time.monotonic,
        max_bytes: int = 32 * 1024 * 1024,
    ):
        if ttl_seconds <= 0 or max_items <= 0:
            raise ValueError("ttl_seconds와 max_items는 양수여야 한다")
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self.max_bytes = max_bytes
        self._clock = clock
        self._items: OrderedDict[str, _StoredProfile] = OrderedDict()
        self._operations: dict[str, str] = {}
        self._lock = threading.RLock()

    def find_operation(self, operation_id: str | None, fingerprint: str | None = None) -> str | None:
        if not operation_id:
            return None
        with self._lock:
            self._prune_locked()
            profile_id = self._operations.get(operation_id)
            entry = self._items.get(profile_id)
            if entry and fingerprint and entry.fingerprint != fingerprint:
                raise ValueError("operation frame changed")
            return profile_id if entry else None

    def put(self, png: bytes, operation_id: str | None = None, *, fingerprint: str | None = None) -> str:
        with self._lock:
            self._prune_locked()
            previous = self._operations.get(operation_id) if operation_id else None
            if previous in self._items:
                return previous
            if len(png) > self.max_bytes:
                raise ValueError("profile exceeds memory limit")
            while len(self._items) >= self.max_items or sum(len(item.png) for item in self._items.values()) + len(png) > self.max_bytes:
                profile_id, entry = self._items.popitem(last=False)
                self._remove_operation_locked(profile_id, entry)
            profile_id = f"p_{secrets.token_urlsafe(18)}"
            self._items[profile_id] = _StoredProfile(
                png=bytes(png),
                expires_at=self._clock() + self.ttl_seconds,
                operation_id=operation_id,
                fingerprint=fingerprint,
            )
            if operation_id:
                self._operations[operation_id] = profile_id
            return profile_id

    def get(self, profile_id: str) -> bytes | None:
        with self._lock:
            self._prune_locked()
            entry = self._items.get(profile_id)
            return entry.png if entry else None

    def claim(self, profile_id: str, session_id: str) -> bool:
        """Attach the opaque profile once, without extending its retention."""
        with self._lock:
            self._prune_locked()
            entry = self._items.get(profile_id)
            if entry is None:
                return False
            if entry.owner and entry.owner != session_id:
                raise ValueError("profile belongs to another session")
            entry.owner = session_id
            return True

    def prune(self) -> None:
        with self._lock:
            self._prune_locked()

    def delete(self, profile_id: str) -> bool:
        with self._lock:
            entry = self._items.pop(profile_id, None)
            if not entry:
                return False
            self._remove_operation_locked(profile_id, entry)
            return True

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
            self._operations.clear()

    def __len__(self) -> int:
        with self._lock:
            self._prune_locked()
            return len(self._items)

    def _prune_locked(self) -> None:
        now = self._clock()
        expired = [
            profile_id
            for profile_id, entry in self._items.items()
            if entry.expires_at <= now
        ]
        for profile_id in expired:
            entry = self._items.pop(profile_id)
            self._remove_operation_locked(profile_id, entry)

    def _remove_operation_locked(
        self, profile_id: str, entry: _StoredProfile
    ) -> None:
        if entry.operation_id and self._operations.get(entry.operation_id) == profile_id:
            self._operations.pop(entry.operation_id, None)

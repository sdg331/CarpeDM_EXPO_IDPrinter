"""Mode B local composite, temporary store, and endpoint contract tests."""

import asyncio
from io import BytesIO

import cv2
import numpy as np
import pytest
from fastapi import HTTPException, UploadFile

from backend.face import Detection, MultipleFacesError, NoFaceError
from backend.profile import (
    PROFILE_HEIGHT,
    PROFILE_WIDTH,
    ProfileComposer,
    ProfileQualityError,
    ProfileStore,
    _normalized_portrait,
)

def detection(
    box=(400, 160, 160, 190), *, roll_degrees=0.0, confidence=0.99
) -> Detection:
    x, y, width, height = box
    eye_a = np.array([x + width * 0.32, y + height * 0.40])
    eye_dx = width * 0.36
    eye_b = eye_a + np.array(
        [eye_dx, np.tan(np.radians(roll_degrees)) * eye_dx]
    )
    landmarks = np.array(
        [
            eye_a,
            eye_b,
            [x + width * 0.50, y + height * 0.58],
            [x + width * 0.37, y + height * 0.76],
            [x + width * 0.63, y + height * 0.76],
        ],
        dtype=np.float32,
    )
    row = np.zeros(15, dtype=np.float32)
    row[:4] = box
    row[4:14] = landmarks.reshape(-1)
    row[-1] = confidence
    return Detection(row=row, confidence=confidence)


def portrait_fixture() -> np.ndarray:
    image = np.full((720, 960, 3), (205, 216, 225), np.uint8)
    cv2.rectangle(image, (300, 340), (660, 719), (95, 125, 155), -1)
    cv2.ellipse(image, (480, 255), (108, 145), 0, 0, 360, (82, 112, 142), -1)
    cv2.rectangle(image, (400, 160), (560, 350), (150, 178, 205), -1)
    cv2.circle(image, (450, 235), 10, (35, 42, 50), -1)
    cv2.circle(image, (510, 235), 10, (35, 42, 50), -1)
    cv2.line(image, (450, 305), (510, 305), (55, 70, 85), 6)
    # Fine detail makes the fixture meaningfully exercise the sharpness gate.
    for offset in range(0, 160, 12):
        cv2.line(image, (400 + offset, 165), (400 + offset, 185), (120, 145, 170), 2)
    return image


def test_local_composite_is_opaque_3_by_4_and_preserves_face_center():
    composer = ProfileComposer()
    png = composer.compose(portrait_fixture(), detection())
    result = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_UNCHANGED)
    assert result.shape == (PROFILE_HEIGHT, PROFILE_WIDTH, 3)

    # The normalized face center is (360, 326); preserve its original colour.
    expected_skin = np.array([150, 178, 205])
    assert np.max(np.abs(result[326, 360].astype(int) - expected_skin)) <= 3
    # Preserve the visitor's actual clothing instead of painting a suit over it.
    assert np.max(np.abs(result[800, 360].astype(int) - [95, 125, 155])) <= 3


def test_quality_gate_rejects_tilt_small_and_flat_photos():
    composer = ProfileComposer()
    image = portrait_fixture()
    with pytest.raises(ProfileQualityError, match="bad_position"):
        composer.compose(image, detection(roll_degrees=28))
    with pytest.raises(ProfileQualityError, match="bad_position"):
        composer.compose(image, detection(box=(450, 220, 30, 36)))
    with pytest.raises(ProfileQualityError, match="bad_position"):
        composer.compose(image, detection(box=(400, 520, 160, 190)))
    flat = np.full_like(image, 128)
    with pytest.raises(ProfileQualityError, match="low_quality"):
        composer.compose(flat, detection())


def test_close_up_enlarges_face_without_changing_proportions():
    _, (_, y, width, height) = _normalized_portrait(portrait_fixture(), detection())
    assert width >= 300
    assert height >= 370
    assert width / height == pytest.approx(160 / 190)
    assert y + height / 2 == pytest.approx(PROFILE_HEIGHT * 0.34)


def test_tight_source_fills_frame_without_inventing_space_below_shoulders():
    image = np.full((480, 360, 3), (80, 110, 140), np.uint8)
    portrait, _ = _normalized_portrait(image, detection(box=(85, 80, 190, 260)))
    assert np.all(portrait == (80, 110, 140))


def test_original_clothing_colour_is_retained_for_different_inputs():
    for colour in [(45, 75, 135), (140, 80, 40)]:
        source = portrait_fixture()
        source[410:, 310:650] = colour
        png = ProfileComposer().compose(source, detection())
        result = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)
        assert np.max(np.abs(result[800, 360].astype(int) - colour)) <= 3


def test_generate_requires_exactly_one_face():
    composer = ProfileComposer()
    image = portrait_fixture()

    class FakeEngine:
        def __init__(self, detections):
            self.detections = detections

        def detect(self, _):
            return self.detections

    with pytest.raises(NoFaceError):
        composer.generate(image, FakeEngine([]))
    with pytest.raises(MultipleFacesError):
        composer.generate(image, FakeEngine([detection(), detection()]))


def test_profile_store_reuses_operations_expires_and_evicts():
    now = [100.0]
    store = ProfileStore(ttl_seconds=10, max_items=2, clock=lambda: now[0])
    first = store.put(b"one", "job-1")
    assert store.put(b"different", "job-1") == first
    second = store.put(b"two", "job-2")
    third = store.put(b"three", "job-3")
    assert store.get(first) is None
    assert store.get(second) == b"two"
    assert store.get(third) == b"three"

    now[0] += 11
    assert store.get(second) is None
    assert len(store) == 0


def test_profile_endpoint_reuses_id_serves_no_store_and_deletes():
    from backend import app as app_module

    class FakeComposer:
        calls = 0

        def generate(self, image, engine):
            self.calls += 1
            assert image.shape == (24, 32, 3)
            return b"\x89PNG\r\nfixture"

    image = np.full((24, 32, 3), 128, np.uint8)
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok
    composer = FakeComposer()
    app_module.STATE.clear()
    app_module.STATE.update(
        {
            "profiles": ProfileStore(ttl_seconds=30, max_items=2),
            "profile_composer": composer,
            "engine": object(),
        }
    )
    try:
        request = lambda: UploadFile(
            filename="capture.jpg", file=BytesIO(encoded.tobytes())
        )
        first = asyncio.run(app_module.generate_profile(request(), "ai-job-1"))
        second = asyncio.run(app_module.generate_profile(request(), "ai-job-1"))
        assert first["ok"] is True
        assert second["profileId"] == first["profileId"]
        assert second["reused"] is True
        assert composer.calls == 1

        response = app_module.profile_image(first["profileId"])
        assert response.media_type == "image/png"
        assert response.headers["cache-control"] == "no-store, max-age=0"
        assert response.body.startswith(b"\x89PNG")

        assert app_module.delete_profile(first["profileId"]) == {"ok": True}
        missing = app_module.profile_image(first["profileId"])
        assert missing.status_code == 410
    finally:
        app_module.STATE.clear()


def test_store_enforces_memory_budget_and_rejects_changed_frame_operation():
    store = ProfileStore(max_items=10, max_bytes=8)
    first = store.put(b'12345', 'first', fingerprint='one')
    second = store.put(b'1234', 'second', fingerprint='two')
    assert store.get(first) is None
    assert store.get(second) == b'1234'
    with pytest.raises(ValueError, match='operation frame changed'):
        store.find_operation('second', 'different')
    with pytest.raises(ValueError, match='memory limit'):
        store.put(b'123456789')


def test_image_dimension_limit_is_checked_before_opencv_decode(monkeypatch):
    from PIL import Image
    from backend import app as app_module

    buffer = BytesIO()
    Image.new('1', (4000, 4000)).save(buffer, format='PNG')
    monkeypatch.setattr(cv2, 'imdecode', lambda *_: pytest.fail('oversized image reached decoder'))
    with pytest.raises(HTTPException) as exc:
        app_module._decode_frame(buffer.getvalue())
    assert exc.value.status_code == 413

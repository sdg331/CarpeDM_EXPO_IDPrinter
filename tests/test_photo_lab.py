"""The opt-in experiment cannot mutate kiosk sessions or print photos."""

import asyncio
from types import SimpleNamespace

import cv2
import httpx
import numpy as np
import pytest
from fastapi.testclient import TestClient

import backend.app as api
from backend.face import MultipleFacesError, NoFaceError
from backend.profile import ProfileQualityError
from backend.photo_lab import MAX_BYTES
from test_profile import portrait_fixture, detection


def client():
    return TestClient(api.app, client=("127.0.0.1", 50000))


def prepare(monkeypatch):
    monkeypatch.setenv("KIOSK_PHOTO_LAB", "1")
    monkeypatch.setitem(api.STATE, "engine", SimpleNamespace(detect=lambda _: [detection()]))
    monkeypatch.setitem(api.STATE, "profiles", SimpleNamespace(put=lambda *a: pytest.fail("stored a photo")))
    monkeypatch.setattr(api, "print_badge", lambda *a: pytest.fail("printed a photo"))
    monkeypatch.setattr(api, "STORE", SimpleNamespace())


def frame():
    ok, png = cv2.imencode(".png", portrait_fixture(), [cv2.IMWRITE_PNG_COMPRESSION, 0])
    assert ok and png.nbytes > 1024 * 1024
    return png.tobytes()


def test_disabled_by_default_does_not_read_or_process(monkeypatch):
    monkeypatch.delenv("KIOSK_PHOTO_LAB", raising=False)
    assert client().get("/api/experiments/photo/status").json()["enabled"] is False
    result = client().post("/api/experiments/photo/compose", content=b"private-synthetic", headers={"content-type": "image/png"})
    assert result.status_code == 403
    assert result.json()["error"]["code"] == "PHOTO_LAB_DISABLED"


def test_real_composer_retains_face_and_clothes_without_disk_or_sessions(monkeypatch):
    import starlette.formparsers as parsers
    prepare(monkeypatch)
    monkeypatch.setattr(parsers, "SpooledTemporaryFile", lambda *a, **kw: pytest.fail("spooled a photo"))
    result = client().post("/api/experiments/photo/compose", content=frame(), headers={"content-type": "image/png"})
    assert result.status_code == 200
    assert result.headers["content-type"] == "image/png"
    assert result.headers["cache-control"] == "no-store, max-age=0"
    image = cv2.imdecode(np.frombuffer(result.content,np.uint8),cv2.IMREAD_COLOR)
    assert image.shape == (960,720,3)
    assert np.max(np.abs(image[326,360].astype(int)-[150,178,205])) <= 3
    assert np.max(np.abs(image[800,360].astype(int)-[95,125,155])) <= 3


@pytest.mark.parametrize("error,code", [(NoFaceError(),"NO_PERSON"),(MultipleFacesError(2),"MULTIPLE_PEOPLE"),(ProfileQualityError("low_quality"),"PHOTO_QUALITY_FAILED"),(RuntimeError("private traceback"),"PHOTO_PROCESSING_FAILED")])
def test_processing_failures_are_errors_and_keep_private_details_hidden(monkeypatch,error,code):
    prepare(monkeypatch)
    monkeypatch.setitem(api.STATE, "engine", SimpleNamespace(detect=lambda _: (_ for _ in ()).throw(error)))
    response = client().post("/api/experiments/photo/compose", content=frame(), headers={"content-type":"image/png"})
    assert response.status_code in {422,503}
    assert response.json()["error"]["code"] == code
    assert "private traceback" not in response.text


def test_missing_model_reports_unavailable(monkeypatch):
    prepare(monkeypatch)
    monkeypatch.setitem(api.STATE,"engine",None)
    assert client().get("/api/experiments/photo/status").json()["ready"] is False
    response = client().post("/api/experiments/photo/compose",content=frame(),headers={"content-type":"image/png"})
    assert response.status_code == 503


def test_invalid_empty_multipart_and_declared_oversize_input(monkeypatch):
    prepare(monkeypatch)
    for data,type_,expected in [(b"bad","image/png",400),(b"","image/png",400),(b"body","multipart/form-data",400),(b"body","image/svg+xml",400)]:
        result=client().post("/api/experiments/photo/compose",content=data,headers={"content-type":type_})
        assert result.status_code == expected
    result=client().post("/api/experiments/photo/compose",content=b"",headers={"content-type":"image/png","content-length":str(MAX_BYTES+1)})
    assert result.status_code == 413


def test_chunked_body_capped_before_decode(monkeypatch):
    prepare(monkeypatch)
    monkeypatch.setattr(api,"_decode_frame",lambda _: pytest.fail("oversized decode"))
    async def run():
        async def chunks():
            for _ in range(9):
                yield b"x" * 1024 * 1024
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api.app,client=("127.0.0.1",50000)),base_url="http://127.0.0.1") as c:
            return await c.post("/api/experiments/photo/compose",content=chunks(),headers={"content-type":"image/png"})
    assert asyncio.run(run()).status_code == 413


def test_large_decoded_dimensions_rejected_before_opencv(monkeypatch):
    from io import BytesIO
    from PIL import Image
    prepare(monkeypatch)
    buffer=BytesIO();Image.new("1",(4000,4000)).save(buffer,format="PNG")
    monkeypatch.setattr(api.cv2,"imdecode",lambda *a:pytest.fail("oversized decode"))
    result=client().post("/api/experiments/photo/compose",content=buffer.getvalue(),headers={"content-type":"image/png"})
    assert result.status_code == 413


def test_loopback_and_origin_boundaries_still_apply(monkeypatch):
    prepare(monkeypatch)
    remote=TestClient(api.app,client=("192.168.1.10",50000))
    assert remote.get("/api/experiments/photo/status").status_code == 403
    assert client().post("/api/experiments/photo/compose",content=b"",headers={"content-type":"image/png","origin":"https://unrelated.example"}).status_code == 403

from io import BytesIO
from types import SimpleNamespace

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import backend.app as app
import backend.ratio_lab as lab
from backend.face import Detection, FaceEngine, NoFaceError, primary_face
from backend.face_ratios import FaceRatioEngine, RatioError


def detection(box, confidence=.9):
    x,y,w,h=box
    points=np.array([[x+.3*w,y+.35*h],[x+.7*w,y+.35*h],[x+.5*w,y+.5*h],
                     [x+.35*w,y+.75*h],[x+.65*w,y+.75*h]])
    return Detection(np.array([*box,*points.flatten(),confidence],dtype=np.float32),confidence)


def test_largest_visible_face_wins_over_confidence_and_offscreen_area():
    small=detection((50,50,70,90),.99);large=detection((250,80,160,210),.7)
    outside=detection((-600,0,650,400))
    assert primary_face([small,outside,large],640,480) is large
    with pytest.raises(NoFaceError):primary_face([],640,480)


def test_equal_size_prefers_center_independently_of_detection_order():
    side=detection((10,50,80,100),.99);center=detection((280,190,80,100),.7)
    for candidates in ([side,center],[center,side]):assert primary_face(candidates,640,480) is center


@pytest.fixture
def client(monkeypatch):
    engine=FaceEngine.__new__(FaceEngine)
    engine.detect=lambda _: [detection((20,40,60,90),.99),detection((230,70,180,260),.7)]
    engine.embed=lambda _,selected: np.full(128,selected.box[2],dtype=float)
    monkeypatch.setitem(app.STATE,"engine",engine)
    monkeypatch.setitem(app.STATE,"proto",SimpleNamespace(ids=[f"char_{i:02d}" for i in range(1,9)],
                         groups=["?"]*8,match_scores=lambda embedding,*_:np.arange(8,dtype=float)))
    monkeypatch.setitem(app.STATE,"mu_real",None)
    return TestClient(app.app,client=("127.0.0.1",12345))


def post(client,path):
    raw=BytesIO();Image.new("RGB",(640,480)).save(raw,format="PNG")
    return client.post(path,files={"frame":("test.png",raw.getvalue(),"image/png")})


def test_preview_and_match_select_the_same_face_and_keep_empty_error(client,monkeypatch):
    preview=post(client,"/api/detect").json();match=post(client,"/api/match").json()
    assert preview["ok"] and preview["count"]==2 and match["ok"]
    assert preview["face"]==match["face"]
    assert preview["face"]["box"]==pytest.approx([230/640,70/480,180/640,260/480])
    assert len(match["face"]["landmarks"])==5
    monkeypatch.setattr(app.STATE["engine"],"detect",lambda _:[])
    assert post(client,"/api/detect").json()["face"] is None
    assert post(client,"/api/match").json()["error"]=="no_face"


def test_dense_map_uses_the_selected_box_and_falls_back_only_to_real_points(client,monkeypatch):
    calls=[]
    def dense(raw,gender,selected,*,landmarks_only):
        calls.append(selected)
        assert landmarks_only and selected["count"]==2
        return {"landmarks":[[.5,.5]]*478}
    monkeypatch.setattr(lab,"run_ratio_frame",dense)
    result=post(client,"/api/face-map").json()
    assert result["detailAvailable"] and len(result["face"]["landmarks"])==478
    assert result["face"]["box"]==calls[0]["box"]
    def fail(*args,**kwargs):raise RatioError("LANDMARK_ENGINE_UNAVAILABLE")
    monkeypatch.setattr(lab,"run_ratio_frame",fail)
    result=post(client,"/api/face-map").json()
    assert not result["detailAvailable"] and result["face"]["source"]=="yunet"
    assert len(result["face"]["landmarks"])==5 and not lab.COMPARISON_LOCK.locked()


def test_dense_engine_follows_yunet_target_instead_of_a_different_face():
    engine=FaceRatioEngine.__new__(FaceRatioEngine)
    engine.mp=SimpleNamespace(Image=lambda **_:None,ImageFormat=SimpleNamespace(SRGB=1))
    def landmarks(x,width):
        points=np.tile([x,.5],(478,1));points[0]=[x-width/2,.3];points[1]=[x+width/2,.7]
        return [SimpleNamespace(x=a,y=b) for a,b in points]
    engine.model=SimpleNamespace(detect=lambda _:SimpleNamespace(face_landmarks=[landmarks(.25,.35),landmarks(.75,.18)]))
    _,selected=engine.extract(np.zeros((480,640,3),np.uint8),target_box=[.65,.3,.2,.4],landmarks_only=True)
    assert selected[:,0].mean()>.7
    with pytest.raises(RatioError,match="LANDMARK_QUALITY_FAILED"):
        engine.extract(np.zeros((480,640,3),np.uint8),target_box=[.4,.0,.1,.1],landmarks_only=True)


def measured_result(gender):
    from backend.face_ratios import load_balance, load_references, rank_ratios
    result = rank_ratios(np.array(load_balance()["realMean"]), load_references(), gender)
    return {**result, "landmarks": [[.5, .5]] * 478, "elapsedMs": 30}


@pytest.mark.parametrize("gender,count", [("any", 8), ("male", 4), ("female", 4)])
def test_visitor_recommendation_uses_geometry_and_explains_the_same_selected_face(client, monkeypatch, gender, count):
    expected = measured_result(gender)
    def geometry(raw, preference, selected):
        assert preference == gender and selected["count"] == 2
        assert selected["box"] == pytest.approx([230/640, 70/480, 180/640, 260/480])
        return expected
    monkeypatch.setattr(lab, "run_ratio_frame", geometry)
    monkeypatch.setattr(app.STATE["engine"], "embed", lambda *_: pytest.fail("SFace must not select the visitor result"))
    raw = BytesIO(); Image.new("RGB", (640, 480)).save(raw, format="PNG")
    response = client.post("/api/match/landmarks", data={"character_gender": gender},
                           files={"frame": ("test.png", raw.getvalue(), "image/png")})
    data = response.json()
    assert response.status_code == 200 and data["engine"] == "mediapipe_ratios"
    assert data["characters"][data["top"]]["id"] == expected["characterId"]
    assert data["analysis"]["comparisons"] == expected["comparisons"]
    assert data["analysis"]["candidateCount"] == count
    assert len(data["face"]["landmarks"]) == 478 and data["face"]["source"] == "mediapipe"
    assert data["externalUpload"] is False and data["analysis"]["likenessValidated"] is False
    assert not lab.COMPARISON_LOCK.locked()


@pytest.mark.parametrize("code,status", [("FACE_NOT_FRONTAL", 422), ("LANDMARK_ENGINE_UNAVAILABLE", 503)])
def test_geometry_failure_never_returns_a_sface_or_random_recommendation(client, monkeypatch, code, status):
    def fail(*_): raise RatioError(code)
    monkeypatch.setattr(lab, "run_ratio_frame", fail)
    response = post(client, "/api/match/landmarks")
    assert response.status_code == status and response.json()["error"]["code"] == code
    assert "top" not in response.json() and not lab.COMPARISON_LOCK.locked()


def test_geometry_rejects_busy_or_malformed_results(client, monkeypatch):
    with lab.COMPARISON_LOCK:
        assert post(client, "/api/match/landmarks").status_code == 409
    result = measured_result("any"); result["landmarks"] = [[.5, .5]] * 5
    monkeypatch.setattr(lab, "run_ratio_frame", lambda *_: result)
    assert post(client, "/api/match/landmarks").status_code == 503
    assert not lab.COMPARISON_LOCK.locked()


def test_landmark_preference_defaults_to_any_and_rejects_unknown_values(client, monkeypatch):
    calls = []
    def geometry(raw, gender, selected):
        calls.append(gender)
        return measured_result(gender)
    monkeypatch.setattr(lab, "run_ratio_frame", geometry)
    data = post(client, "/api/match/landmarks").json()
    assert data["characterGender"] == "any" and data["analysis"]["candidateCount"] == 8
    raw = BytesIO(); Image.new("RGB", (640, 480)).save(raw, format="PNG")
    response = client.post("/api/match/landmarks", data={"character_gender": "unknown"},
                           files={"frame": ("test.png", raw.getvalue(), "image/png")})
    assert response.status_code == 422 and calls == ["any"]


@pytest.mark.parametrize("gender,other", [("male", "female"), ("female", "male")])
def test_landmark_engine_cannot_return_candidates_outside_the_selected_preference(client, monkeypatch, gender, other):
    monkeypatch.setattr(lab, "run_ratio_frame", lambda *_: measured_result(other))
    raw = BytesIO(); Image.new("RGB", (640, 480)).save(raw, format="PNG")
    response = client.post("/api/match/landmarks", data={"character_gender": gender},
                           files={"frame": ("test.png", raw.getvalue(), "image/png")})
    assert response.status_code == 503 and "top" not in response.json()
    assert not lab.COMPARISON_LOCK.locked()

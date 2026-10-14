import json
from io import BytesIO
from unittest.mock import AsyncMock

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import backend.app as app
import backend.face_ratios as ratios
import backend.ratio_lab as lab


def points():
    p = np.full((478,2),.5)
    positions = {234:(.2,.5),454:(.8,.5),10:(.5,.15),152:(.5,.85),172:(.3,.75),397:(.7,.75),
                 33:(.3,.4),133:(.43,.4),362:(.57,.4),263:(.7,.4),1:(.5,.53),
                 159:(.37,.38),145:(.37,.42),386:(.63,.38),374:(.63,.42),
                 98:(.45,.55),327:(.55,.55),168:(.5,.4),2:(.5,.57),61:(.4,.67),291:(.6,.67)}
    for i,xy in positions.items(): p[i]=xy
    return p


def test_features_ignore_scale_translation_and_roll():
    p=points(); expected=ratios.ratio_features(p,640,800)
    assert np.allclose(expected,ratios.ratio_features(p+.05,1280,1600))
    theta=.2; rotation=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
    rotated=((p*[640,800])@rotation.T)/[640,800]
    assert np.allclose(expected,ratios.ratio_features(rotated,640,800))


@pytest.mark.parametrize("bad",[np.zeros((478,2)),np.full((478,2),np.nan),np.zeros((5,2))])
def test_invalid_geometry_is_rejected(bad):
    with pytest.raises(ratios.RatioError): ratios.ratio_features(bad,640,800)


def test_oblique_face_is_rejected():
    p=points(); p[1]=[.7,.53]
    with pytest.raises(ratios.RatioError,match="FACE_NOT_FRONTAL"): ratios.ratio_features(p,640,800)


def test_reference_self_match_and_gender_filter():
    data=ratios.load_references()
    for row in data["characters"]:
        result=ratios.rank_ratios(np.array(row["features"]),data,row["gender"],balanced=False)
        assert result["characterId"]==row["id"]
        assert result["ranking"][0]["distance"]==0
        assert len(result["ranking"])==4


def test_stale_references_are_rejected(monkeypatch,tmp_path):
    data=ratios.load_references(); data["characters"][0]["sourceSha256"]="stale"
    path=tmp_path/"references.json"; path.write_text(json.dumps(data))
    monkeypatch.setattr(ratios,"REFERENCES",path)
    with pytest.raises(ratios.RatioError,match="RATIO_REFERENCES_UNAVAILABLE"): ratios.load_references()


def test_distribution_mapping_preserves_geometry_and_gender_without_rotation(monkeypatch):
    data=ratios.load_references(); correction=ratios.load_balance()
    # Remove learned prior offsets to isolate the domain transform.
    correction["bias"]={"any":[0]*8,"male":[0]*4,"female":[0]*4}
    monkeypatch.setattr(ratios,"load_balance",lambda:correction)
    for row in data["characters"]:
        relative=(np.array(row["features"])-correction["characterMean"])/correction["characterScale"]
        real=np.array(correction["realMean"])+relative*correction["realScale"]
        result=ratios.rank_ratios(real,data,row["gender"])
        assert result["characterId"]==row["id"]
        assert result["distributionCorrected"] is True
        assert result==ratios.rank_ratios(real,data,row["gender"])
        assert len(result["ranking"])==4 and result["ranking"][0]["distance"]==0


@pytest.mark.parametrize("invalid",["stale","nan","scale","bias"])
def test_invalid_balance_never_silently_returns_uncorrected_results(monkeypatch,tmp_path,invalid):
    data=ratios.load_balance()
    if invalid=="stale": data["referencesSha256"]="old"
    elif invalid=="nan": data["realMean"][0]=float("nan")
    elif invalid=="scale": data["realScale"][0]=0
    else: data["bias"]["male"]=[0]*3
    path=tmp_path/"balance.json"; path.write_text(json.dumps(data))
    monkeypatch.setattr(ratios,"BALANCE",path)
    with pytest.raises(ratios.RatioError,match="RATIO_REFERENCES_UNAVAILABLE"):ratios.load_balance()


def test_balanced_recommendation_is_repeatable_with_public_aggregate_statistics():
    correction=ratios.load_balance(); data=ratios.load_references()
    for gender,count in (("any",8),("male",4),("female",4)):
        result=ratios.rank_ratios(np.array(correction["realMean"]),data,gender)
        assert result==ratios.rank_ratios(np.array(correction["realMean"]),data,gender)
        assert len(result["ranking"])==count
        assert all(np.isfinite(row["distance"]) and row["distance"]>=0 for row in result["ranking"])


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("KIOSK_MATCH_LAB","1")
    monkeypatch.setattr(lab,"status",lambda:{"configured":True})
    sface={"ok":True,"top":0,"characters":[{"id":"char_01"},{"id":"char_03"}],"raw":[.4,.2],"order":[0,1],"elapsed_ms":40}
    monkeypatch.setattr(app,"match",AsyncMock(return_value=sface))
    monkeypatch.setattr(lab,"run_ratio_frame",lambda raw,gender,selected:{"ok":True,"characterId":"char_03","ranking":[],"elapsedMs":100})
    return TestClient(app.app,client=("127.0.0.1",12345))


def compare(client,gender="female"):
    photo=BytesIO(); Image.new("RGB",(32,32)).save(photo,format="PNG")
    return client.post("/api/experiments/matching/compare",data={"character_gender":gender},files={"frame":("reference.png",photo.getvalue(),"image/png")})


def test_comparison_uses_the_same_production_frame_and_preference(client):
    response=compare(client); data=response.json()
    assert response.status_code==200 and data["sameRecommendation"] is False
    assert data["sface"]["characterId"]=="char_01" and data["ratios"]["characterId"]=="char_03"
    assert data["externalUpload"] is False and data["experimental"] is True
    assert app.match.await_args.args[1]=="female"


def test_experiment_is_explicit_and_validated(client,monkeypatch):
    monkeypatch.setenv("KIOSK_MATCH_LAB","0"); assert compare(client).status_code==403
    monkeypatch.setenv("KIOSK_MATCH_LAB","1"); assert compare(client,"unknown").status_code==422
    monkeypatch.setattr(lab,"status",lambda:{"configured":False}); assert compare(client).status_code==503


def test_unstable_landmarks_never_return_a_fake_result(client,monkeypatch):
    def fail(*_): raise ratios.RatioError("FACE_NOT_FRONTAL")
    monkeypatch.setattr(lab,"run_ratio_frame",fail)
    response=compare(client)
    assert response.status_code==422 and response.json()["error"]["code"]=="FACE_NOT_FRONTAL"
    assert not lab.COMPARISON_LOCK.locked()


def test_busy_comparison_and_empty_frame_are_rejected(client):
    with lab.COMPARISON_LOCK:
        assert compare(client).status_code==409
    assert client.post("/api/experiments/matching/compare",files={"frame":("empty.png",b"","image/png")}).status_code==400

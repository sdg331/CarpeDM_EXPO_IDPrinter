from io import BytesIO
from types import SimpleNamespace

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import backend.app as backend_app


@pytest.fixture
def client(monkeypatch):
    # The excluded female candidate has the highest score; filtering must
    # choose the highest eligible male, not the first male in the catalogue.
    proto = SimpleNamespace(
        ids=[f"char_{i:02d}" for i in range(1, 9)],
        groups=["?"] * 8,
        match_scores=lambda *_: np.array([.9, .1, .8, .5, .7, .3, .6, .2], np.float32),
    )
    face = {"count":1,"selection":"largest_visible_face","source":"yunet","imageSize":[32,32],
            "box":[.1,.1,.8,.8],"landmarks":[[.3,.3],[.7,.3],[.5,.5],[.3,.7],[.7,.7]]}
    engine = SimpleNamespace(embed_primary=lambda *_args: (np.ones(128), SimpleNamespace(confidence=.99),face))
    monkeypatch.setitem(backend_app.STATE, "proto", proto)
    monkeypatch.setitem(backend_app.STATE, "engine", engine)
    monkeypatch.setitem(backend_app.STATE, "mu_real", None)
    return TestClient(backend_app.app, client=("127.0.0.1", 12345))


def request_match(client, gender=None):
    stream = BytesIO()
    Image.new("RGB", (32, 32), "white").save(stream, format="PNG")
    return client.post("/api/match", files={"frame": ("capture.png", stream.getvalue(), "image/png")},
                       data={} if gender is None else {"character_gender": gender})


@pytest.mark.parametrize("gender,top,order", [
    (None, 0, [0, 2, 4, 6, 3, 5, 7, 1]),
    ("any", 0, [0, 2, 4, 6, 3, 5, 7, 1]),
    ("male", 3, [3, 5, 7, 1]),
    ("female", 0, [0, 2, 4, 6]),
])
def test_preference_limits_ranking_and_display(client, gender, top, order):
    response = request_match(client, gender)
    assert response.status_code == 200
    data = response.json()
    assert data["top"] == top
    assert data["order"] == order
    assert data["characterGender"] == (gender or "any")
    assert len(data["raw"]) == len(data["display"]) == 8
    assert abs(sum(data["display"]) - 100) < .3
    assert all(data["display"][i] == 0 for i in set(range(8)) - set(order))
    assert data["margin"] == pytest.approx(.2 if gender == "male" else .1)


def test_unknown_preference_is_rejected(client):
    assert request_match(client, "unknown").status_code == 422


def test_empty_candidate_set_never_falls_back(client, monkeypatch):
    monkeypatch.setattr(backend_app, "CHARACTER_GENDERS", {})
    assert request_match(client, "male").status_code == 503

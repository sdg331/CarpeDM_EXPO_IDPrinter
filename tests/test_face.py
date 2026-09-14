"""매칭 엔진 계약 테스트 — 게이트에서 검증한 성질이 코드 수정으로 깨지면 여기서 잡는다."""

import json
from pathlib import Path

import numpy as np
import pytest

from backend.face import Prototypes, display_scores, l2_normalize, load_groups

ROOT = Path(__file__).resolve().parent.parent
PROTO = ROOT / "assets" / "prototypes.npz"


@pytest.fixture(scope="module")
def proto() -> Prototypes:
    if not PROTO.exists():
        pytest.skip("prototypes.npz 없음 — build_prototypes.py 먼저")
    return Prototypes.load(PROTO)


def test_프로토타입_형태(proto):
    assert len(proto.ids) == 8
    assert proto.vectors.shape == (8, 128)
    # 각 행이 L2 정규화돼 있어야 내적 = 코사인이 성립한다
    norms = np.linalg.norm(proto.vectors, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


def test_뮤스타일은_독립_표본이다(proto):
    """μ_style 이 8종 자기 평균으로 떨어지면 잔차 상관이 −1/7 로 강제된다(PLAN §7.4)."""
    assert proto.mu_style is not None
    assert proto.style_n >= 24, f"스타일 표본 {proto.style_n}장 — 24장 이상이어야 한다"


def test_잔차_분리도_게이트(proto):
    """캐릭터 교체의 통과 기준 그 자체 — 잔차 최대 쌍 < 0.36."""
    r = proto.residuals()
    m = r @ r.T
    worst = m[np.triu_indices(8, 1)].max()
    assert worst < 0.36, f"잔차 최대 쌍 {worst:.3f} — 캐릭터를 다시 골라야 한다"


def test_그룹은_파일과_일치(proto):
    """groups.json 이 있으면 프로토타입에 저장된 그룹과 같아야 한다."""
    gpath = ROOT / "assets" / "characters" / "groups.json"
    expected = load_groups()
    for cid, g in zip(proto.ids, proto.groups):
        assert expected.get(cid) == g, f"{cid}: npz={g} / 파일={expected.get(cid)}"
    if gpath.exists():
        on_disk = json.loads(gpath.read_text(encoding="utf-8"))
        assert set(on_disk) == set(proto.ids)


def test_표시점수는_확률분포다():
    raw = np.array([0.3, 0.1, -0.2, 0.05, 0.0, -0.1, 0.15, 0.02], np.float32)
    disp = display_scores(raw, temperature=0.08)
    assert abs(disp.sum() - 1.0) < 1e-6
    # 순위가 보존돼야 한다 — 화면 막대와 실제 계산이 어긋나면 거짓말이 된다
    assert list(np.argsort(raw)) == list(np.argsort(disp))


def test_매칭점수_경로(proto):
    """백엔드가 쓰는 match_scores 가 (8,) 를 내고, μ_real 유무 모두 동작한다."""
    rng = np.random.default_rng(7)
    fake = l2_normalize(rng.normal(size=128).astype(np.float32))
    s0 = proto.match_scores(fake, None)
    s1 = proto.match_scores(fake, l2_normalize(rng.normal(size=128).astype(np.float32)) * 0.8)
    assert s0.shape == s1.shape == (8,)
    assert np.isfinite(s0).all() and np.isfinite(s1).all()

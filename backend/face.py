"""얼굴 검출(YuNet) · 임베딩(SFace) · 8종 매칭 엔진.

검증 스크립트와 FastAPI 백엔드가 **이 모듈 하나만** 쓴다. 매칭 로직이 두 곳에
갈라지면 게이트에서 검증한 수치와 전시에서 실제로 도는 수치가 달라진다.

용어
    임베딩   SFace가 뽑는 128차원 벡터. 여기서는 항상 L2 정규화해서 다룬다.
    프로토타입  캐릭터 한 명을 대표하는 벡터. 변형 이미지가 있으면 평균낸다.
    원시 점수  프로토타입과의 코사인 유사도. 실제로는 좁은 구간에 몰린다(0.0~0.3).
    표시 점수  8종 원시 점수를 합 100으로 정규화한 값. 화면에 보여주는 건 이쪽이다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"

YUNET = MODELS / "face_detection_yunet_2023mar.onnx"
SFACE = MODELS / "face_recognition_sface_2021dec.onnx"

# 검출은 축소본에서 하고 정렬 크롭만 원본에서 한다.
# 원본(1086×1448)에서 바로 검출하면 100~220ms인데 640으로 줄이면 훨씬 빠르고,
# 정렬 크롭은 원본 좌표로 하니까 화질 손해가 없다. 파이 5에서 특히 중요하다.
DETECT_MAX_SIDE = 640

GROUPS_PATH = ROOT / "assets" / "characters" / "groups.json"

# **옛 8종(2×2×2 큐브 설계) 전용 폴백이다.** 하관 폭 축(A=각진, B=갸름)이
# 결과적으로 성별 축과 일치했기 때문에 파일명에 그대로 박아둘 수 있었다.
#
# select_characters.py 로 후보 풀에서 다시 고르면 char_01~08 이 max-min 선정
# 순서로 다시 매겨지므로 파일명과 그룹의 대응이 깨진다. 그래서 선정 시점에
# groups.json 을 함께 쓰고, 이 표는 그 파일이 없을 때만 쓴다.
LEGACY_GROUPS = {
    "char_01": "A", "char_02": "A", "char_05": "A", "char_06": "A",
    "char_03": "B", "char_04": "B", "char_07": "B", "char_08": "B",
}


def load_groups() -> dict[str, str]:
    """char_XX → 그룹. 선정 결과(groups.json)가 있으면 그쪽이 우선이다."""
    if GROUPS_PATH.exists():
        return json.loads(GROUPS_PATH.read_text(encoding="utf-8"))
    return dict(LEGACY_GROUPS)


class NoFaceError(Exception):
    """얼굴을 찾지 못했다."""


class MultipleFacesError(Exception):
    """얼굴이 둘 이상이다 — 뒤에 선 사람이 함께 잡힌 경우."""

    def __init__(self, count: int):
        super().__init__(f"얼굴이 {count}개 검출됐다")
        self.count = count


@dataclass
class Detection:
    """검출된 얼굴 하나. box/landmarks는 원본 이미지 좌표계다."""

    row: np.ndarray          # YuNet 출력 한 행 (15개 값)
    confidence: float

    @property
    def box(self) -> tuple[int, int, int, int]:
        x, y, w, h = self.row[:4]
        return int(x), int(y), int(w), int(h)


class FaceEngine:
    """YuNet + SFace를 감싼다. 모델 로드가 무거우니 프로세스당 하나만 만든다."""

    def __init__(self, score_threshold: float = 0.6, nms_threshold: float = 0.3):
        for path in (YUNET, SFACE):
            if not path.exists():
                raise FileNotFoundError(
                    f"모델이 없다: {path}\nscripts/fetch_models.sh 를 먼저 실행할 것."
                )
        self._det = cv2.FaceDetectorYN.create(
            str(YUNET), "", (320, 320), score_threshold, nms_threshold, 5000
        )
        self._rec = cv2.FaceRecognizerSF.create(str(SFACE), "")

    # ---------- 검출 ----------

    def detect(self, bgr: np.ndarray) -> list[Detection]:
        """모든 얼굴을 신뢰도 내림차순으로 돌려준다. 좌표는 원본 기준."""
        h, w = bgr.shape[:2]
        scale = min(1.0, DETECT_MAX_SIDE / max(h, w))

        if scale < 1.0:
            small = cv2.resize(bgr, (round(w * scale), round(h * scale)),
                               interpolation=cv2.INTER_AREA)
        else:
            small = bgr

        sh, sw = small.shape[:2]
        self._det.setInputSize((sw, sh))
        _, faces = self._det.detect(small)
        if faces is None or len(faces) == 0:
            return []

        out = []
        for row in faces:
            row = row.astype(np.float32).copy()
            if scale < 1.0:
                # 앞 14개가 좌표(박스 4 + 랜드마크 10), 마지막이 신뢰도다.
                row[:14] /= scale
            out.append(Detection(row=row, confidence=float(row[-1])))

        out.sort(key=lambda d: d.confidence, reverse=True)
        return out

    # ---------- 임베딩 ----------

    def embed(self, bgr: np.ndarray, det: Detection) -> np.ndarray:
        """128차원 L2 정규화 임베딩."""
        aligned = self._rec.alignCrop(bgr, det.row)
        feat = self._rec.feature(aligned).flatten().astype(np.float32)
        return l2_normalize(feat)

    def embed_single(self, bgr: np.ndarray, *, strict: bool = True) -> tuple[np.ndarray, Detection]:
        """관람객 촬영용 — 얼굴이 정확히 하나일 때만 통과시킨다.

        strict=False 는 캐릭터 원본처럼 신뢰할 수 있는 입력에 쓴다.
        """
        dets = self.detect(bgr)
        if not dets:
            raise NoFaceError("얼굴을 찾지 못했다")
        if strict and len(dets) > 1:
            raise MultipleFacesError(len(dets))
        return self.embed(bgr, dets[0]), dets[0]


def l2_normalize(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


# ---------- 프로토타입 ----------


@dataclass
class Prototypes:
    ids: list[str]
    vectors: np.ndarray               # (8, 128), 각 행 L2 정규화
    counts: list[int]                 # 평균에 들어간 이미지 수
    groups: list[str]
    mu_style: np.ndarray | None = None  # 생성 스타일 방향 (스타일 세트에서 추정)
    style_n: int = 0                    # μ_style 추정에 쓴 이미지 수

    @classmethod
    def load(cls, path: Path) -> "Prototypes":
        z = np.load(path, allow_pickle=False)
        mu = z["mu_style"].astype(np.float32) if "mu_style" in z.files else None
        return cls(
            ids=[str(s) for s in z["ids"]],
            vectors=z["vectors"].astype(np.float32),
            counts=[int(c) for c in z["counts"]],
            groups=[str(s) for s in z["groups"]],
            mu_style=mu,
            style_n=int(z["style_n"][0]) if "style_n" in z.files else 0,
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(
            ids=np.array(self.ids),
            vectors=self.vectors,
            counts=np.array(self.counts),
            groups=np.array(self.groups),
            style_n=np.array([self.style_n]),
        )
        if self.mu_style is not None:
            payload["mu_style"] = self.mu_style
        np.savez(path, **payload)

    # ---------- 점수 ----------

    def raw_scores(self, emb: np.ndarray) -> np.ndarray:
        """보정 없는 코사인. 벡터가 전부 정규화돼 있으니 내적이 곧 코사인이다.

        참고 — 관람객 임베딩 v에 대해 v·pᵢ = v·μ + v·rᵢ 이고 v·μ는 8종 공통이라,
        **순위 자체는** 공통 성분과 무관하다. 공통 성분이 망가뜨리는 건 순위가 아니라
        1·2위 사이의 마진(잔차 rᵢ의 크기)과 표시할 절대값이다.
        """
        return self.vectors @ l2_normalize(emb)

    def residuals(self) -> np.ndarray:
        """스타일 성분을 뺀 잔차 프로토타입 (8, 128), 각 행 재정규화.

        μ_style이 없으면 8종 자기 평균으로 대체하는데, 이때는 잔차 사이에
        −1/(n−1) = −0.143 의 음의 상관이 수학적으로 강제되므로 분리도를
        그대로 읽으면 안 된다. 스타일 세트로 추정한 μ가 있어야 정확하다.
        """
        mu = self.mu_style if self.mu_style is not None else self.vectors.mean(axis=0)
        return np.array([l2_normalize(v - mu) for v in self.vectors], dtype=np.float32)

    def match_scores(self, emb: np.ndarray, mu_real: np.ndarray | None = None) -> np.ndarray:
        """전시에서 실제로 쓰는 점수 — 도메인별 평균 제거 후 코사인.

        mu_real 은 실제 얼굴 표본에서 구한다(scripts/distribution_test.py --save).
        없으면 관람객 쪽 보정을 건너뛴다. 순위는 나오지만 특정 캐릭터로 쏠릴 수 있다.
        """
        v = l2_normalize(emb) if mu_real is None else l2_normalize(l2_normalize(emb) - mu_real)
        return self.residuals() @ v

    @property
    def style_energy(self) -> float:
        """공통 성분이 차지하는 에너지 비율. 1단계 진단에서 0.562였다."""
        mu = self.mu_style if self.mu_style is not None else self.vectors.mean(axis=0)
        return float(np.linalg.norm(mu) ** 2)


def display_scores(raw: np.ndarray, temperature: float = 0.05) -> np.ndarray:
    """원시 코사인을 화면용 분포로 바꾼다. 합이 1이 되며 순위는 보존된다.

    **왜 원시값을 그대로 안 쓰는가** — SFace는 동일인 검증 모델이라, 실제 사람과
    AI 생성 캐릭터 사이의 코사인은 8종 전부 0.0~0.3의 좁은 구간에 몰린다.
    0.18을 "유사도 82%"로 표시하면 근거 없는 숫자가 된다.

    대신 softmax로 "8종 중 상대적으로 어디에 가까운가"를 낸다. 이건 문자 그대로
    참이라 화면 문구("8종 중 이 캐릭터에 가장 가깝습니다")와 정확히 일치한다.
    temperature 는 1단계 분포 테스트 결과로 확정한다 — 작을수록 1등이 도드라진다.
    """
    z = (raw - raw.max()) / temperature
    e = np.exp(z)
    return e / e.sum()

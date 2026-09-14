# 실행 방법

## 전체 기동 (맥)

```bash
cd ~/Desktop/EXPO_Kiosk
./.venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8002
```

브라우저에서 **http://localhost:8002** 를 연다.
카메라 권한을 물으면 허용한다. `localhost`는 보안 컨텍스트로 취급되므로
HTTPS 없이도 `getUserMedia`가 동작한다.

> 포트 8002 — 8000은 carpedm-kiosk, 8001은 EXPO poc 백엔드가 쓴다.

## 상태 확인

```bash
curl -s localhost:8002/api/health
```

| 필드 | 의미 |
| --- | --- |
| `characters` | 캐릭터 수 (8이어야 정상) |
| `style_set_n` | μ_style 추정에 쓴 표본 수 |
| `mu_real_n` | 실제 얼굴 표본 수. **0이면 관람객 쪽 보정이 꺼져 있다** |
| `calibrated` | μ_real 적용 여부 |
| `max_pair` | 캐릭터 잔차 최대 쌍. 클수록 그 두 캐릭터를 구분 못 한다 |

화면 좌하단 배지에도 같은 상태가 뜬다 — `LIVE · 보정 완료` / `LIVE · μ_real 미보정` /
`MOCKUP · 백엔드 미연결`.

## 파이에 올리기 전 확인할 것 — 글꼴

화면은 **Pretendard** 를 먼저 찾는다. 맥에서는 없어도 Apple SD Gothic Neo 로 떨어져
비슷하게 보이지만, **파이에는 둘 다 없다.** 설치하지 않으면 조판이 눈에 띄게 달라진다.

```bash
sudo apt install fonts-pretendard || sudo apt install fonts-noto-cjk
```

이름 입력은 화면 키보드(두벌식)가 담당한다. 키오스크에는 물리 키보드가 없으므로
`inputmode="none"` 으로 OS 가상 키보드를 막아 두었다. 개발 중에는 물리 키보드로도
그대로 입력된다.

## 유휴 자동 리셋

관람객이 중간에 떠나면 다음 사람이 남의 이름과 부서가 박힌 화면을 마주한다.
마지막 조작에서 **90초**가 지나면 처음 화면으로 돌아간다.

말없이 날아가지는 않는다 — **75초에 경고와 카운트다운**이 뜨고, 화면 아무 데나
누르면 취소된다. 시연 중 설명하는 사이에 화면이 초기화되는 일을 막기 위한 것이다.

| | 값 | 위치 |
| --- | --- | --- |
| 전체 대기 | 90초 | `IDLE_MS` |
| 경고 구간 | 마지막 15초 | `WARN_MS` |
| 제외 화면 | 인트로 · 분석 중 · 출력 중 | `IDLE_SKIP` |

분석·출력 화면은 스스로 다음으로 넘어가므로 제외했다. 값은 `frontend/kiosk.html`
상단의 상수 세 개만 고치면 된다.

## 데모 중 백엔드가 죽으면

프론트가 자동으로 목업 점수로 폴백해서 흐름을 끝까지 진행한다.
화면이 멈추지 않으므로 시연을 계속할 수 있고, 좌하단 배지가 `MOCKUP`으로 바뀐다.

## 실제 얼굴 표본 모으기 (μ_real 보정)

`mu_real_n` 이 0이면 관람객 쪽 도메인 보정이 **꺼져 있다.** 순위는 나오지만 특정
캐릭터로 쏠린다. 이 값은 실측 말고 구할 방법이 없다 — 생성 이미지로 대신할 수 없다.
**이 사진들은 검증용이 아니라 엔진의 입력이다.**

### 1단계 · 사진 모으기 (둘 중 아무거나)

**웹캠으로 이어서 촬영** — 한 명씩 Enter, 번호는 자동으로 매겨진다.

```bash
./.venv/bin/python scripts/capture_faces.py --session
```

> 맥에서 "카메라를 열 수 없다" 가 나오면 시스템 설정 → 개인정보 보호 및 보안 →
> 카메라 에서 터미널을 켜고 **터미널을 완전히 껐다 다시 열 것.** 키오스크 화면에서
> 카메라가 되는 것과는 별개다 — 권한이 앱마다 따로 관리된다.

**사진을 직접 넣기** — 팀원이 보낸 셀카로도 된다. 촬영보다 이쪽이 빠를 수 있다.

```
data/test_faces/ 에 한 사람당 한 장
  · 정면, 얼굴 하나만 (뒤에 사람이 있으면 표본이 오염된다)
  · 파일명은 아무거나. png · jpg · webp
```

### 2단계 · 보정값 계산

```bash
./.venv/bin/python scripts/distribution_test.py --save
```

**저장 후 백엔드를 재시작해야 적용된다.** `curl -s localhost:8002/api/health` 의
`calibrated` 가 `true` 로 바뀌면 된 것이다.

### 몇 명이 필요한가

| 표본 | 쓸 수 있는 것 |
| --- | --- |
| 10명 | 방향 판단 — 쏠림이 줄어드는지 확인 |
| 40명 | 확정 — 캐릭터당 5명이라야 쏠림을 해석할 수 있다 |

### 읽는 법

`distribution_test.py` 는 두 가지를 나란히 보여준다.

- **A. 원시 코사인** — 보정 없음. 3~4종에 몰리는 게 정상이다.
- **B. 도메인별 평균 제거** — **전시에서 실제로 도는 경로.** 이쪽만 보면 된다.

통과 기준은 8종 중 6종 이상이 쓰이고, 1–2위 마진이 0.02 미만인 표본이 25% 미만인 것.
마진이 그보다 작으면 같은 사람이 찍을 때마다 다른 캐릭터가 나온다.

`--dir` 로 다른 폴더를 볼 수 있지만 그때는 `--save` 가 막힌다 — 배관 점검용이다.

## 자산 다시 굽기

```bash
./.venv/bin/python scripts/build_prototypes.py      # 임베딩 → assets/prototypes.npz
./.venv/bin/python scripts/similarity_matrix.py     # 8×8 분리도 점검
./.venv/bin/python scripts/make_print_assets.py     # 감열 인쇄용 1비트 (5단계)
```

**굽고 나면 백엔드를 재시작해야 한다.** 프로토타입은 기동 시 한 번만 읽는다.

## 캐릭터 8종 다시 고르기

8종은 설계로 정하지 않고 후보 풀에서 **측정해서** 고른다 — 근거는 PLAN.md §7.4.

```bash
./.venv/bin/python scripts/import_style_sheet.py assets/sheets/style_sheet_40.png \
    --start 1 --cols 8 --expect 40 --out pool
./.venv/bin/python scripts/select_characters.py            # 선정 결과만 확인
./.venv/bin/python scripts/select_characters.py --apply    # 반영
```

`--apply` 는 기존 8종을 `assets/characters/_previous/` 로 옮기고, 선정되지 않은
나머지를 `assets/style_set/`(μ_style 표본)으로 돌린다. 그룹 대응표
`assets/characters/groups.json` 도 이때 쓰인다 — 번호가 다시 매겨지므로 파일명만으로는
그룹을 알 수 없다. 이후 위의 "자산 다시 굽기"를 순서대로 실행한다.

판정 기준은 잔차 최대 쌍이다. `0.30` 미만이면 통과, `0.36` 이상이면 후보 풀을 늘려야 한다.

## 출력 (5단계)

발급은 `배지 렌더(576×808 1비트) → 출력 계층` 두 단계다. 백엔드는 환경변수로 고른다.

```bash
KIOSK_PRINT=screen   # 기본 — data/last_badge.png 로 저장 (개발·8/1 데모)
KIOSK_PRINT=escpos   # ESC/POS USB 감열 (전시). python-escpos 설치 필요
KIOSK_PRINT=cups     # CUPS 대기열
```

escpos 는 `lsusb` 로 확인한 ID 를 함께 준다:

```bash
KIOSK_PRINT=escpos KIOSK_ESCPOS_VENDOR=0x04b8 KIOSK_ESCPOS_PRODUCT=0x0e28 \
  ./.venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8002
```

⚠ escpos 백엔드는 **하드웨어 없이 검증 못 한 코드다.** 프린터가 오면 가장 먼저
`/api/health` 의 `printer.ready` 확인 → 발급 1회 → 대비 계수 조정(`--sweep`) 순서로 볼 것.

인쇄 실패(용지·단선)는 화면에 "인쇄에 실패했어요"로 뜨고 흐름은 초기화된다.
`data/last_badge.png` 는 이름이 들어가므로 커밋 금지(.gitignore 처리됨).

## 테스트

```bash
./.venv/bin/pytest tests/ -v
```

카메라·프린터·실제 얼굴 없이 돈다. 매칭 엔진 계약(잔차 게이트 < 0.36 포함)과
배지 렌더·발급 엔드포인트를 덮는다.

## API

| 엔드포인트 | 용도 |
| --- | --- |
| `GET /api/health` | 상태·진단 (프린터 상태 포함) |
| `GET /api/characters` | 캐릭터 8종 메타 |
| `POST /api/detect` | 프리뷰용 — 얼굴 유무만 (임베딩 생략) |
| `POST /api/match` | 촬영 프레임 → 8종 점수 |
| `POST /api/issue` | `{name, dept, char_id, emp_no}` → 배지 렌더 + 출력 |

`/api/match` 응답의 `raw`는 원시 코사인으로 **운영자 진단용**이다.
화면에는 `display`(합 100 정규화)만 쓴다 — 근거는 PLAN.md §2.1.

**얼굴 이미지는 어느 엔드포인트에서도 디스크에 쓰지 않는다.**

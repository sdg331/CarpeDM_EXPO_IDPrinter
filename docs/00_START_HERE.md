# START HERE — 프론트엔드 인수인계

이 문서는 처음 프로젝트를 맡은 사람이 **오늘 무엇을 해야 하는지**만 알려준다.

## 1. 먼저 이해할 것

이 프로젝트는 일반 웹사이트가 아니다.

```text
10.1" Touch Display
        ↓
Frontend UI
        ↓
Camera + FastAPI + AI + NFC + Printer
        ↓
MirrorTing Smart Mirror
```

관람객이 전시장에 와서 한 번의 짧은 세션을 완료하는 키오스크다.

## 2. 제품 경험

### 입사

```text
HOME
→ 팀 선택
→ 팀 상세
→ 이름 입력
→ AI 체험 A/B 선택
→ AI 방식 상세
→ 사진 촬영
→ AI 처리
→ 결과
→ NFC 등록
→ 사원증 출력
→ 스마트미러 안내
```

### 퇴근

```text
HOME
→ 퇴근하기
→ NFC 태그
→ MirrorTing 결과 조회
→ 퇴근 리포트 확인
→ 리포트 출력
→ 완료
```

## 3. 첫날 읽는 순서

1. `PROJECT_CONTEXT.md`
2. `CURRENT_CODE_AUDIT.md`
3. `PRODUCT_REQUIREMENTS.md`
4. `USER_FLOW.md`
5. `SCREEN_DEFINITION.md`
6. `DECISIONS.md`
7. Figma

개발 전에:
8. `DESIGN.md`
9. `UI_STATE_SPEC.md`
10. `API_CONTRACT.md`
11. `ACCEPTANCE_CRITERIA.md`

## 4. 프론트 담당 범위

담당:
- 화면 레이아웃/상태
- 사용자 입력
- 화면 전환
- 카메라 preview/capture UX (현재 방식 유지 시 브라우저 getUserMedia)
- FastAPI 호출
- Loading / Success / Error / Retry
- Mock scenario UI
- 800×1280 검증

직접 담당하지 않음:
- YuNet/SFace 모델 구현
- NFC USB SDK/PCSC 직접 제어
- ESC/POS 프린터 driver 직접 제어
- DB 스키마 결정
- NFC 저장 포맷 최종 결정

## 5. 현재 코드 실행 기준

CURRENT repository는 Python/FastAPI 기반이다.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows는 환경에 맞게 활성화
pip install -r requirements.txt
uvicorn backend.app:app --host 127.0.0.1 --port 8002
```

브라우저:

```text
http://localhost:8002
```

테스트:

```bash
pytest tests/ -v
```

## 6. 작업 시작 전 Git

`main`에서 직접 코딩하지 않는다.

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/scr-02-team-select
```

자세한 내용은 `GIT_WORKFLOW.md`.

## 7. 모르는 게 생기면

추측하지 않는다.

우선순위:
1. `DECISIONS.md`
2. `SCREEN_DEFINITION.md`
3. `USER_FLOW.md`
4. `DESIGN.md`
5. `API_CONTRACT.md`
6. 현재 코드
7. 프로젝트 담당자에게 질문

문서끼리 충돌하면 구현을 멈추고 충돌을 보고한다.

## 8. 완료 기준

`작동함` ≠ `완료됨`.

완료는 `ACCEPTANCE_CRITERIA.md`와 `TESTING_GUIDE.md`를 통과했을 때다.

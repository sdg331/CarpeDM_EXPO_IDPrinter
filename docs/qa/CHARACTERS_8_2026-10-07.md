# 캐릭터 8명 적용 · 2026-10-07

이 기록은 현재 인물 수에 관해 `CHARACTERS_12_2026-10-07.md`를 대체합니다.

- 활성 인물: 승인된 새 사진의 char_01~char_08.
- 9~12번 컬러/미리보기/인쇄 자산, 이전 groups.json 및 prototypes.npz: 상위 `completion-backups/portraits12-before-8-20261007/`에 보관.
- 안내: 4열×2행, 최대 폭 480px. 800×1280에서 8장 로드 완료 및 시작/이름 수정 버튼이 footer 위에 표시됨.
- 매칭: 기존 생성 스크립트로 8×128 비교 데이터를 재생성. 실행 서버를 재시작하고 `/api/characters`가 1~8번만 반환함을 확인.
- `npm test`: 46 passed. 9~12번 응답 거부 포함.
- `.venv/bin/python -m pytest tests/ -q`: 69 passed, 1 skipped, 1 warning. 독립 스타일 표본 분리도 검증은 보류. Starlette/httpx 경고는 기존 의존성 관련.
- `.venv/bin/python scripts/preflight.py`: 소프트웨어 및 8명 자산 점검 통과.
- `git diff --check`: 통과.
- 화면: `characters-8-800x1280.png`.
- 실제 관람객 매칭 품질, Raspberry Pi, 물리 터치, NFC/감열 출력은 이번 작업에서 검증하지 않음.

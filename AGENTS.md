# MIRRORTING WORKS — Agent Instructions

## Mission

MIRRORTING WORKS 키오스크의 확정된 제품 의도와 현재 동작을 보존하면서 **작고 검증 가능한 변경**을 수행한다.

## Read Before Working

모든 작업에서 먼저 읽기:
- `docs/PROJECT_CONTEXT.md`
- `docs/CURRENT_CODE_AUDIT.md`
- `docs/DECISIONS.md`

화면/UI 작업:
- `docs/USER_FLOW.md`
- `docs/SCREEN_DEFINITION.md`
- `DESIGN.md`
- `docs/UI_COMPONENT_GUIDE.md`

비동기/API/하드웨어 상태 작업:
- `docs/UI_STATE_SPEC.md`
- `docs/API_CONTRACT.md`
- `docs/ERROR_HANDLING.md`

완료 전:
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TESTING_GUIDE.md`
- `docs/FRONTEND_QA_CHECKLIST.md`

필요한 문서만 읽고, 불필요하게 전체 문서를 로드하지 않는다.

## Hard Constraints

- Target viewport: **800×1280 portrait**.
- Touch-first. Mouse/hover is never required.
- Physical keyboard is used only for `SCR-04 NAME_INPUT`.
- Existing FastAPI + YuNet + SFace + thermal print pipeline is the baseline.
- Do not invent API fields or hardware capabilities.
- Do not silently change confirmed user flow.
- Do not rename confirmed teams.
- Do not add external generative AI APIs to Mode B.
- Do not create random/fake production success when AI/NFC/print fails.
- Never expose raw stack traces or backend exception dumps to visitors.
- Never commit credentials, API keys, `.env` secrets, private keys, or passwords.
- Avoid framework migration during the exhibition sprint unless the owner explicitly approves it.

## Camera Boundary

CURRENT implementation uses browser `getUserMedia()` for preview/capture and sends frames to FastAPI for detection/matching.

Until explicitly changed:
- Browser preview/capture may remain frontend-owned.
- Face detection/matching/AI inference remains backend-owned.
- NFC and printer control must remain backend-owned.

Do not refactor the camera path merely to satisfy an abstract architecture rule if the current path is stable on Raspberry Pi.

## Work Process

### Before editing
1. Inspect current implementation.
2. Identify Screen ID / feature.
3. Read only relevant source-of-truth documents.
4. State what is CURRENT vs PROPOSED.
5. List files to change.
6. Implement the smallest valid change.

### During editing
- Reuse existing styles/functions/components before creating duplicates.
- Keep UI state explicit.
- Lock duplicate actions during capture, AI job, NFC write, badge print, report print.
- Preserve current session on retryable hardware errors.
- Ignore stale async responses from previous sessions/operations.
- Do not mix unrelated refactoring into feature work.

### After editing
1. Run relevant tests.
2. Run backend tests when backend contract is touched.
3. Verify 800×1280.
4. Verify touch-only path.
5. Check acceptance criteria.
6. Report files changed.
7. Report tests/verification performed.
8. Report unresolved risks/TBDs.

## Definition of Done

A task is done only when:
- requested behavior is implemented,
- required states exist,
- failure/retry behavior is defined where applicable,
- no unrelated behavior changed,
- relevant tests pass,
- 800×1280 was checked,
- session leakage is not introduced,
- docs are synchronized if contract/behavior changed.

## Git Safety

Do not work directly on `main`.

Never run without explicit human approval:
- `git reset --hard`
- `git clean -fd`
- `git push --force`
- `git push -f`
- history-rewriting commands on shared branches

If Git state is unclear: stop, run `git status`, `git diff`, `git log --oneline -5`, then explain before acting.

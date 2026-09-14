# Git & GitHub Workflow — 처음 쓰는 사람용

## 1. Git과 GitHub 차이

- **Git**: 내 컴퓨터에서 코드 변경 이력을 관리하는 도구
- **GitHub**: Git 저장소를 온라인에서 공유하고 PR/리뷰하는 서비스

## 2. 꼭 알아야 할 단어

- Repository: 프로젝트 저장소
- Clone: GitHub 저장소를 내 컴퓨터로 복사
- Branch: main과 분리된 내 작업 공간
- Commit: 의미 있는 변경 묶음의 저장 기록
- Push: 내 commit을 GitHub에 업로드
- Pull: GitHub의 최신 내용을 가져옴
- Pull Request(PR): 내 branch를 main에 합치기 전에 리뷰 요청
- Merge: 승인된 변경을 main에 합침
- Conflict: 같은 부분을 서로 다르게 수정해서 Git이 자동 결정 못 하는 상태

## 3. 원칙

복잡한 Git Flow를 사용하지 않는다.

```text
main
├─ feat/scr-02-team-select
├─ feat/ai-mode-ui
├─ fix/nfc-retry
└─ docs/api-contract
```

`main`에서 직접 작업하지 않는다.

## 4. 처음 한 번

```bash
git clone <repository-url>
cd <repository-folder>
git status
```

프로젝트 실행을 먼저 확인한다.

## 5. 새 작업 시작

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/scr-02-team-select
```

Branch examples:
- `feat/scr-02-team-select`
- `feat/ai-mode-ui`
- `fix/camera-double-submit`
- `docs/update-screen-definition`

## 6. 작업 중 확인

```bash
git status
git diff
```

가능하면 필요한 파일만 stage:

```bash
git add frontend/kiosk.html
git add docs/SCREEN_DEFINITION.md
```

`git add .`를 습관처럼 먼저 실행하지 않는다.

## 7. Commit

```bash
git commit -m "feat: implement team selection screen"
```

좋은 예:
- `feat: add ai mode detail screens`
- `fix: prevent duplicate badge print`
- `docs: confirm six team descriptions`
- `test: add nfc retry scenarios`

## 8. GitHub로 올리기

```bash
git push -u origin feat/scr-02-team-select
```

그다음 GitHub에서 Pull Request를 만든다.

## 9. PR에 쓸 내용

```md
## What changed
- SCR-02 팀 선택 화면 구현
- 6개 팀 2×3 배치

## Screen
SCR-02 TEAM_SELECT

## Verification
- [ ] 800×1280
- [ ] touch interaction
- [ ] acceptance criteria
- [ ] relevant tests

## Screenshots
Before / After 또는 구현 화면
```

## 10. 작업 도중 main이 바뀌었을 때

```bash
git switch main
git pull --ff-only origin main
git switch <내-브랜치>
git merge main
```

Conflict가 나오면 **멈춘다**.

무작정 `ours/theirs`를 고르지 않는다.
충돌 파일에서 두 변경의 의미를 확인하고, 모르면 팀원/AI에게 설명을 요청한다.

## 11. 절대 혼자 실행하지 말 것

다음 명령은 작업을 지우거나 shared history를 망가뜨릴 수 있다.

```text
git reset --hard
git clean -fd
git push --force
git push -f
```

담당자 승인 없이 실행 금지.

## 12. Secret 금지

Commit 금지:
- `.env` secret
- API key
- password
- private key
- local credential
- 개인 사진/임시 출력물

## 13. Git이 이상할 때

먼저:

```bash
git status
git diff
git log --oneline -5
```

이 3개 결과를 팀원/AI에게 보여주고 **작업을 잃지 않는 방법**을 물어본다.

## 14. 초보자 체크리스트

작업 시작:
- [ ] main 최신화
- [ ] 새 branch

Commit 전:
- [ ] git status 확인
- [ ] unrelated file 없음
- [ ] secret 없음
- [ ] 실행/테스트

PR 전:
- [ ] screenshot
- [ ] acceptance criteria
- [ ] 문서가 바뀔 필요 없는지 확인

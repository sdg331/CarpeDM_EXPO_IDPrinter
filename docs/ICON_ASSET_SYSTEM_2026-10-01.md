# MIRRORTING WORKS Icon & Asset System — 2026-10-01

## 1. Purpose

아이콘은 화면을 장식하기 위한 수단이 아니라:
- 행동을 빠르게 이해시키고
- 각 장면의 성격을 구분하며
- MIRRORTING WORKS의 시각적 세계관을 통일한다.

## 2. Three Asset Levels

### A. Hero 3D Object

큰 장면을 만드는 3D object.

Examples:
- HOME 사원증
- HOME 퇴근 리포트
- AI A character/matching object
- AI B profile/photo object
- completion object

Rules:
- screen당 1–2개
- 장식용으로 남발하지 않음
- main copy/CTA와 경쟁하지 않음

### B. Team 3D Icon

6개 팀을 구분하는 동일 family icon.

- 개발팀: code / terminal
- AI팀: AI chip / neural spark
- 디자인팀: pen / palette
- 기획팀: checklist / planning board
- 마케팅팀: megaphone
- 인사팀: people

모든 팀은:
- 동일 camera angle
- 동일 material family
- 동일 shadow softness
- 동일 visual weight

팀별로 완전히 다른 illustration style 사용 금지.

### C. Utility Vector Icon

작고 기능적인 icon.

Examples:
- back
- arrow
- close
- retry
- camera
- NFC
- printer
- warning
- success

Rules:
- simple vector/SVG
- 2px 내외 stroke family
- hero 3D와 경쟁하지 않음
- icon-only action은 가능하면 text/aria-label 제공

## 3. 3D Visual Language

Target:
- soft matte / semi-gloss plastic
- rounded forms
- clean studio light
- blue/white/charcoal 중심
- 필요 시 팀별 보조색 한 가지
- soft shadow
- friendly but not toy-like

Avoid:
- metallic cyberpunk
- excessive neon
- realistic human photo inside generic icon
- tiny unreadable text baked into image
- random camera angle per icon
- stock-looking emoji style

## 4. Home Hero Composition

HOME 중앙:
- employee ID badge object
- report/document object

배치:
- 서로 대각선
- 약한 depth difference
- one object slightly foreground
- central empty space/copy와 충돌하지 않음

의미:
- 사원증 = 출근/입사
- 리포트 = 퇴근/회고

## 5. Asset Format

Preferred:
- transparent WebP for runtime
- PNG master if alpha edge quality is better
- SVG for utility icons

Suggested source resolution:
- hero: 1024×1024 master
- team: 768×768 master
- runtime CSS display size는 화면별 조정

Do not:
- embed Korean/English text into raster icon
- bake background rectangle into transparent 3D asset
- upscale low-resolution generated asset

## 6. Naming

```text
frontend/assets/icons/
├─ hero/
│  ├─ home-badge.webp
│  ├─ home-report.webp
│  ├─ ai-character.webp
│  └─ ai-profile.webp
├─ teams/
│  ├─ team-development.webp
│  ├─ team-ai.webp
│  ├─ team-design.webp
│  ├─ team-planning.webp
│  ├─ team-marketing.webp
│  └─ team-hr.webp
└─ utility/
   ├─ arrow-right.svg
   ├─ back.svg
   ├─ close.svg
   ├─ retry.svg
   ├─ nfc.svg
   └─ printer.svg
```

## 7. Interaction

3D asset 자체를 복잡하게 애니메이션하지 않는다.

Pointer hover:
- scale: max 1.03–1.05
- translateY: -2px 정도
- shadow slightly stronger

Touch pressed:
- parent card scale 0.985
- icon may move 1–2px with parent
- no spin/bounce

Selected:
- icon brightness/contrast very slightly raised
- selection is primarily shown by card state

## 8. Asset Generation Workflow

1. 목적/의미 결정
2. 한 문장 object definition
3. shared style prompt 적용
4. transparent master 생성
5. edge/lighting/angle 검수
6. text artifact 제거
7. team family consistency comparison
8. WebP export
9. target screen에서 실제 size 확인

## 9. Prompt Template

Generated assets should be original rather than copies of another product's artwork.

```text
Create an original premium soft-3D UI icon for a Korean kiosk interface.
Object: [OBJECT]
Meaning: [ACTION/TEAM]
Material: rounded matte/semi-gloss plastic
Palette: MIRRORTING WORKS blue, white, charcoal, plus one restrained accent
Lighting: soft studio lighting, subtle ambient shadow
Camera: consistent 3/4 front angle
Background: transparent
No text, no logos, no watermark, no extra objects.
Friendly and clear, but not toy-like or cyberpunk.
```

"Toss-like" 등의 표현은 내부 mood reference로만 사용한다.
최종 asset은 독자적인 형태와 조합으로 제작한다.

## 10. Asset Review Checklist

- 6개 team icon을 한 화면에 놓았을 때 같은 family인가?
- 밝기와 shadow가 한 아이콘만 튀지 않는가?
- 100–160px 표시 크기에서도 의미가 보이는가?
- alpha edge halo가 없는가?
- embedded text artifact가 없는가?
- touch target과 icon이 혼동되지 않는가?
- icon이 정보보다 앞서지 않는가?

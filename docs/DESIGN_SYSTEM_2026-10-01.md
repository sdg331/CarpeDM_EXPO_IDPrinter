# MIRRORTING WORKS Design System — 2026-10-01

> 이 문서는 리디자인 목표 디자인 시스템을 정의한다.
> 수치는 프로젝트 자체 토큰이며 Toss/Apple 등 외부 제품의 공식 토큰이라고 주장하지 않는다.

## 1. Product Character

- 미래형 회사의 입사/출근/퇴근 터미널
- 전문적이지만 딱딱하지 않음
- 기술적이지만 한눈에 이해 가능
- 전시용으로 기억에 남되 SF HUD처럼 과장하지 않음
- 한 화면에 한 가지 주요 행동
- hardware가 기다리는 동안에도 멈춘 것처럼 보이지 않음

## 2. Canvas

- Base canvas: 800×1280
- Orientation: portrait
- Primary input: touch
- Pointer hover: desktop/demo 보조
- Main CTA target height: 96–112px 권장
- Minimum interactive target: 48×48 CSS px

## 3. Typography

Font:
- Pretendard Variable
- fallback: Noto Sans KR / system sans-serif

Base scale:
- Home display: 60px / 1.18 / 700
- Screen title: 52px / 1.2 / 700
- Section title: 34–40px / 1.25 / 700
- Body large: 28px / 1.5 / 500
- Body: 24px / 1.5 / 400–500
- Button: 30–32px / 1.2 / 600
- Label/caption: 20–22px / 1.4 / 500

Rules:
- 제목은 가능하면 2줄 이하
- 본문은 2~4줄 단위
- ultra-thin 금지
- 장식용 영문 all-caps 남용 금지

## 4. Color System

### Core

```css
--brand-blue: #2864ED;
--text-primary-light: #191F28;
--text-secondary-light: #5C6675;
--canvas-light: #FFFFFF;
--surface-light: #F5F6F8;
--border-light: #E5E8EB;

--canvas-dark: #0B0D10;
--surface-dark: #171A20;
--surface-dark-hover: #1D2128;
--text-primary-dark: #F4F6F8;
--text-secondary-dark: #9DA6B3;

--success: #20A66A;
--warning: #D89124;
--error: #D94C4C;
```

### Scene Background Strategy

모든 화면을 같은 배경으로 고정하지 않는다.

- Hero / completion: light or deep-dark를 화면 목적에 따라 선택
- Team explore/modal: dark premium scene 허용
- Name input: light/neutral focus scene
- Camera: camera full-bleed + dark overlay
- AI processing: darker immersive scene
- Report: light/editorial 또는 high-contrast paper-like surface

상태 의미는 배경이 바뀌어도 동일하게 유지한다.

## 5. Spacing

8px rhythm:
- 4 / 8 / 12 / 16 / 24 / 32 / 40 / 48 / 64 / 80

Suggested page:
- side inset: 48–64px
- header to title: 48–72px
- title to main content: 40–56px
- content to CTA: 40–64px

## 6. Radius

```css
--radius-sm: 14px;
--radius-md: 18px;
--radius-lg: 24px;
--radius-xl: 30px;
--radius-pill: 999px;
```

- Team card: 20–24px
- Modal: 28–30px
- CTA: 20–28px
- Small chips: pill

## 7. Elevation / Glass

Glassmorphism은 **modal/elevated layer에만 제한적으로** 사용한다.

Dark modal example:
- background: rgba(20, 23, 29, 0.86)
- backdrop-filter: blur(16–22px)
- border: 1px solid rgba(255,255,255,0.08)
- inner highlight: rgba(255,255,255,0.03)
- shadow: 0 24px 64px rgba(0,0,0,0.34)

금지:
- 모든 카드에 glass
- 과도한 neon outline
- 읽기 어려운 투명도

## 8. Motion Tokens

### Navigation

- normal screen enter: 280ms / translateY 12px → 0 / opacity
- reset/home: 160ms
- easing: cubic-bezier(0.22, 1, 0.36, 1)

### Touch

Pressed:
- duration: 120ms
- transform: scale(0.985)
- shadow slightly reduced

Release:
- duration: 220ms

Selected:
- background/edge highlight
- icon scale max 1.03–1.05
- no bounce

### Modal

Open:
- backdrop 0 → target opacity
- modal opacity 0 → 1
- scale 0.98 → 1
- translateY 10–12px → 0
- 240ms

Close:
- 140–160ms

### Result Reveal

- result image: blur 6–10px → 0 + opacity
- title: 80–120ms after image begins
- metadata: 60–100ms after title
- CTA: last
- total reveal should not unnecessarily block input

### Reduced Motion

`prefers-reduced-motion: reduce`:
- remove translate/scale animation
- keep state color/opacity feedback
- do not delay navigation for animation

## 9. Interaction State Matrix

Every interactive component considers:

- default
- pressed
- selected
- disabled
- loading
- success
- error

Pointer-only component may add:
- hover
- focus-visible

Hover cannot contain information unavailable on touch.

## 10. Key Component Rules

### TeamCard

Default:
- dark/neutral surface
- team 3D icon
- team title
- one-line summary
- arrow

Pointer hover:
- translateY -4px max
- icon scale 1.03
- arrow +4px
- border/brightness subtle only

Touch pressed:
- scale 0.985
- immediate tactile feedback

Selected:
- thin blue accent
- preserve card position
- open detail modal

### TeamDetailModal

- background page remains visible
- backdrop dim + mild blur
- team icon/title at top
- 1–2 sentence description
- keywords 3
- tasks 3
- primary CTA
- secondary "다른 팀 보기"
- close action optional but touch-safe

### Name Input

- text field is main visual object
- no unnecessary card grid
- visible focus
- Korean IME composition respected
- character count small but readable

### Camera

- preview dominates
- instruction must reflect real detection state
- capture CTA enabled only when ready
- no decoration competing with face framing

### NFC

States:
1. waiting
2. detected
3. registering/writing
4. verifying
5. success
6. timeout/error

Each state changes both copy and visual treatment.

### Printing

States:
- preparing
- printing
- success
- offline/error
- paper_out only when actual backend detection exists

Do not automatically reprint ambiguous outcomes.

## 11. Screen Uniqueness Checklist

Before approving a screen, ask:

1. Does this screen look too similar to the previous one?
2. Is the main interaction visually obvious from standing distance?
3. Is a card being used because it is useful, or just because other screens use cards?
4. Could the primary action become the visual scene itself?
5. Is there unnecessary blue/glow/3D decoration?
6. Does the transition explain state or merely decorate it?
7. Would the screen still make sense with hover unavailable?

## 12. QA

- 800×1280 browser screenshot
- target Pi/browser
- real 10.1-inch panel
- touch-only happy path
- reduced motion
- dark/light contrast
- Korean IME
- idle reset
- repeated tap stress
- back button during processing
- hardware disconnected/error states

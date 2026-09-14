# Frontend Architecture

## Decision

CURRENT frontend is vanilla HTML/CSS/JavaScript. For the EXPO sprint, **do not migrate framework**.

Reason:
- working prototype exists
- target is a single fixed-size kiosk
- Raspberry Pi/browser stability matters more than framework modernization
- beginner handoff should reduce moving parts

## Current

`frontend/kiosk.html` contains markup, CSS, data, state, API calls, camera, and navigation in one file.

This is acceptable as prototype but hard to hand off as features grow.

## Target Incremental Structure — PROPOSED

Split only when useful:

```text
frontend/
├─ kiosk.html
├─ styles/
│  ├─ tokens.css
│  ├─ components.css
│  └─ screens.css
├─ js/
│  ├─ app.js
│  ├─ state.js
│  ├─ navigation.js
│  ├─ content.js
│  ├─ api-client.js
│  ├─ camera.js
│  ├─ screens/
│  │  ├─ home.js
│  │  ├─ team.js
│  │  ├─ ai-mode.js
│  │  ├─ camera-screen.js
│  │  ├─ nfc.js
│  │  └─ printing.js
│  └─ mocks/
│     └─ scenarios.js
└─ assets/
```

Do not reorganize everything in one PR. Extract modules as screens are implemented.

## Dependency Direction

```text
Screen/UI
  ↓
App/Session State
  ↓
API Client
  ↓
FastAPI
  ↓
AI / NFC / Printer / DB
```

Camera exception:

```text
Browser getUserMedia → preview/frame capture
                      ↓
                   FastAPI AI
```

This matches CURRENT code and is allowed if stable on Raspberry Pi Camera Module 3.

## State

Recommended session model:
- sessionId
- flow
- team
- name
- aiMode
- capture reference/current frame only as needed
- aiResult
- nfc state
- print state
- checkout/report state

Do not store raw server responses indiscriminately.

## API Client

CURRENT code directly calls `fetch()` in screen functions.
Target: centralize request helpers/domain adapters so mock/error handling is consistent.

## Async Safety

For every operation:
- lock repeated user action
- bind response to current session/operation
- ignore stale response after reset
- preserve recoverable state

## Session Reset

One reset function must clear all visitor-specific state and visual remnants.

## Logging

Allowed diagnostic context:
- timestamp
- session ID if privacy policy allows
- screen ID
- operation
- error code
- request ID

Never log:
- raw photos
- secret keys
- full unnecessary personal data

## Future Framework Migration

React/Vite may be evaluated after EXPO only if:
- product scope stabilizes
- tests exist around current behavior
- migration is separate from new feature work

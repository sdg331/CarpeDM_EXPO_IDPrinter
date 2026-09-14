# Frontend Agent Instructions

Root `../AGENTS.md` rules also apply.

## Scope

This folder owns visitor-facing kiosk UI only.

## Current Stack

CURRENT frontend is plain HTML/CSS/JavaScript (`frontend/kiosk.html`) served by FastAPI.
Do not introduce React/Vite or another framework unless the project owner explicitly approves migration.

## Required References

Before screen changes read:
- `../docs/SCREEN_DEFINITION.md`
- `../docs/UI_STATE_SPEC.md`
- `../DESIGN.md`
- `../docs/ACCEPTANCE_CRITERIA.md`

Before API changes read:
- `../docs/API_CONTRACT.md`
- `../docs/ERROR_HANDLING.md`

## Rules

- 800×1280 portrait is primary viewport.
- Touch-first; mouse/hover not required.
- Physical keyboard only on NAME_INPUT.
- Current camera preview uses browser `getUserMedia`; keep AI/detection on backend.
- NFC/printer must not be controlled directly from browser code.
- Do not add random fallback AI results.
- Do not create success UI without backend-confirmed success for NFC/print.
- Protect irreversible actions against double tap.
- Reset stale visitor data between sessions.
- Use stable Screen IDs in code comments/diagnostics when useful.

## Verification

For UI tasks:
1. Run the project.
2. Check 800×1280.
3. Use keyboard only where intended.
4. Exercise success + at least one failure state.
5. Run existing tests if backend/API was touched.
6. Compare with Figma/Screen Definition.

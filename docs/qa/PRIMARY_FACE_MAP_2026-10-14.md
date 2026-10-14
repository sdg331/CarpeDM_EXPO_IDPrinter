# Exhibition primary face and real map QA

## Current problem and change

The old SCR-09 map was a fixed decorative12-point overlay at the center, unrelated to the captured face. Preview and production matching rejected multiple people. The new map uses actual normalized coordinates and shows only the selected face. Largest visible YuNet box approximates proximity; image-center distance then confidence break area ties. This is not depth measurement or persistent identity tracking.

## Files changed for this request

- backend/face.py: shared primary-face policy, actual box/five landmarks metadata, production embed_primary. Existing strict embed_single for assets/offline evaluation remains.
- backend/app.py: preview ready for one or more faces, same selection in matching, new optional face-map API.
- backend/face_ratios.py, backend/ratio_lab.py, scripts/ratio_frame.py: pass selected box to MediaPipe, select overlapping target, reject target mismatch. Dense map8s worker budget; existing comparison30s budget.
- frontend/js/face-overlay.js: validated coordinate data, contain/cover/mirror transform, real point/contour drawing; contour indices checked against installed MediaPipe definitions.
- frontend/js/camera.js, api-client.js, app.js, state.js: real target forwarding, multi-person capture, optional dense detail, processing toggle, captured-frame/stale-result guard and cleanup.
- frontend/js/views.js, frontend/styles/kiosk.css: remove decorative map from markup, actual canvases and accessible48px feature toggle, whole camera frame visible with contain, real map counts.
- frontend/js/matching-lab.js, matching-lab-core.js: same primary face during preview/comparison, actual detailed overlay on by default and feature checkbox.
- frontend/js/ui-preview.js, frontend/ui-preview.html: sample-only actual coordinate request, truthful preview disclosure and toggle. Styles/module cache revisions in kiosk.html, ui-preview.html, matching-lab.html and shared-module imports (including digital-badge.js).
- tests/test_primary_face.py, test_character_preference.py, test_face_ratios.py; frontend/face-overlay.test.mjs, kiosk.test.mjs, matching-lab.test.mjs.
- docs/API_CONTRACT.md, UI_STATE_SPEC.md, USER_FLOW.md, SCREEN_DEFINITION.md, ACCEPTANCE_CRITERIA.md, DECISIONS.md, FACE_RATIO_EXPERIMENT.md and this document.

## Actual checks

- `.venv/bin/python -m pytest tests integrations/mirrorting/test_bridge_client.py -q`:153 passed,1 existing skipped style-quality gate,1 existing Starlette/httpx warning.
- `npm test`:77 passed. Covers multi-person ready, contained/cropped/mirrored coordinates, invalid/missing map hidden, and late dense response rejected after visitor change.
- Node syntax, Python compileall, git diff --check passed.
- Real local8002 API with two public cartoon portraits (near/large char01 left, far/small char08 right): detect, match, face-map and comparison all successful, count2, identical selected left box approximately[0.163,0.313,0.216,0.363]. detect/match five real points; face-map/comparison478 points belonging to the selected left face. Aggregate QA result ../output/ratio-balance-20261014/primary-face-validation.json. Test image is temporary/public fictional art, not a visitor photo.
- Tests confirm low-confidence larger face beats high-confidence smaller bystander, clipped offscreen area is not favored, center tie is order-independent, and failed detail retains only five real points.
- UI fixed preview SCR-09 requests actual478 points from a labeled public character sample. On800×1280, actual eye/nose/mouth/outline alignment confirmed, #screen704px client/scroll width equal, feature toggle hides and restores canvas. Saved face-map-actual-800.jpg.
- Comparison UI with the two-face test file selected the larger left face and displayed actual points on that person, not the bystander.390×844 scroll width390, overlay and results visible. Saved primary-face-lab-390.jpg.
- Temporary comparison tab closed and viewport overrides reset. Analysis preview retained as the reviewable output. The user's existing photo tab was not reloaded or cleared.

## Behavior and limitations

Matching keeps working if dense MediaPipe is unavailable/busy; the map shows only actual YuNet5 points. Coordinates/images stay in current browser/server memory and are cleared on capture lifecycle/reset. Background detailed processing may continue up to8s after a browser abort; late replies cannot replace another visitor's data. No image/landmark records were added to DB or visitor logs.

Original booth camera permission/capture, moving real crowds, Raspberry Pi/ARM startup/latency, NFC and physical printer were not tested. Validation uses generated public portraits and actual local model inference plus browser/sample QA. Largest visible face is a proximity heuristic; no depth sensor claim. B composition and offline calibration retain strict single-face behavior; current visitor matching uses A.

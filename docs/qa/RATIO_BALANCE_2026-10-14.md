# Face ratio distribution correction QA

## Scope and files

- backend/face_ratios.py: domain transform, fixed gender-specific distribution costs, strict balance validation and deterministic ranking.
- backend/ratio_lab.py: status validates correction and exposes distributionCorrected.
- assets/face_ratio_balance.json: public aggregate statistics and reference/model fingerprints only.
- scripts/build_ratio_balance.py: disjoint people for fit/validation/diagnostic, entropy-regularized uniform prior, aggregate report and acceptance gate before atomic replacement.
- scripts/evaluate_face_ratios.py: original character self-tests explicitly use uncorrected geometry.
- frontend/matching-lab.html, js/matching-lab.js, js/matching-lab-core.js: correction disclosure, sample-image boundary, response flag validation and cache revisions.
- tests/test_face_ratios.py, tests/frontend/matching-lab.test.mjs: geometry mapping, repeatability, gender filtering, stale/malformed balance rejection, old uncorrected response rejection.
- README.md, docs/API_CONTRACT.md, docs/FACE_RATIO_EXPERIMENT.md, docs/DECISIONS.md and this QA.

## Distribution evidence

Public local LFW640 distinct people, seed20261013. First128 selected are the prior diagnostic set (102 valid). Of the subsequent valid people, first100 are validation and remaining274 are fit only. Exclusions:97 SFace multiple-face,1 MediaPipe multiple-face,66 non-frontal. No new photo, identity, individual-feature or landmark files retained.

Validation100 any before01..08:0,0,0,0,0,7,49,44; after:10,9,13,15,11,13,9,20. Male02/04/06/08:23/28/17/32; female01/03/05/07:22/20/25/33. Prior diagnostic102 any after:8,11,10,17,15,10,15,16. Aggregate report is ../output/ratio-balance-20261014/evaluation.json.

The validation cohort is disjoint from fitting people but from the same public dataset. These are distribution counts, not human likeness accuracy, demographic fairness or exhibition visitor acceptance. Exact uniform distribution is not promised. No runtime visitor counters, cycling or random assignment.

## Checks performed

- `.venv/bin/python -m pytest tests/test_face_ratios.py tests/test_character_preference.py tests/test_face.py tests/test_api_flow.py -q`:58 passed,1 skipped, existing Starlette/httpx warning.
- `npm test`:73 passed.
- Node syntax, Python compileall, git diff --check passed.
- Actual8002 health200, balance configured=true/distributionCorrected=true.
- Actual char_06 reference frame any twice/male/female:successful API,478 real points,8/4 valid candidates, repeated any rankings exactly equal. Cartoon input is engine QA, not likeness validation; current corrected results any01/male02/female01.
- Browser success in separate temporary test tab, updated correction/sample/privacy copy visible. Production session/NFC/print not called.
- 800×1280 and390×844 horizontal overflow absent. Photo clear hides results and disables compare. Temporary viewport reset and test tab closed. Screenshot `ratio-balance-800.jpg` documents public cartoon reference input only, not likeness quality.

## Limits

Main kiosk SFace matching is unchanged. Human likeness labels, Korean booth-camera distribution, real camera permissions, Raspberry Pi/ARM latency, NFC and physical printing were not tested here. Correction is for real photos; character sample self-matching is not preserved in the corrected mode.

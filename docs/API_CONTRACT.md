# API Contract

## Status

This file separates **CURRENT endpoints** from **PROPOSED extensions**.
Do not treat PROPOSED routes as already implemented.

## Current Backend Base

FastAPI serves frontend and API on the same origin in the existing design.

### GET `/api/health` — CURRENT

Use: AI/calibration/printer diagnostic.

### GET `/api/characters` — CURRENT

Returns 8 character metadata.

### POST `/api/detect` — CURRENT

Input: multipart `frame` image.

Current conceptual response:

```json
{
  "ok": true,
  "count": 1,
  "confidence": 0.98
}
```

Use for lightweight preview face-count checks.

### POST `/api/match` — CURRENT

Input: multipart `frame` image.

Success includes:
- `top`
- `characters`
- `display`
- `order`
- `raw` (operator diagnostic; do not expose to visitor)
- `margin`
- `confidence`
- `elapsed_ms`
- `calibrated`

Failure may include:
- `no_face`
- `multiple_faces`

Production frontend must not replace request failure with random result.

### POST `/api/profile` — CURRENT

Mode B local profile generation. Input is multipart `frame` and optional
`operation_id`. Processing stays on the kiosk backend: YuNet face/landmark
checks, local OpenCV background separation, and a close-up crop preserving the original face and clothing. No suit overlay or neck stretching is applied.

Success:

```json
{
  "ok": true,
  "profileId": "p_opaque_random_id",
  "previewUrl": "/api/profile/p_opaque_random_id/image",
  "expiresIn": 600,
  "reused": false
}
```

User-correctable failure remains a domain response so the UI can show retake
guidance: `no_face`, `multiple_faces`, `bad_position`, or `low_quality`.
There is no sample/random fallback.

### GET `/api/profile/{profile_id}/image` — CURRENT

Returns the generated PNG from the process-local temporary store with
`Cache-Control: no-store`. Missing and expired IDs return 404.

### DELETE `/api/profile/{profile_id}` — CURRENT

Idempotently removes the generated result when the browser session resets.
Expiry is the fallback when the browser closes before cleanup.

### POST `/api/issue` — CURRENT

Current request:

```json
{
  "name": "김지연",
  "dept": "AI팀",
  "char_id": "char_01",
  "emp_no": "MW2609140001"
}
```

CURRENT backend accepts character-based badge only. Mode B preview is
implemented, while Mode B physical badge rendering still requires extension.

---

## Target Frontend Service Interface — PROPOSED

The UI should depend on a logical API client, not scatter `fetch()` everywhere.

```text
getHealth()
getCharacters()
detectPreview(frame)
matchCharacter(frame)
generateProfile(frame, session)
createSession(profile)
registerNfc(sessionId)
issueBadge(sessionId / payload)
resolveCheckout()
getMirrorTingReport(sessionId)
printReport(reportId)
```

Exact REST names are backend-owner decisions.

## Session — PROPOSED

Recommended domain shape:

```json
{
  "sessionId": "MW-260914-0001",
  "flow": "checkin",
  "name": "김지연",
  "teamId": "ai",
  "aiMode": "A",
  "status": "active"
}
```

Backend should own stable employee/session ID. Browser random number should be removed.

## Mode B Generation — CURRENT PREVIEW / PRINT LINK TBD

The CURRENT `/api/profile` contract above supplies the generated preview and a
temporary `profileId`. The image is not placed in frontend state as base64.
Linking that `profileId` to the future server session and physical badge print
job remains TBD with the NFC/print contract.

## NFC Registration — PROPOSED

Backend owns ACR1252U read/write/verify.

Frontend contract concept:

```json
{
  "ok": true,
  "sessionId": "MW-260914-0001",
  "status": "verified"
}
```

Possible domain errors:
- `NFC_TIMEOUT`
- `NFC_READER_OFFLINE`
- `NFC_WRITE_FAILED`
- `NFC_VERIFY_FAILED`

### NFC payload direction

Product direction: card stores minimal identity/session information; details live in DB.

Final physical payload format is **TBD with backend/NFC implementation**. Do not hard-code in frontend.

## Checkout Resolve — PROPOSED

Backend waits for/read card then resolves session.

Result concept:

```json
{
  "sessionId": "MW-260914-0001",
  "name": "김지연",
  "teamId": "ai",
  "mirrorTing": {
    "status": "available",
    "scenario": "...",
    "summary": "...",
    "strength": "...",
    "nextAction": "..."
  }
}
```

Do not invent fields not produced by MirrorTing backend.

## Print Jobs — PROPOSED Extension

Current `/api/issue` is synchronous-ish. For stronger duplicate protection, backend may later expose job identity.

Concept:

```json
{
  "printJobId": "print_001",
  "status": "printing"
}
```

Possible states only if backend can detect:
- queued
- printing
- success
- offline
- paper_out
- error

## Error Envelope — PROPOSED

Prefer stable error codes:

```json
{
  "ok": false,
  "error": {
    "code": "NFC_WRITE_FAILED",
    "retryable": true,
    "requestId": "req_123"
  }
}
```

Visitor UI maps code to approved Korean copy. Raw backend text is not blindly shown.

## Mock Strategy

Current app has no formal MockApiClient; it has a dangerous random fallback.

Target:
- remove random fallback
- create deterministic mock scenarios for frontend-only development
- mock shape must equal real domain contract

Suggested scenarios:
- success
- slow success
- timeout
- retryable error
- fatal error

## Secrets

No API keys/secrets in browser code or client-exposed env variables.

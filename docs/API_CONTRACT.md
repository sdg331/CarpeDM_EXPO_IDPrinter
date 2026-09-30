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

CURRENT backend accepts character-based badge only. Mode B requires extension.

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

## Mode B Generation — PROPOSED

Could be one endpoint receiving captured frame or a capture/session reference.

Return only fields frontend needs, for example:

```json
{
  "ok": true,
  "profileId": "profile_001",
  "previewUrl": "/api/profile/profile_001/image"
}
```

Do not place base64 image blobs in global state if avoidable.

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


## Backend Extensions — CURRENT (2026-09-30)

The following routes are implemented on the feature backend and use durable SQLite state.

### POST `/api/nfc/register`

Creates/reuses a backend-owned session, reads the physical card UID through the NFC adapter, and binds that UID to the session.

Request:

```json
{
  "operationId": "browser-generated-idempotency-key",
  "name": "김지연",
  "teamId": "ai",
  "aiMode": "A",
  "result": {
    "kind": "A",
    "characterId": "char_01"
  }
}
```

Success:

```json
{
  "ok": true,
  "status": "verified",
  "sessionId": "MW2609300001"
}
```

Important:
- `operationId` is persistent idempotency state, not the employee number.
- a retryable NFC timeout reuses the same operation/session.
- crash recovery checks whether the UID binding was already committed.
- the current MVP reads the immutable UID and keeps the session mapping in SQLite.
- it does **not** claim that visitor data was written into NFC card memory.

### POST `/api/nfc/resolve`

Read-only checkout card resolution.

Request:

```json
{"operationId": "checkout-operation-id"}
```

Success:

```json
{
  "ok": true,
  "sessionId": "MW2609300001",
  "name": "김지연",
  "teamId": "ai"
}
```

Unknown cards return stable error code `UNKNOWN_CARD`.

### POST `/api/badge/print`

Idempotent badge print contract.

Request:

```json
{
  "operationId": "badge-print-operation-id",
  "sessionId": "MW2609300001"
}
```

Success:

```json
{
  "ok": true,
  "status": "success",
  "printJobId": "badge-print-operation-id",
  "backend": "screen"
}
```

If the printer raises after bytes may already have reached the device, the server records `UNKNOWN_OUTCOME` and does not automatically print again under the same operation ID.

### GET `/api/operations/{operationId}`

Operator/reconciliation endpoint for persistent side-effect state.

Possible stored statuses:
- `running`
- `success`
- `retryable_error`
- `unknown`
- `error`

### NFC backend configuration

Default is fail-closed:

```bash
KIOSK_NFC=disabled
```

Frontend/device development:

```bash
KIOSK_NFC=mock
KIOSK_NFC_MOCK_UID=04AABBCC
```

ACR1252U through PC/SC:

```bash
KIOSK_NFC=pcsc
```

Mode B generation, MirrorTing report retrieval, and report printing remain unimplemented until their contracts are verified.

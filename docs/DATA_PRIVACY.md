# Data & Privacy Notes

## Principle

Public exhibition kiosk should collect and retain the minimum data required for the experience.

## Name

Used for:
- badge
- personalized MirrorTing/check-out experience

Retention: final policy must be set by project owner/backend. Do not keep indefinitely by default.

## Face Image

CURRENT `/api/match` decodes image in memory and deletes references; it does not persist capture to disk.

Target direction:
- original photo not persistently stored unless explicitly required/approved
- no raw image in frontend log
- no cloud upload for Mode B

## Face Embedding

Mode A uses SFace embedding for matching. Treat feature data carefully; do not expose/log unnecessarily.

## Mode B Profile

Generated composite may need temporary session storage for badge printing.
Target: delete or expire after session/report retention purpose unless approved otherwise.

## NFC

CURRENT feature backend (2026-09-30):
- ACR1252U reads the card's immutable UID.
- visitor/session details are stored in local SQLite, not written into NFC card memory.
- reissuing the same physical card deactivates its previous active session binding.
- full photos and face embeddings are never stored in the card mapping.

Card-memory write remains TBD and must not be described as implemented.

## Logs

Avoid logging:
- raw photo
- full name unless necessary
- full NFC payload
- biometric feature vector

Prefer diagnostic IDs/error codes.

## Reset

Frontend reset must clear visitor state from memory/UI.
Backend state is now persisted in `data/kiosk.sqlite3` so browser reset/restart does not break idempotency.
The DB may contain visitor name + card UID + session metadata and is excluded from Git.
A final retention/automatic purge period is still **TBD**; do not retain the exhibition DB indefinitely.

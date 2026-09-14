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

Card should hold minimal identity/session data.
Do not put full photos or unnecessary private profile data on card.

## Logs

Avoid logging:
- raw photo
- full name unless necessary
- full NFC payload
- biometric feature vector

Prefer diagnostic IDs/error codes.

## Reset

Frontend reset must clear visitor state from memory/UI.
Backend retention and cleanup must be implemented separately and documented when final.

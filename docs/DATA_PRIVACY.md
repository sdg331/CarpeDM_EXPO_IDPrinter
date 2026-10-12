# Data & Privacy Notes

## Principle

Public exhibition kiosk should collect and retain the minimum data required for the experience.

## Name

Used for:
- badge
- personalized MirrorTing/check-out experience

Retention: final policy must be set by project owner/backend. Do not keep indefinitely by default.

## Face Image

Web upload accepts JPEG/PNG/WebP up to 8 MB and 12 megapixels. The browser
decodes and resizes the selected image to at most 1280 pixels before sending it
to the same local FastAPI server. Camera permission is requested only after
the visitor chooses to turn the camera on.

Web badge PNGs are composed in browser memory. Returning home revokes the
object URL and clears name/photo state. An explicitly downloaded PNG remains
in the user's chosen download location and is not removed by session reset.

CURRENT `/api/match` decodes image in memory and deletes references; it does not persist capture to disk.

Target direction:
- original photo not persistently stored unless explicitly required/approved
- no raw image in frontend log
- no cloud upload for Mode B

## Face Embedding

Mode A uses SFace embedding for matching. Treat feature data carefully; do not expose/log unnecessarily.

## Mode B Profile

The original capture is decoded and processed in memory and is not written to
disk. The generated PNG alone is held in a process-local store for 10 minutes
by default, capped at 8 entries. Browser reset requests immediate deletion;
expiry and process shutdown provide fallback cleanup. Image responses use
`Cache-Control: no-store`.

`KIOSK_PROFILE_TTL_SECONDS` and `KIOSK_PROFILE_MAX_ITEMS` can lower or raise
those operational limits. A future badge-print session may refer to the opaque
`profileId`; it must not put the photo itself on NFC.

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

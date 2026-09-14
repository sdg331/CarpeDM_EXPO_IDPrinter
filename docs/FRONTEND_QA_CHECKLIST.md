# Frontend QA Checklist

## Visual
- [ ] 800×1280
- [ ] no horizontal overflow
- [ ] main CTA not clipped
- [ ] consistent spacing/tokens
- [ ] status text readable over camera/result visuals
- [ ] no accidental tiny icon-only critical action

## Touch
- [ ] primary targets comfortably ≥48×48
- [ ] no hover dependency
- [ ] no precision drag
- [ ] rapid double tap handled

## Keyboard
- [ ] name input only
- [ ] Korean IME
- [ ] visible focus
- [ ] keyboard reconnect after reboot

## Check-in Flow
- [ ] HOME
- [ ] 6 teams
- [ ] team detail
- [ ] name
- [ ] A/B select
- [ ] A detail
- [ ] B detail
- [ ] camera
- [ ] AI processing
- [ ] result
- [ ] NFC
- [ ] badge print
- [ ] complete

## Check-out Flow
- [ ] HOME → checkout
- [ ] NFC resolve
- [ ] MirrorTing result
- [ ] report preview
- [ ] report print
- [ ] complete

## Failure
- [ ] camera unavailable
- [ ] no person
- [ ] multiple people
- [ ] AI error/timeout
- [ ] backend offline
- [ ] NFC timeout/write failure
- [ ] printer error
- [ ] unknown checkout card
- [ ] MirrorTing result missing

## Data Isolation
- [ ] previous name cleared
- [ ] previous team cleared
- [ ] previous AI image/result cleared
- [ ] previous NFC/print state cleared
- [ ] stale async response ignored

## Forbidden
- [ ] no random production AI result
- [ ] no fake NFC success
- [ ] no fake print success
- [ ] no raw stack trace
- [ ] no cloud Mode B upload unless explicitly approved

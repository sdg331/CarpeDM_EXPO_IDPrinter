# Figma Handoff Specification

## Purpose

Figma는 **visual source of truth**다.
기능/상태 계약은 Markdown 문서가 source of truth다.

## Recommended Pages

```text
00_COVER
01_USER_FLOW
02_FOUNDATIONS
03_COMPONENTS
04_WIREFRAMES_CHECKIN
05_WIREFRAMES_CHECKOUT
06_STATES_AND_ERRORS
07_HIFI_CHECKIN
08_HIFI_CHECKOUT
09_PROTOTYPE
99_ARCHIVE
```

## Frame Size

`800 × 1280`

## Frame Naming

```text
SCR-01__HOME__default
SCR-02__TEAM_SELECT__default
SCR-03__TEAM_DETAIL__development
SCR-04__NAME_INPUT__empty
SCR-04__NAME_INPUT__filled
SCR-04__NAME_INPUT__error
SCR-08__CAMERA__initializing
SCR-08__CAMERA__ready
SCR-08__CAMERA__no-person
SCR-08__CAMERA__multiple-people
SCR-08__CAMERA__capturing
SCR-08__CAMERA__error
SCR-12__NFC_REGISTER__waiting
SCR-12__NFC_REGISTER__writing
SCR-12__NFC_REGISTER__success
SCR-12__NFC_REGISTER__error
```

## Component Names

```text
CMP/Button
CMP/TeamCard
CMP/TeamDetail
CMP/AIModeCard
CMP/AIModeDetail
CMP/TextInput
CMP/StepHeader
CMP/StatusPanel
CMP/LoadingIndicator
CMP/CameraGuide
CMP/NFCInstruction
CMP/ResultCard
CMP/ErrorPanel
```

## Variants

Example Button:
- intent = primary | secondary | danger
- state = default | pressed | disabled | loading
- size = medium | large

Example TeamCard:
- state = default | pressed | selected | disabled
- team = development | ai | design | planning | marketing | hr

## Variables/Tokens

Collections:
- Color
- Typography
- Spacing
- Radius
- Motion

Use names matching DESIGN.md where practical.

Do not lock permanent brand Accent before Hi-Fi approval.

## Auto Layout Rules

- Use Auto Layout for cards, button content, vertical screen sections.
- Avoid manually positioned text inside reusable components.
- Prefer fill/hug rules that preserve 800px canvas behavior.
- Use consistent outer margins and 8px rhythm.

## Wireframe Order

1. Create all primary frames in grayscale.
2. Connect happy path prototype.
3. Add hardware/error states.
4. Test with a person who did not design it.
5. Update docs for discovered changes.
6. Finalize design tokens/components.
7. Build Hi-Fi.
8. Build production-like prototype.

## Prototype Rules

- Tap, not hover.
- Do not use impossible gestures.
- Simulate realistic wait states for AI/NFC/print.
- Include at least one failure/retry path.
- NAME_INPUT clearly indicates physical keyboard.

## Wireframe Gate

Do not start Hi-Fi until:
- [ ] flow approved
- [ ] screen list approved
- [ ] team/A-B content fits
- [ ] camera/NFC/print states represented
- [ ] no major 800×1280 overflow issue

## Hi-Fi Gate

Before frontend handoff:
- [ ] variables/tokens approved
- [ ] core components approved
- [ ] error states styled
- [ ] Figma and DESIGN.md agree
- [ ] frame names match Screen IDs
- [ ] happy + critical failure prototypes work

## Developer Handoff

For every frame:
- Screen ID in name
- state in name
- link/reference to corresponding Screen Definition section if possible

For every reusable component:
- description of semantics
- variants
- implementation note only when behavior is non-obvious

Do not rely on scattered sticky notes as the only spec.

# UI Component Guide

## Component Naming

Figma:
- `CMP/Button`
- `CMP/TeamCard`
- `CMP/AIModeCard`
- `CMP/TextInput`
- `CMP/StepHeader`
- `CMP/StatusPanel`
- `CMP/CameraGuide`
- `CMP/NFCInstruction`
- `CMP/ResultCard`
- `CMP/ErrorPanel`

Code names may be equivalent even in vanilla JS/CSS. Reuse classes/templates rather than screen-specific duplicates.

## Button

Properties:
- intent: primary | secondary | danger
- state: default | pressed | disabled | loading
- size: medium | large

Rules:
- min touch area 48×48
- primary CTA should be visually dominant
- disabled must be visible beyond color alone

## TeamCard

Props/data:
- id
- title
- icon
- selected
- disabled

States:
- default
- pressed
- selected
- disabled

Grid target: 2×3.

## TeamDetailCard

Contents:
- icon
- team title
- description
- 3 responsibilities
- 3 keyword chips
- secondary + primary actions

## AIModeCard

Props:
- mode A/B
- title
- summary
- illustration/icon
- selected

A and B use same structure/size.

## AIModeDetail

Contents:
- title
- short description
- HOW IT WORKS 5 steps
- back/change
- start CTA

## TextInput

Used on NAME_INPUT.

States:
- default
- focused
- filled
- error
- disabled

Requirements:
- Korean IME
- obvious focus
- 1–10 char validation
- physical keyboard hint

## StepHeader

Contents:
- optional back
- current step title
- optional progress rail

Do not show Back when unsafe during hardware side-effect.

## CameraGuide

Contents:
- preview
- dynamic guide/bounding indication
- instruction
- capture CTA

It does not own YuNet/SFace logic.

## StatusPanel

Generic waiting/working/success/error panel.

Use for NFC/printer/backend states.

## LoadingIndicator

- indeterminate by default
- real progress only if backend reports truthful progress

## NFCInstruction

States:
- waiting
- detected
- writing
- verifying
- success
- error

Animation should communicate where to tap, not decorate.

## ResultCard

A/B share structural rhythm.
Mode content can differ without duplicating entire layout.

## ErrorPanel

Must answer:
1. what happened
2. what to do next

Never show raw internal errors.

## Modal

Use sparingly.
Good:
- idle warning
- destructive reset confirmation

Bad:
- every normal navigation step

## Design Drift Rule

Before creating new component/style:
1. search Figma components
2. search current CSS/JS patterns
3. check DESIGN.md
4. create only if semantics genuinely differ

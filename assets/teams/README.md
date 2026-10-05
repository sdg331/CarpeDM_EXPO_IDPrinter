# Team icons

User-supplied PNGs from 2026-09-22, copied unchanged.

1. development.png — 개발팀 (blue code window)
2. ai.png — AI팀 (purple processor)
3. design.png — 디자인팀 (pink pencil)
4. planning.png — 기획팀 (teal plan)
5. marketing.png — 마케팅팀 (orange megaphone)
6. hr.png — 인사팀 (green people)

Shared by team selection, team details, and selected-team summary.
No ownership or license is inferred from the upload.

## Transparent versions — 2026-10-05

The kiosk uses `development-transparent.png`, `ai-transparent.png`,
`design-transparent.png`, `planning-transparent.png`,
`marketing-transparent.png`, and `hr-transparent.png` from this directory.
The original PNGs above remain unchanged. Each new file is a 1254×1254 RGBA
PNG with transparent exterior pixels; the white glass panel belongs to the
icon and is retained. The popup's separate white backing has also been removed.

Edited with the built-in Imagegen tool, `transparent_background: true`, using
one source icon per call. The common final prompt below was used for each of
`development`, `ai`, `design`, `planning`, `marketing`, and `hr`, substituting
the corresponding name for `[asset]`:

```text
Use case: background-extraction. Edit target: the supplied [asset] team icon, intended for an existing company kiosk UI. Remove only the exterior white/off-white studio backdrop, the floor/background and its broad colored floor glow. Output a genuinely transparent RGBA PNG with actual alpha, no checkerboard baked into pixels. Keep the original icon's full solid 3D object, including the frosted WHITE front panel which is part of the icon (do not remove that panel), its geometry, symbols, color palette, glossy highlights, camera angle, perspective, and centered square framing. Do not redesign or add anything. Preserve all isolated parts such as processor stars/rings and megaphone sound rays. The exterior around the object and the negative spaces must be alpha-transparent, with clean anti-aliased edges. No white rectangle, no colored backdrop, no surrounding tile, no floor, no text, no watermark. Preserve the provided icon, just cleanly cut it out.
```

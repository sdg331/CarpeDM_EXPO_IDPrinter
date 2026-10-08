# Kiosk glass icons

Generated 2026-10-05 with the built-in imagegen tool, using the supplied team PNGs as style references. Original team assets are unchanged. Merged into the current `CarpeDM_EXPO_IDPrinter-complete` UI served at port 8002. Applied through `frontend/js/views.js` to home entry, device NFC/print status, browser checkout and empty-report views. The current welcome text, team popup, transparent team artwork and checkout photo flow are preserved. These are decorative UI artwork, not device status evidence.

| File | Proposed use | Style reference |
| --- | --- | --- |
| checkin-badge.png | employee ID badge for entering a company | ../teams/development.png |
| checkout-report.png | take-home experience report for checking out | ../teams/hr.png |
| nfc-register.png | NFC card registration | ../teams/development.png |
| thermal-printer.png | compact thermal printer producing a report | ../teams/development.png |

All four originals are 1254×1254 PNGs with genuine alpha transparency. Keep alpha when exporting. `frontend/styles/kiosk-icons.css` sizes each image for its context (entry 64–88px, NFC 144–220px, error 112px). Small navigation icons remain SVGs. Error views shrink the artwork and preserve visible recovery actions.

Merge verification: `npm test` passed all 38 checks. Browser checks covered the 800×1280 home, the current team dialog with 26px work/keyword text, sample checkout with optional photo skipped, printer failure and successful retry, and 390×844 browser preview with no horizontal overflow or missing artwork. Real camera/NFC/printer operation was not part of this visual verification. Screenshots are in `../../docs/qa/merged-icons-*.png`.

## Generation prompts

### checkin-badge

Use case: style-transfer. Create a NEW sibling icon by transforming the supplied team artwork reference into the specified subject; reference is STYLE ONLY, original team images must remain untouched. Match the same premium rounded 3D design: translucent frosted glass, thick softly bevelled edges, polished coloured acrylic relief, softly rounded silhouettes, subtle blue-cyan edge refraction, gentle studio highlights from upper left, restrained pastel gradients, clean three-quarter front view at roughly 10 degrees, no aggressive metallic reflection. A single centred isolated icon in a square canvas, consistent visual mass filling 72% of canvas, generous padding on all sides. Real transparent alpha background, no opaque background rectangle, no drawn checkerboard. Keep the subject legible at small kiosk UI size. No text, letters, numerals, logos, watermark, arrows, unrelated decorative objects, sparkles, faces or photographic portraits.
SUBJECT: employee ID badge for entering a company. A rounded vertical frosted glass identification card with vivid blue/cyan acrylic back layer, a short integrated blue clip at its top, one simple raised blue head-and-shoulders silhouette, and two short geometric information bars below. Friendly, clean, sophisticated.

### checkout-report

Use case: style-transfer. Create a NEW sibling icon by transforming the supplied team artwork reference into the specified subject; reference is STYLE ONLY, original team images must remain untouched. Match the same premium rounded 3D design: translucent frosted glass, thick softly bevelled edges, polished coloured acrylic relief, softly rounded silhouettes, subtle blue-cyan edge refraction, gentle studio highlights from upper left, restrained pastel gradients, clean three-quarter front view at roughly 10 degrees, no aggressive metallic reflection. A single centred isolated icon in a square canvas, consistent visual mass filling 72% of canvas, generous padding on all sides. Real transparent alpha background, no opaque background rectangle, no drawn checkerboard. Keep the subject legible at small kiosk UI size. No text, letters, numerals, logos, watermark, arrows, unrelated decorative objects, sparkles, faces or photographic portraits.
SUBJECT: take-home experience report for checking out. One upright rounded frosted glass mint/teal report sheet with emerald acrylic backing, subtle folded upper-right corner, three broad mint geometric horizontal summary bars and a small glossy teal pie-chart circle near the top. No writing, no numbers. Same premium family, simple readable silhouette.

### nfc-register

Use case: style-transfer. Create a NEW sibling icon by transforming the supplied team artwork reference into the specified subject; reference is STYLE ONLY, original team images must remain untouched. Match the same premium rounded 3D design: translucent frosted glass, thick softly bevelled edges, polished coloured acrylic relief, softly rounded silhouettes, subtle blue-cyan edge refraction, gentle studio highlights from upper left, restrained pastel gradients, clean three-quarter front view at roughly 10 degrees, no aggressive metallic reflection. A single centred isolated icon in a square canvas, consistent visual mass filling 72% of canvas, generous padding on all sides. Real transparent alpha background, no opaque background rectangle, no drawn checkerboard. Keep the subject legible at small kiosk UI size. No text, letters, numerals, logos, watermark, arrows, unrelated decorative objects, sparkles, faces or photographic portraits.
SUBJECT: NFC card registration. One small rounded translucent glass reader puck in blue and pale lavender, shown as a compact horizontal base, with ONE small rounded blue glass employee ID card floating diagonally immediately above it. The card carries a simple head-and-shoulders relief. Exactly three rounded blue raised wireless signal arcs beside the card communicate contactless registration. Visually one cohesive icon, no hands, no cables, no screen.

### thermal-printer

Use case: style-transfer. Create a NEW sibling icon by transforming the supplied team artwork reference into the specified subject; reference is STYLE ONLY, original team images must remain untouched. Match the same premium rounded 3D design: translucent frosted glass, thick softly bevelled edges, polished coloured acrylic relief, softly rounded silhouettes, subtle blue-cyan edge refraction, gentle studio highlights from upper left, restrained pastel gradients, clean three-quarter front view at roughly 10 degrees, no aggressive metallic reflection. A single centred isolated icon in a square canvas, consistent visual mass filling 72% of canvas, generous padding on all sides. Real transparent alpha background, no opaque background rectangle, no drawn checkerboard. Keep the subject legible at small kiosk UI size. No text, letters, numerals, logos, watermark, arrows, unrelated decorative objects, sparkles, faces or photographic portraits.
SUBJECT: compact thermal printer producing a report. One rounded blue acrylic and frosted glass desktop thermal printer, simple box body in three-quarter front view, softly glowing pale-cyan edge detail, one wide white translucent receipt emerging visibly downward from the dark-blue front slot, two short embossed cyan geometric lines on paper and one small circular blue status light. No text, no cables, no extra paper rolls. Same blue family as the employee badge.

## Completion check · 2026-10-08

`completion-check.png` is a transparent 1254×1254 original generated with the built-in imagegen tool, using `../teams/development-transparent.png` and `checkin-badge.png` as style references. It is shared by check-in and checkout completion. The frosted glass slab and raised blue acrylic check share one perspective. No halo, stars, text or logos are baked into the artwork. Decorative motion is removed from the visitor UI; loading indicators remain.

# Kiosk glass icons

Generated 2026-10-05 with the built-in imagegen tool, using the supplied team PNGs as style references. Original team assets are unchanged. Applied through `frontend/js/views.js` to entry, card/print preview, empty-report, NFC and print-status views. These are decorative UI artwork, not device status evidence.

| File | Proposed use | Style reference |
| --- | --- | --- |
| checkin-badge.png | employee ID badge for entering a company | ../teams/development.png |
| checkout-report.png | take-home experience report for checking out | ../teams/hr.png |
| nfc-register.png | NFC card registration | ../teams/development.png |
| thermal-printer.png | compact thermal printer producing a report | ../teams/development.png |

All four originals are 1254×1254 PNGs with genuine alpha transparency. Keep alpha when exporting. CSS sizes each image for its context (entry 68–84px, NFC 144–236px, print preview 96px). Small navigation icons remain SVGs. Error views shrink the artwork and preserve visible recovery actions.

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

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

## Added glass icons · 2026-10-16

Generated with the built-in imagegen tool. Camera and service-attention art use `checkin-badge.png` and `checkout-report.png` as style references. The smart mirror was subsequently regenerated from the project's assembled-device concept and the badge style reference; see the product-specific prompt below. All three are 1254×1254 RGBA PNGs with genuine alpha transparency. Originals are kept in the generated-images directory; project copies live beside the existing five kiosk images.

| File | Applied use |
| --- | --- |
| photo-camera.png | Home photo-only entry (96px), analysis error/absent-photo artwork |
| smart-mirror.png | Project-specific MirrorTing device in web next-experience guidance (176px) |
| service-alert.png | Service maintenance screen |

These illustrations are decorative. They do not indicate camera/NFC/printer success. Existing navigation, camera overlays, retry controls and reduced-motion behavior remain unchanged.

Integration files: `frontend/js/views.js`, `frontend/styles/kiosk-icons.css`, `frontend/styles/kiosk.css`. Cache versions are updated in `frontend/js/app.js`, `frontend/js/ui-preview.js`, `frontend/kiosk.html` and `frontend/ui-preview.html`. Design references are synchronized in `DESIGN.md` and `docs/SCREEN_DEFINITION.md`; `tests/frontend/kiosk-icons.test.mjs` checks the new assets alongside existing recovery actions.

Validation: `npm test` passed 77 tests. The 800×1280 sample home loaded all three entry images with no horizontal overflow; the new camera entry reached the sample photo screen. Analysis-error, service-maintenance and web next-experience previews loaded their new art and retained visible actions. At 390×844 the sample home had no horizontal overflow and the photo entry remained visible at about 70px high. Actual camera/NFC/printer acceptance was not performed.

### Shared generation prompt

```text
Use case: stylized-concept. Asset type: original transparent PNG 3D illustration for the MIRRORTING WORKS kiosk. Input images 1 and 2 are STYLE REFERENCES ONLY; do not edit or reproduce their badge/report subjects. Create ONE new subject as a matching sibling in their existing icon family. Premium softly rounded 3D, thick frosted translucent white glass and polished blue/cyan acrylic relief, smooth broad bevels, subtle cyan refraction, soft studio highlights from upper left, clean near-frontal three-quarter perspective about 10 degrees, restrained colors. One centered isolated object on a square canvas, full silhouette occupies roughly 75 percent with generous clear margin. REAL transparent alpha background, no opaque background, no checkerboard pattern, no floor plane, no cast shadow outside the subject. Large simple readable shapes suitable for UI use at 96 to 340 CSS px. No text, letters, numerals, logos, watermarks, arrows, sparkles, extra floating decorations, people or faces.
```

### photo-camera

```text
Subject: a friendly compact camera. Rounded horizontal frosted-white translucent camera body with a rich royal-blue acrylic back layer. One large simple protruding circular lens in blue and cyan, a subtle dark-blue glass center with soft specular reflection, a small blue shutter button and short integrated viewfinder bump along the top. This is a polished UI camera icon, not a photorealistic camera model. Keep detailing minimal and the lens immediately recognizable.
```

### smart-mirror · initial generic study, replaced

```text
Subject: a smart mirror for the next visitor experience. A single upright portrait mirror with rounded rectangular frosted glass edges and a thick blue acrylic backing, on a short simple integrated blue desktop stand. Quiet pale icy-blue reflective center with one broad subtle diagonal sheen, no user interface, no camera eye, no buttons, no person or reflection of a person. Silhouette must read as an upright mirror rather than a phone. Same friendly glass material and simple blue relief language as the supplied references.
```

### service-alert

```text
Subject: a service attention symbol. A single softly rounded equilateral warning triangle made of thick frosted translucent white glass, with a polished blue acrylic rear layer, shown upright in the same gentle three-quarter view. The triangle carries one simple raised amber acrylic exclamation shape, one rounded vertical bar over one small rounded dot. These are solid geometry, not typography. Calm readable service attention, not danger or emergency. No gear, tools, additional objects or badge surrounding the triangle.
```

### smart-mirror · product-specific replacement

The owner requested the actual project's identity rather than a generic tabletop mirror. The structure reference is `CarpeDM_EXPO_Microsite/public/media/hardware/sm-assembled-v1.webp`, whose metadata identifies it as a supplied-drawing-based 3D concept. `checkin-badge.png` is the material/style reference. The top camera and microphone, side NFC module, two lower speakers and caster base are retained. Display waveform and empty dialogue lines are symbolic. This is neither a photograph nor manufacturing/integration evidence. The previous generic study is preserved in the chat workspace's `output/smart-mirror-before-product-20261016.png`.

The current icon remains `assets/kiosk-icons/smart-mirror.png`. It was generated with built-in imagegen and is displayed at 176px so the product outline remains readable.

Replacement validation: 77 frontend tests passed. The 1254×1254 PNG retains RGBA alpha. Browser checks at 800×1280 and 390×844 confirmed the current artwork, 176px image sizing, no horizontal overflow and the existing mobile column layout. Screenshots are in the chat workspace's `output/ui-mirrorting-device-guide-800-20261016.jpg` and `output/ui-mirrorting-device-guide-390-20261016.jpg`.

```text
Use case: stylized-concept. Asset type: transparent square 3D icon representing the actual project-specific MirrorTing conversation-training smart-mirror PRODUCT DESIGN, for a kiosk's next-experience guidance. Input image 1 is the PRODUCT STRUCTURE reference: the supplied-drawing based full-height assembled smart mirror with sensor modules, two lower speakers and caster base. Preserve these distinctive proportions and component placements. Input image 2 is MATERIAL/STYLE reference only: the existing blue/cyan acrylic and frosted-glass employee badge icon. Create ONE original matching sibling icon that unmistakably shows the WHOLE PRODUCT in image 1, simplified for legibility around 176 CSS px. Physical structure: a tall portrait rectangular dark reflective display in a slim graphite frame, slightly rounded corners; a short rounded rectangular DUAL-LENS camera bar on a small bracket at TOP CENTER, a separate compact flattened dark-blue microphone puck at TOP LEFT; a slim card-reader/NFC module attached to the RIGHT SIDE at lower-middle height; TWO clear round dark-blue speaker grilles in an angled low speaker console directly below the display; a low wide solid rectangular wheeled plinth with exactly four small caster wheels, three visible in this perspective; visible shallow rear support behind the display. The display extends down toward the speaker console, with NO thin stalk and NO desktop vanity-mirror stand. Keep the frame graphite so its industrial identity survives; use soft frosted white-silver highlights and restrained translucent blue acrylic depth on edges, speaker console and base to harmonize with reference 2. Mirror surface dark cool reflective glass with a quiet broad sheen, one very subtle small cyan voice-wave motif and two simple empty rounded conversation lines, no words or numbers; these are decorative UI cues. Clean near-frontal three-quarter view matching the reference assembly, modest depth, soft upper-left studio light, friendly polished rounded 3D, broad readable forms. Center the complete assembled product in a square canvas; full silhouette including sensors and wheels about 86 percent of canvas height with safe clear padding. TRUE transparent alpha outside the object; no white rectangle, no checkerboard pattern, no room/floor, no detached cast shadow. No people, faces, labels, logos, text, scores, percentages, floating panels, arrows, orbit rings or sparkles. Do not invent a printer or keyboard. This is a stylized representation of the project's supplied product concept, not a manufacturing-accurate rendering or hardware verification.
```

## Completion check · 2026-10-08

`completion-check.png` is a transparent 1254×1254 original generated with the built-in imagegen tool, using `../teams/development-transparent.png` and `checkin-badge.png` as style references. It is shared by check-in and checkout completion. The frosted glass slab and raised blue acrylic check share one perspective. No halo, stars, text or logos are baked into the artwork. Decorative motion is removed from the visitor UI; loading indicators remain.

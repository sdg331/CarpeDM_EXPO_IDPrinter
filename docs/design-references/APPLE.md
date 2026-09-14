# Apple Reference Design System

<!-- design-md:section experience -->
## 1. Experience

### Visual Theme & Atmosphere

Apple’s current design language makes hardware, software, content, and controls feel like one continuous system. On the public web, a small neutral palette, SF Pro optical families, and conspicuous blue actions leave product photography and page composition to carry most of the drama. Across Apple platforms, the newer Liquid Glass direction adds a translucent functional layer for controls and navigation while keeping content visually primary. The recognizable effect is not minimalism for its own sake: precise hierarchy, familiar behavior, platform harmony, and carefully limited ornament make complex capabilities feel immediately usable.

This reference distinguishes three evidence domains: `apple.com` marketing, Apple Store commerce/product UI, and the Human Interface Guidelines documentation website. HIG guidance may describe native-platform components, but the computed style of the HIG website is only evidence for its documentation chrome.

**Key Characteristics:**
- SF Pro Text: 600 visible uses on current Apple public pages; SF Pro Display: 31
- Primary filled action `#0071e3`; text link `#0066cc`; dark-surface link `#2997ff`
- 44px large pill and 36px compact pill coexist on the current homepage
- HIG documentation cards use an 18px radius but are not native-platform component tokens

### Do's and Don'ts

### Do
- Use SF Pro Display for verified large display roles and SF Pro Text for body/control roles.
- Name Apple web variants by surface and size.
- Use `#0071e3` for filled actions and `#0066cc` for light-surface links/outline actions.
- Keep selected state explicit in gallery-style tabs.
- Label HIG website chrome separately from native-platform HIG guidance.

### Don't
- Don't call the HIG website's 18px card a universal Apple platform card.
- Don't promote declared-only SF Mono or icon fonts as visible UI families.
- Don't treat `#0066cc` as a filled-button background.
- Don't collapse 36px and 44px marketing controls into one invented default.
- Don't infer hover, disabled, or focus visuals that were not retained by the capture.

### Brand Narrative

Apple publishes the Human Interface Guidelines as a living platform design system rather than a static visual kit. The current principles start from how people think, feel, and act, then organize design around purpose, agency, responsibility, familiarity, flexibility, simplicity, craft, and delight. This makes the system’s restraint functional: interfaces are expected to help people act, preserve context, recover from mistakes, and trust how their information is handled.

The 2025 software redesign introduced Liquid Glass across iOS, iPadOS, macOS, watchOS, and tvOS. Apple describes it as a shared material language that creates harmony while preserving what makes each platform distinct. Controls and navigation occupy a translucent functional layer above content; they should not become a decorative glass effect spread across the content layer.

Typography follows the same system logic. SF Pro is neutral and flexible, with optical sizing and platform integration; SF Compact adapts to narrow watch contexts; SF Mono supports alignment in coding environments; New York provides a serif companion. The family names matter less than using the platform role, license, and context correctly.

### Principles

These are implementation principles derived from the verified public surfaces:

1. Let product content dominate while controls remain visually restrained.
2. Use one clear chromatic action accent per local composition.
3. Match typography optical role to size: Display for large hierarchy, Text for reading and controls.
4. Keep marketing, commerce, documentation, and native-platform evidence separate.
5. Prefer verified component-local measurements over a fictional universal Apple scale.

### Personas

These are official design contexts from the Human Interface Guidelines, not invented demographic personas.

- **A person pursuing a goal:** expects the interface to stay out of the way, provide feedback, and make mistakes reversible.
- **A person protecting sensitive information:** needs clear reasons for permissions, transparent data behavior, and safe defaults.
- **A person using a different device, input, language, or accessibility setting:** needs the experience to adapt while preserving familiar structure and context.
- **A person learning a new interaction:** relies on established physical and digital patterns plus consistent behavior to build confidence quickly.

<!-- design-md:section foundations -->
## 2. Foundations

<!-- design-md:claim foundations kind=rules-or-constraints lang=en -->
### Color Palette & Roles

- **Primary Action** (`#0071e3`): current filled buttons across Apple-owned web surfaces.
- **Brand / Dark Canvas** (`#000000`): identity and immersive dark sections.
- **Fog Canvas** (`#f5f5f7`): light section and footer background.
- **Surface** (`#ffffff`): white content and HIG card surfaces.
- **Foreground** (`#1d1d1f`): principal text and selected commerce state.
- **Muted** (`#6e6e73`): secondary HIG documentation text.
- **Secondary** (`#515154`): another current HIG documentation neutral.
- **On Primary** (`#ffffff`): text on blue filled actions.
- **Link** (`#0066cc`): links and outline-button text/border on light surfaces.
- **Link on Dark** (`#2997ff`): brighter blue observed on dark Apple sections.

Do not infer a universal native-platform semantic palette from these web values. HIG platform colors are dynamic and context-dependent; this pass records public web evidence.
<!-- design-md:claim-end -->

### Depth & Elevation

No shadow token is canonical in this revision. Captured primary and outline buttons reported no shadow, and HIG reference cards were flat in computed style. Product imagery and color contrast create depth on the inspected surfaces.

### Motion & Easing

No exact Apple motion token is promoted from this web capture. Use relevant platform HIG guidance and reduced-motion support for native implementation; label any web animation duration or easing as a local extension until verified.

<!-- design-md:section typography-assets -->
## 3. Typography & Assets

### Typography Rules

### Font Family
- **Display**: `SF Pro Display`, loaded/high confidence, 31 visible uses across current Apple public pages.
- **Text**: `SF Pro Text`, loaded/high confidence, 600 visible uses across marketing and store surfaces; another 734 on HIG documentation surfaces.
- **SF Mono**: declared on the HIG site but not visibly used in this capture, so it is not promoted.

| Role | Family | Size | Weight | Line Height | Tracking |
|---|---|---:|---:|---:|---:|
| Display Hero | SF Pro Display | 56px | 600 | 60px | -0.28px |
| Section | SF Pro Display | 40px | 600 | 44px | normal |
| Tile Heading | SF Pro Display | 28px | 400 | 32px | 0.196px |
| Body | SF Pro Text | 17px | 400 | 25px | -0.374px |
| Body Small | SF Pro Text | 14px | 400 | 18.0008px | -0.224px |
| Caption | SF Pro Text | 12px | 400 | 16.0005px | -0.12px |

| Evidence class | Apple status |
|---|---|
| **Official product-use** | SF Pro is the system family for Apple platforms; SF Compact serves watchOS; SF Mono serves coding environments such as Xcode |
| **Live surface-use** | SF Pro Text and SF Pro Display are loaded and visibly used across inspected Apple marketing, Store, and HIG web surfaces |
| **Official distributed asset** | Apple provides SF Pro, SF Compact, SF Mono, New York, script extensions, and design resources under Apple-specific licenses |
| **Declared-only** | SF Mono was declared on the inspected HIG website but not observed as visible page chrome |
| Evidence boundary | A universal mapping from Apple web roles to every native platform context; platform APIs remain the authority |

<!-- design-md:section components-states -->
## 4. Components & States

### Component Stylings

### apple.com Marketing Primary
- Background: `#0071e3`
- Text: `#ffffff`
- Radius: 980px
- Padding: 11px 21px
- Height: 44px
- Font: 17px / 400 / SF Pro Text
- States: default captured; hover not retained
- Use: large homepage marketing CTA

### apple.com Marketing Outline
- Background: transparent
- Text: `#0066cc`
- Border: 1px solid `#0066cc`
- Radius: 980px
- Padding: 11px 21px
- Height: 44px
- Font: 17px / 400 / SF Pro Text
- States: default captured; hover not retained
- Use: secondary marketing CTA paired with a filled action

### apple.com Marketing Compact
- Background: `#0071e3`
- Text: `#ffffff`
- Radius: 980px
- Padding: 8px 15px
- Height: 36px
- Font: 14px / 400 / SF Pro Text
- States: default captured; hover not retained
- Use: compact product-tile CTA on the current homepage

### Apple Store Product Gallery Tab
- Text: `#1d1d1f`
- Height: 53px in the captured product thumbnail navigation
- Font: 17px / 400 / SF Pro Text
- States: selected and unselected thumbnails
- Use: choosing a product image on an Apple Store product page

### HIG Documentation Reference Card
- Background: `#ffffff`
- Radius: 18px
- States: default documentation card; hover not retained
- Use: HIG component-index navigation only. Do not present this as a native iOS or macOS card token.

### States

| Component | Verified state evidence |
|---|---|
| Marketing buttons | default geometry captured; hover/pressed/disabled not retained |
| Product gallery tab | selected and unselected thumbnail states |
| HIG reference card | default documentation state only |

<!-- design-md:section layout-platforms -->
## 5. Layout & Platforms

### Layout Principles

- Public marketing sections use full-width composition and centered content; store pages use denser product-detail layout.
- Exact spacing promoted here is component-local: 8px and 15px for compact action padding; 11px and 21px for the large pill; 20px as a recurrent content cluster.
- Avoid treating every sampled margin from Apple page composition as a universal system token.

### Responsive Behavior

The homepage and store surface are responsive, but this pass does not promote universal breakpoints. Preserve control geometry at the inspected desktop surface, then use platform-specific HIG guidance when targeting iOS, macOS, watchOS, tvOS, or visionOS rather than scaling web values mechanically.

<!-- design-md:section content-locales -->
## 6. Content & Locales

### Voice & Tone

Apple’s current design guidance treats language as part of simplicity and agency. Labels should be concise, recognizable, and directly tied to what happens next; feedback should keep people informed and in control. Product pages tend to make one capability the subject of a headline and use short actions, while platform guidance explains the rationale and constraints without promotional filler.

Clarity does not mean stripping away character. Apple’s current principles pair **Simplicity** with **Craft** and **Delight**: remove what is unnecessary, care about every detail, and create defining moments that support the task rather than interrupt it. Privacy, safety, permissions, and destructive actions require transparent language and recoverability, not euphemism.

<!-- design-md:section governance -->
## 7. Governance

### Agent Prompt Guide

- “Create a large Apple web CTA with `#0071e3`, white text, 44px height, 980px radius, 11px 21px padding, and SF Pro Text 17px/400.”
- “Pair it with an outline action using transparent background and `#0066cc` text/border.”
- “For a compact homepage tile, use the separately verified 36px / 8px 15px variant.”
- “When building a native app, treat this web reference as inspiration and consult the relevant platform HIG instead of copying web geometry.”

<!-- design-md:claim authority kind=evidence-backed-reconstruction lang=en -->
### Authority

This document is an evidence-backed reconstruction, not authority for an unrelated target project.
<!-- design-md:claim-end -->

<!-- design-md:claim application-priority order=prompt-fact,repository-fact,system-contract,reference-inspiration lang=en -->
### Application priority

1. Direct user instructions for the requested scope.
2. Repository facts.
3. This system contract.
4. Reference inspiration.
<!-- design-md:claim-end -->

<!-- design-md:claim unknowns policy=absent-at-smallest-unresolved-boundary lang=en -->
### Unknowns

Omit only the smallest unresolved value or group. Do not replace it with a plausible default.
<!-- design-md:claim-end -->

<!-- design-md:claim changes policy=review-record-validate-before-adoption lang=en -->
### Changes

Record, review, and validate changes before adoption.
<!-- design-md:claim-end -->

---
name: Nyayrithm
description: One courtroom, two times of day. Light "in session" is the default; dark "after hours" is the working-late counterpart.
colors:
  # Values below are the DARK ("after hours") theme. The LIGHT ("in session")
  # theme swaps ground/text/hairline only; brass and ember are byte-identical in
  # both. Light: ground #F2F3F5, raised #FBFBFC, text #191D25, hairline
  # rgba(18,22,32,0.11), brass-text #8A5A22, ember-text #C4491C.
  ink: "#0B0E14"
  ink-raised: "#10141C"
  ink-higher: "#161C27"
  bone: "#ECE3D2"
  brass: "#C88A4A"
  brass-lit: "#E8B676"
  oxblood: "#6E1F2A"
  oxblood-bright: "#C0453C"
  ember: "#FF7A3D"
  muted-foreground: "#9A9384"
  hairline: "rgba(236,227,210,0.10)"
  prov-cited: "#C88A4A"
  prov-inferred: "#6E7688"
  prov-disputed: "#C0453C"
  role-judge: "#D69B58"
  role-prosecutor: "#C0453C"
  role-defense: "#5B7FA6"
  role-plaintiff: "#8E7BB0"
  role-accused: "#B26E8A"
  role-witness: "#6E9E86"
  role-investigator: "#C77F4A"
  role-expert-witness: "#5E93A0"
  role-custom: "#8A8578"
typography:
  display:
    fontFamily: "Spectral, Iowan Old Style, Georgia, serif"
    fontSize: "clamp(2.7rem, 6vw, 4.9rem)"
    fontWeight: 500
    lineHeight: 0.98
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Spectral, Iowan Old Style, Georgia, serif"
    fontSize: "clamp(1.9rem, 3.5vw, 2.9rem)"
    fontWeight: 500
    lineHeight: 1.1
  title:
    fontFamily: "Spectral, Iowan Old Style, Georgia, serif"
    fontSize: "1.15rem"
    fontWeight: 500
    lineHeight: 1.25
  body:
    fontFamily: "Libre Franklin, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: "0.68rem"
    fontWeight: 400
    letterSpacing: "0.06em"
rounded:
  sm: "2px"
  md: "3px"
  lg: "6px"
spacing:
  hairline: "1px"
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "28px"
  section: "clamp(5rem, 10vw, 7rem)"
components:
  button-primary:
    backgroundColor: "{colors.brass}"
    textColor: "#12100A"
    rounded: "{rounded.md}"
    padding: "10px 16px"
  button-primary-hover:
    backgroundColor: "{colors.brass-lit}"
  button-ember:
    backgroundColor: "{colors.ember}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "12px 24px"
  button-record:
    backgroundColor: "transparent"
    textColor: "{colors.muted-foreground}"
    rounded: "{rounded.md}"
    typography: "{typography.label}"
    padding: "12px 20px"
  input:
    backgroundColor: "{colors.ink-raised}"
    textColor: "{colors.bone}"
    rounded: "{rounded.sm}"
    padding: "8px 12px"
    height: "40px"
  card:
    backgroundColor: "{colors.ink-raised}"
    textColor: "{colors.bone}"
    rounded: "{rounded.lg}"
    padding: "20px"
  badge:
    backgroundColor: "rgba(200,138,74,0.10)"
    textColor: "{colors.brass}"
    rounded: "{rounded.sm}"
    padding: "2px 6px"
    typography: "{typography.label}"
---

# Design System: Nyayrithm

## Overview

**Creative North Star: "The Night Court / The Court in Session"**

The product is a courtroom, and the interface is that room at two times of the working day. **Light ("The court, in session")** is the default: cool institutional paper (`#F2F3F5`, never warm cream), north-window daylight, the printed page. **Dark ("The court, after hours")** is the counterpart: the litigator working late, the proceeding they convened the only light on. The visitor picks; the choice is remembered, and the tab title follows it (`Nyayrithm: The court, in session.` / `... after hours.`). The server-rendered `<title>` stays a single search-legible string; the poetic line is a hydrated flavour touch and never changes the indexable metadata.

Brass (`#C88A4A`) and ember (`#FF7A3D`) are byte-identical in both themes; only the room changes. Where brass or ember would fail WCAG AA as small text on the light ground, a darker same-hue shade is used for the text (`--brass-text`, `--ember-text`) while the fill stays the brand value. What is LIVE is struck forward with a **solid 2px ember edge and a full-strength read, never a glow or bloom**. Everything the system knows is spoken on the record, line-numbered, and traceable back to the passage it came from. The visual world is built from three real artifacts of litigation: the printed law report (Spectral serif carries any voice on the record), the stenographic transcript (a hanging line number in the margin of every turn), and the chain-of-custody tag (a hairline rule down the left of each claim, colored for whether it is cited, inferred, or disputed).

Depth is tonal, never cast. Surfaces separate by stepping through three near-black navy values and by 1px bone-tinted hairlines; there are no drop shadows in the product except a single deep ambient one reserved for things that float above the page (dialogs, the transcript panel, popovers). Glass appears in exactly one place: the fixed nav and the simulation header, the "podium edge." One warm radial pool of brass light sits behind hero and closing moments and behind empty states, the pool of light on the bench.

Color is disciplined to the point of severity. Brass is the institutional accent, the seal and the bench light. Ember (`#FF7A3D`) is load-bearing and rationed: it marks only what is **live** right now, the turn currently being spoken, the primary call to action, an active agent. Nothing decorative is ever ember. Oxblood carries contest and error. Eight legal roles each own one reserved hue and one sigil letter, applied identically in the graph, the transcript, and setup.

**Key Characteristics:**
- Two themes, one world: light "in session" (cool paper, default) and dark "after hours". Brass and ember unchanged across both. Every surface passes WCAG AA in both.
- Spectral serif for anything on the record; Libre Franklin for the room; JetBrains Mono for line numbers, timestamps, citations.
- Flat tonal layering and 1px hairlines; shadows only for floating surfaces; glass only at the nav edge.
- Ember means live and nothing else, and it is a solid edge, never a glow.
- Sharp corners (2 to 6px). No pills, no cards-as-scaffold.
- Provenance is visible in the margin, not hidden in a chip.
- Mono uppercase-tracked labels are rationed to where they carry data (line numbers, timestamps, provenance words). No eyebrow above a section heading.
- The reveal on scroll is CSS `animation-timeline: view()`: content is visible by default and the motion can never leave a section hidden.

## Colors

A two-temperature palette: cold near-black navy for structure, warm brass and bone for everything that carries meaning, with ember held in reserve.

### Primary
- **Brass** (`#C88A4A`): the institutional accent. Filled primary buttons, the active-nav tick, section rules on hover, `cited` provenance, focus rings, links inside prose. Its lit form **Brass Lit** (`#E8B676`) is the hover state and the hot center of the bench-light gradient.
- **Ember** (`#FF7A3D`): reserved for what is **live**. The turn currently being spoken (struck forward with an `-2px 0 0` ember edge and a soft glow), the top-of-funnel call to action ("Convene a proceeding"), an actively speaking agent, an "on the record" indicator. Never a border, never a fill on anything at rest, never decoration.

### Secondary
- **Oxblood** (`#6E1F2A`) and **Oxblood Bright** (`#C0453C`): contest and failure. `disputed` provenance, destructive buttons (outline only), error text and error banners, the prosecutor's role hue, "mistrial" status.

### Neutral
- **Ink** (`#0B0E14`): the page ground everywhere. The scene.
- **Ink Raised** (`#10141C`): cards, panels, the sidebar, input fields, the transcript surface.
- **Ink Higher** (`#161C27`): the active tab, nested raised surfaces.
- **Bone** (`#ECE3D2`): primary type and headings. Never pure white.
- **Muted foreground** (`~#9A9384`, `hsl(38 10% 62%)`): secondary type, warm-tinted, never a flat gray.
- **Hairline** (`rgba(236,227,210,0.10)`, strong form `0.16`): every divider. Borders are 1px; a heavier or colored border is a lapse.

### Tertiary (role spectrum)
Eight fixed hues, one per legal role, each used at ~10% as a chip fill with a 25% border and full strength for the sigil glyph: judge `#D69B58`, prosecutor `#C0453C`, defense `#5B7FA6`, plaintiff `#8E7BB0`, accused `#B26E8A`, witness `#6E9E86`, investigator `#C77F4A`, expert witness `#5E93A0`, custom `#8A8578`.

### Named Rules
**The Ember Rule.** Ember is the color of *now*. It appears on the single live turn, the single primary CTA, and live indicators, and nowhere else. If two ember things are visible in one region, one of them is wrong.

**The Hairline Rule.** Dividers are 1px, bone at 10% alpha. There is no 2px border, no colored `border-left`, no card outline heavier than a hairline. Grouping is done with tonal steps and space.

**The Provenance Rule.** Every agent claim shows its standing in the left margin, not in a trailing chip: a solid brass rule for `cited` (tied to an openable passage), a dashed cool-gray rule for `inferred` (on the record, not yet accepted), a solid oxblood rule for `disputed`.

## Typography

**Display / record font:** Spectral (with Iowan Old Style, Georgia). A screen-tuned transitional serif with the weight of a printed law report. Carries every headline and any agent speaking on the record.
**Body / interface font:** Libre Franklin (with system sans). A Franklin-lineage grotesque, the workhorse of American legal and newspaper setting. Everything the interface says about itself.
**Mono font:** JetBrains Mono. Line numbers, timestamps, citation markers, provenance labels, docket metadata, code in the docs.

**Character:** authoritative and printed, not decorative. The serif never appears in italic-as-flourish; emphasis inside a heading is weight, not a face swap.

### Hierarchy
- **Display** (Spectral 500, `clamp(2.7rem, 6vw, 4.9rem)`, line-height 0.98, tracking -0.02em): the hero headline and the closing "All rise." Two lines maximum.
- **Headline** (Spectral 500, `clamp(1.9rem, 3.5vw, 2.9rem)`, line-height 1.1): section titles.
- **Title** (Spectral 500, ~1.05 to 1.2rem): card titles, dialog titles, agent names in the transcript, roll-call role names.
- **Body** (Libre Franklin 400, 0.9 to 1rem, line-height ~1.65, measure 60 to 70ch): all prose and UI copy. Secondary body drops to `foreground/55`, tinted from the ground, never gray.
- **Label** (JetBrains Mono 400, 0.6 to 0.72rem, tracking 0.06 to 0.2em, often uppercase): line numbers, timestamps, provenance tags, docket metadata, section kickers where one is genuinely needed.

### Named Rules
**The On-the-Record Rule.** If a sentence is something an agent said in a proceeding, it is set in Spectral. If it is the interface talking, it is Libre Franklin. If it is a number, a stamp, or a citation, it is JetBrains Mono.

## Layout

A single centered column, `max-w-6xl` (72rem) for marketing and docs, `max-w-4xl` / `max-w-2xl` for operate views, `px-5` to `px-6` gutters. Marketing sections use `py-20` on mobile stepping to `py-28` at `sm`, each opened by a top hairline. Operate views are denser: `py-8` page padding, tight `divide-y` hairline lists instead of card grids.

The app shell is a fixed 15rem sidebar (`w-60`, hairline right edge, tonal `ink-raised/70`) plus a 4rem top bar and a scrolling main. The simulation view is a full-height flex column: a glass "podium" header, then a two-pane courtroom (a 15rem agent rail plus the scrolling record) or the full-bleed spawn graph.

Rhythm: tight within a group (`gap-1` to `gap-2`), generous between groups, and always more space above a heading than below it. Long lists (roles, evidence, past proceedings, dockets) are hairline-divided rows, never card grids.

Breakpoints follow Tailwind defaults (`sm` 640, `md` 768, `lg` 1024, `xl` 1280). Multi-column marketing layouts collapse to a single column below `md`; the roll-call list collapses from a 3-cell grid to a stacked block.

## Elevation & Depth

Tonal, not cast. Hierarchy is conveyed by stepping through `ink` to `ink-raised` to `ink-higher` and by 1px hairlines. The product UI has **no resting shadows**.

### Shadow Vocabulary
- **`shadow-chamber`** (`0 24px 70px -24px rgba(0,0,0,0.75)`): the only deep shadow. Reserved for surfaces that genuinely float above the page: dialogs, popovers, the hero transcript panel, the auth card.
- **`shadow-chamber-sm`** (`0 12px 34px -16px rgba(0,0,0,0.6)`): a lighter version for smaller floating fragments (the provenance mini-panel).
- **Struck glow** (`-2px 0 0 0 #FF7A3D, 0 0 24px -6px rgba(255,122,61,0.4)`): not elevation, but state. The live turn and the active agent carry this ember edge.

### Named Rules
**The Flat-at-Rest Rule.** A surface sitting in the page has a hairline and a tonal step, never a shadow. A shadow means the surface is above the page and can be dismissed.

## Shapes

Sharp. Base radius is 3px (`--radius`), a stamped-form corner; small elements go to 2px, cards and panels to 6px. There are **no pills**: status is a small square-cornered tag, not a rounded capsule, and there are no decorative rounded rectangles standing in for content. Role sigils are 4 to 6px squares holding a single mono glyph. The custody line and the seam are 1px rules, the custody line optionally dashed for `inferred`. The citation "seam" is a 4px-dashed brass underline sitting a line below the text, the visible stitch from a claim to its source.

## Components

### Buttons
- **Shape:** 3px radius (`rounded-md`). Tactile `:active` press with `translate-y-px`.
- **Primary:** brass fill, near-black text, `hover:` brass-lit. Used for confirming actions inside the app ("Open case", "Call to order").
- **Ember:** ember fill, ink text, `hover:#ff8f5c`. The top-of-funnel CTA only ("Convene a proceeding"). One per view.
- **Outline:** transparent, hairline border, `hover:` brass border at 40%. Secondary actions.
- **Destructive:** transparent with an oxblood-bright border and text, `hover:` a faint oxblood wash. Never a red fill.
- **Record:** mono, uppercase, hairline border, understated. For "read more" style links out ("Read the docs").
- **Ghost:** text only, `foreground/60` to `foreground` on hover.

### Chips / tags (Badge)
- **Style:** 2px radius, 1px border, mono, uppercase, `0.68rem`. Fill at ~10% of the hue, border at ~25 to 30%.
- **Variants:** `default` brass, `success` witness-sage, `warning` brass, `info` defense-blue, `destructive` oxblood, `live` ember (the only place a badge uses ember, for "in session"), `muted` neutral.

### Cards / containers
- **Corner:** 6px (`rounded-lg`).
- **Background:** `ink-raised`; a hairline border; `text-card-foreground`.
- **Shadow:** none at rest (see Elevation).
- **Padding:** 20px (`p-5`).
- Card titles are Spectral. Cards are used sparingly: for genuinely grouped panels (the create form, the "convene" panel, empty states), never as the default page scaffold.

### Inputs / fields
- **Style:** `ink-raised/60` fill, a 1px bottom hairline border (top and sides are borderless), 2px radius, caret in ember.
- **Focus:** the bottom border becomes solid brass and the fill goes fully `ink-raised`. No glow ring on inputs (the ring is for buttons and links).
- **Labels** sit above the field (Libre Franklin, `0.78rem`, `foreground/60`); errors sit below in oxblood-bright, `0.72rem`.

### Navigation
- **Marketing nav / simulation header:** the "podium edge" — `rgba(11,14,20,0.86)` with `backdrop-blur(16px)` and a hairline-strong bottom border. Fixed. 4rem tall. Wordmark in Spectral small-caps, links in Libre Franklin `foreground/55`, one ember CTA. Single line at every width; below `md` the anchor links drop and only Docs / Sign in / CTA remain.
- **App sidebar:** flat `ink-raised/70`, mono section kickers (`CHAMBERS`, `SYSTEM`), nav items with a 2px brass tick on the left when active (no filled pill), lucide icons at `strokeWidth 1.75`.
- **Tabs:** a small `ink-raised` track; the active tab is `ink-higher` with a 2px brass underline drawn by an inset box-shadow.

### The transcript / record (signature component)
The core of the product and of the landing hero. A line is a CSS grid: a 2.5rem right-aligned mono line number, then the claim. The claim sits in a `custody-line` container whose `::before` is the 1px provenance rule (solid brass `cited`, dashed cool-gray `inferred`, solid oxblood `disputed`). The line currently being spoken is `.struck` (bone text, ember left edge, `ember-arrive` glow animation, a blinking ember `streaming-cursor`); completed lines are `.afterglow` (text at 62%). Each line leads with the role sigil chip and the agent name in Spectral, a role tag, and a right-aligned mono provenance word that appears on hover. Citations render inline as a `.seam`: a mono filename with a dashed brass underline that opens a popover onto the source passage.

### Agent graph node
A 3px-radius node, `role-hue` at 12% fill, a 1px border (solid for predefined agents, **dashed** for AI-spawned), the sigil chip plus a mono role label plus the agent name in Spectral. Dismissed or suspended agents drop to 40% opacity and a flat `ink-raised` fill (the "ghost" state). The active agent carries the ember struck glow. "spawned mid-proceeding" is stated in mono beneath spawned nodes.

## Do's and Don'ts

### Do:
- **Do** reserve ember for what is live: the current turn, the primary CTA, an active agent, a live status. One ember element per region.
- **Do** show provenance in the left margin with the custody-line rule (solid brass `cited`, dashed gray `inferred`, solid oxblood `disputed`), never as a trailing colored chip.
- **Do** set anything an agent says in Spectral, the interface's own copy in Libre Franklin, and every number, stamp, timestamp, or citation in JetBrains Mono.
- **Do** separate surfaces with a 1px bone-10% hairline and a tonal navy step; keep `shadow-chamber` for things that actually float (dialogs, popovers, the transcript panel).
- **Do** compose empty and absent states: "Nothing is on the record yet", "The docket is empty", an un-spawned agent as a designed ghost, never a bare blank.
- **Do** use `strokeWidth={1.75}` (or `1.5` for large glyphs) on lucide icons; give each legal role its one reserved hue and sigil everywhere it appears.
- **Do** keep corners sharp (2 to 6px) and use hairline-divided rows for any list over five items.

### Don't:
- **Don't** ship one theme only. Both light ("in session") and dark ("after hours") are first-class; test every surface in both and keep WCAG AA in both.
- **Don't** render ember as a glow, bloom, or zero-offset colored shadow. Live state is a solid 2px ember edge plus a full-strength read.
- **Don't** put a mono uppercase-tracked eyebrow above a section heading, or use the AI-default warm-cream light palette (`#f5f1ea` family) for the light theme.
- **Don't** use ember as a border, a resting fill, or decoration; don't put two primary CTAs on a page.
- **Don't** add a drop shadow to a surface that sits in the page, or a border heavier than 1px, or a colored `border-left` on a card or callout.
- **Don't** use pills or rounded capsules; don't nest cards, or use same-size icon-heading-text cards as the page scaffold.
- **Don't** introduce a fourth typeface or set the serif in italic for visual interest; emphasis is weight.
- **Don't** use pure `#000` or pure `#fff`; secondary text is tinted from the ground (`foreground/55`), never a flat gray.
- **Don't** fabricate adoption: no customer logos, testimonials, benchmarks, or "trusted by" until real ones exist.
- **Don't** revive the previous world (amber `#f59e0b`, Playfair/Cinzel, WebGL shader background, MetalButton, "All Rise" over a globe); it was replaced deliberately.

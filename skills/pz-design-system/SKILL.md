---
name: pz-design-system
description: Generate a complete design system (design.md, design-guidelines.md, design-components.md) from any reference materials — images, PDFs, links, or descriptions.
disable-model-invocation: true
---

# Design System Generator

Analyze the user's provided design references (images, screenshots, PDFs, links, text descriptions, or existing code) and generate a comprehensive 3-file design system documentation.

## Inputs

Accept ANY combination of:

- **Images**: Screenshots of UIs, mockups, design tool exports
- **PDFs**: Brand guidelines, style guides, design specs
- **Links**: URLs to design system documentation, component libraries, or live websites
- **Text descriptions**: Written descriptions of the design language
- **Existing code**: CSS files, theme configs, Tailwind configs, design tokens

If the user provides a link, use WebFetch to retrieve the content. If they provide a file path, read the file.

## Output

Generate exactly 3 markdown files in the user's working directory (or a specified path):

1. **design.md** — Token Reference
2. **design-guidelines.md** — Accessibility & Do's/Don'ts
3. **design-components.md** — Component Specs

## File Specifications

### design.md — Token Reference

```markdown
# [System Name] Design System — Token Reference

> Always read this file first. For component specs see [design-components.md](design-components.md). For accessibility and do's/don'ts see [design-guidelines.md](design-guidelines.md).

[1-2 sentence intro: design language, core architecture, primary typeface, base spacing unit, platform coverage]
```

**Required sections:**

#### Colors

Group by semantic role using H3 subsections (e.g., ### Accent — Primary, ### Surface & Neutral, ### Semantic/Status).

| Role       | Hex       | Usage                            |
| ---------- | --------- | -------------------------------- |
| primary    | `#6442d6` | High-emphasis fills, text, icons |
| on-primary | `#ffffff` | Text/icons on primary            |

Include light/dark hex where detectable.

#### Typography

Default font family + fallback chain.

| Style         | Size | Weight | Line Height | Spacing |
| ------------- | ---- | ------ | ----------- | ------- |
| Display Large | 57sp | 400    | 64sp        | -0.25sp |
| Body Medium   | 14sp | 400    | 20sp        | 0.25sp  |

List all scale levels (Display, Headline, Title, Body, Label or equivalent).

#### Shape

| Token  | Radius | Components           |
| ------ | ------ | -------------------- |
| Small  | 8dp    | Chips, snackbars     |
| Medium | 12dp   | Cards                |
| Full   | 50%    | Buttons, search bars |

#### Elevation

| Level | dp  | CSS Shadow                                              | Usage        |
| ----- | --- | ------------------------------------------------------- | ------------ |
| 0     | 0   | none                                                    | Base surface |
| 1     | 1   | `0 1px 2px rgb(0 0 0/.3), 0 1px 3px 1px rgb(0 0 0/.15)` | Cards        |

#### Interaction States

| State    | Layer Opacity              | Notes          |
| -------- | -------------------------- | -------------- |
| Enabled  | 0%                         | Resting        |
| Hover    | 8%                         | Cursor over    |
| Focus    | 10%                        | Keyboard focus |
| Pressed  | 10%                        | Tap/click      |
| Disabled | 38% content, 12% container | Inoperable     |

#### Layout

| Class    | Width      | Panes | Navigation         |
| -------- | ---------- | ----- | ------------------ |
| Compact  | < 600dp    | 1     | Nav bar            |
| Medium   | 600–839dp  | 1–2   | Nav rail or bar    |
| Expanded | 840–1199dp | 1–2   | Nav rail or drawer |

#### Motion

Easing curves (CSS cubic-bezier values), duration tokens (short/medium/long), transition types.

#### Icons

Icon system specs: style, sizes, grid, stroke weight. Omit if not detectable.

#### Design Tokens

Naming convention format (e.g., `md.sys.color.primary`).

---

### design-guidelines.md — Accessibility & Do's/Don'ts

```markdown
# [System Name] Guidelines — Accessibility & Do's/Don'ts

> See [design.md](design.md) for token values. See [design-components.md](design-components.md) for component specs.
```

**Required sections:**

#### Accessibility

- **Contrast Requirements**: Table with Requirement | Ratio, then Component | 3:1 Against
- **Touch Targets**: Minimum sizes, spacing rules, density constraints
- **Keyboard Navigation**: Table with Key | Action
- **Assistive Technology**: Screen reader rules, labels, roles

#### Gestures

Table with Gesture | Use (Tap, Double tap, Long press, Scroll, Swipe, Drag, Pinch).

#### Content Design

Writing rules: tone, capitalization, line length, label constraints.

#### Do's and Don'ts

Organize by category with H3 subsections: Color, Shape, Elevation, Interaction, Layout, Typography, Motion, Components.

Format:

- **Do** use primary for the single most important action
- **Don't** apply primary fill to multiple buttons in a group

---

### design-components.md — Component Specs

```markdown
# [System Name] Components

> Full specifications for all [N] components. Grouped by workflow.
> For tokens see [design.md](design.md). For rules & accessibility see [design-guidelines.md](design-guidelines.md).
```

**Find ALL components** detectable from the provided references. Do not limit to a fixed list.

**Organize by workflow category using H2 headings:**

- ## Actions
- ## Input
- ## Navigation
- ## Containment
- ## Data Display
- ## Feedback

**Each component as an H3 section:**

```markdown
### Button

**Types:** Filled (primary) > Tonal (secondary) > Elevated > Outlined > Text.
Height 40dp. Target 48dp. Label: 14sp/500. Sentence case.

| Property     | Value                                 |
| ------------ | ------------------------------------- |
| Contrast     | 4.5:1 text, 3:1 icons/borders         |
| States       | Rest, Hover, Pressed, Focus, Disabled |
| Touch target | 48x48dp min                           |

**Do:** Use sentence case; keep labels concise (1-3 words).
**Don't:** Use "Click here"; end with punctuation.

---
```

**Typical components to cover:**

- **Actions:** Button, Icon Button, FAB, Toolbar, Link
- **Input:** Text Field, Checkbox, Radio, Switch, Slider, Dropdown/Select, Combobox, Picker, Textarea
- **Navigation:** Navigation Bar/Rail/Drawer, Tabs, Breadcrumb, Menu, Search, App Bar
- **Containment:** Card, Dialog, Bottom Sheet, Drawer, Popover, Accordion, Divider
- **Data Display:** Avatar, Badge, List, Carousel, Icon, Image, Tag/Chip, Skeleton, Tooltip
- **Feedback:** Progress Indicator, Spinner, Snackbar/Toast, Message Bar

## General Rules

- Be specific: measurements in dp/sp/px, hex colors, CSS box-shadow values
- If a value cannot be determined from references, make a reasonable inference based on the design language and note it with "(inferred)"
- Use tables over prose — keep scannable
- Aim for 150–400 lines per file
- Each file must cross-reference the other two in its opening blockquote
- Separate components with horizontal rules (`---`)
- Use consistent markdown formatting throughout

## Workflow

1. Gather all reference materials from the user (read files, fetch URLs)
2. Analyze the design language: identify colors, typography, spacing patterns, component inventory
3. Generate all 3 files
4. Write each file to the specified directory
5. Summarize what was generated: system name, token count, component count

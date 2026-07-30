# Design Tokens

## Philosophy

UrbanInsight AI follows a modern, clean and AI-first design language.

The interface should feel lightweight, immersive and friendly.

Consistency is more important than visual complexity.

All reusable components must use these tokens whenever possible.

The implemented source of token configuration is:

```text
tailwind.config.ts
```

---

# Border Radius

```text
sm: 12px
md: 16px
lg: 20px
full: 999px
```

Usage

- Buttons → `full`
- Badges → `full`
- Search result actions → `full`
- Cards → `md`
- Panels and page containers → `lg`
- Tooltips → `sm`
- Avatar and circular controls → `full`

Pill-shaped buttons are mandatory.

Cards and panels continue to use their own radius tokens.

MapLibre native controls may retain their compact native control radius.

---

# Spacing

```text
xs: 4px
sm: 8px
md: 16px
lg: 24px
xl: 32px
```

Use an 8pt spacing system whenever possible.

Current shell spacing

- Header height → 72px
- Maximum content width → 1600px
- Main panel gap → 24px
- Main content padding → 32px
- Analysis section spacing → 32px

---

# Shadows

```text
card: 0 8px 24px rgba(15,23,42,.06)
panel: 0 12px 32px rgba(15,23,42,.08)
```

Avoid heavy shadows.

Use soft elevation only.

The map Home control uses a smaller native-map shadow:

```text
0 1px 4px rgba(0,0,0,.18)
```

---

# Colors

Background

```text
#F8FAFC
```

Surface

```text
#FFFFFF
```

Primary

```text
#3B82F6
```

Primary Hover

```text
#2563EB
```

Success

```text
#22C55E
```

Warning

```text
#F59E0B
```

Danger

```text
#EF4444
```

Border

```text
#E5E7EB
```

Text Primary

```text
#0F172A
```

Text Secondary

```text
#64748B
```

Map Highlight

```text
#60A5FA
```

Map Glow

```text
rgba(96,165,250,.28)
```

Supporting Tailwind color utilities may use restrained blue, emerald, amber and red tints for status backgrounds.

No dark theme is currently implemented.

---

# Typography

Font

```text
Inter
```

Fallback

```text
system-ui
sans-serif
```

Title

```text
32px
line-height: 1.15
weight: 700
```

Heading

```text
24px
line-height: 1.25
weight: 600
```

Body

```text
16px
line-height: 1.6
weight: 400
```

Caption

```text
14px
line-height: 1.45
weight: 400
```

Compact component titles may use 18px with weight 600 or 700.

Long explanatory paragraphs should use a maximum width near 70 characters.

---

# Animation

Duration

```text
fast: 150ms
normal: 250ms
slow: 400ms
```

Easing

```text
ease-out
```

Implemented keyframes

- `panel-in` → fade and translate upward over 250ms
- `shimmer` → 1.5 second loading background loop

Map camera transitions use 300ms.

Cards may lift by 2px on hover.

Buttons may lift by 2px on hover.

Avoid bounce animations and excessive scaling.

AI responses do not currently stream or use typing animation.

---

# Components

Buttons

- Minimum height 44px
- Pill radius
- Content-based width by default
- Primary, secondary and ghost variants
- Visible keyboard focus ring
- Disabled opacity and pointer blocking
- Icon-only size is 44px square

Cards

- White surface
- Radius `md`
- Padding 24px
- Card shadow
- Soft hover lift

Panels

- Radius `lg`
- Panel shadow
- Sticky positioning when necessary
- AI Panel may use translucent white and backdrop blur

Inputs

- Minimum height 44px
- Radius `md`
- Border token
- Card shadow
- Primary focus ring

Badges

- Pill radius
- Blue tint by default
- Status-specific tint where necessary

Charts

- Recharts implementation
- 300px stable chart height
- Minimal grid
- Primary blue and secondary mint
- 400ms first-render animation

Map

- MapLibre GL JS
- Light gray background
- Blue borough fill and selection
- Soft hover glow
- 300ms fit and reset transition
- Compact translucent guidance overlay

---

# Responsive

Breakpoints

```text
sm: 640px
md: 768px
lg: 1024px
xl: 1280px
```

Desktop

- Map and AI Panel use a 7:3 grid
- AI Panel has a minimum column width of 340px
- Analysis cards expand into multi-column grids

Below `lg`

- Map and AI Panel stack vertically
- The map retains a minimum height of 640px
- Analysis header actions wrap vertically

Below `md`

- Dimension cards stack
- AI driver cards stack
- Insight cards stack

Below `sm`

- Indicator cards stack
- Report actions stack

The current implementation does not use a mobile bottom sheet.

The minimum supported document width is 320px.

---
paths:
  - "**/*.css"
  - "**/*.scss"
---

# CSS Discipline

Loads when you touch a stylesheet. This is method, not a design system: it assumes your project has design tokens and components, and keeps you using them instead of hardcoding around them. Read "tokens" as whatever your project calls its variables.

## Before Adding Any CSS
1. Search your token or variable file. Does a variable already exist for this color, space, or size?
2. Search your component styles. Does a similar component already exist? Most styling should already live there.
3. Search your utilities. Is there a utility class for this?

If yes to any: use the existing code. Don't recreate it. Duplicate components are the most common source of CSS drift.

## Token Values Only
- Use your design tokens and variables, never hardcoded colors, spacing, or sizes. A raw hex or px value in a component is the tell that a token was skipped.
- One intentional scale. Don't invent one-off values that sit between two existing steps.

## Composition First
- Compose existing primitives and utilities before writing a new class.
- Only add a new class after searching all existing files and finding nothing. Put it in the right component file and give it hover and focus states.

## Anti-Patterns
- No duplicate components. Search first, always.
- No hardcoded colors or spacing. Use variables.
- No inline `style="..."` for color, spacing, or sizing. Use classes. (Runtime custom-property bridges for per-request computed values are the one exception.)
- No `-v2` or `-new` classes. Update the existing class, or discuss first.
- No inline event handlers in markup. Bind in a script.

## States and Motion
- Every interactive element gets a visible `:focus-visible` state.
- Respect `prefers-reduced-motion`: gate or zero out transitions for users who ask for less motion.

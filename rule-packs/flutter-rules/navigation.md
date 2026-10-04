---
paths:
  - "**/*.dart"
---

# Navigation

The examples use GoRouter (the stack this pack is drawn from); the discipline is router-agnostic.

## Route Constants
- Define every route path as a constant in one place. Never hardcode a route string at a call site.

```dart
context.push(AppRoutes.settings); // correct
context.push('/announcements');         // wrong, use the constant
```

## Push vs Switch
- Switch between top-level tabs with `go`; push a screen outside the tab shell with `push`. Be deliberate about which one hides the bottom navigation.

## Sheet vs Full Screen
- Bottom sheet for detail views, forms, pickers, and confirmations.
- Full screen for list views and complex editors.

## Auth Guard
- Gate protected routes with a redirect at the router level, not with a check scattered through each screen. Unauthenticated goes to the login route.

## Deep Links
- Scope your custom URL scheme to the specific callbacks it exists for (an OAuth return, a specific entity), not arbitrary routes.
- Validate every parameter that arrives through a deep link before you act on it. A deep link is untrusted input.

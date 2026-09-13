# Lifetime Journey Calculator — GitHub package

This package contains the current Lifetime Journey Calculator with the approved One-Touch Form Centre visual language applied.

## Upload to GitHub

Upload both files to the calculator's existing GitHub folder:

- `index.html`
- `cbus-theme.css`

Keep the two files in the same folder. The stylesheet is linked with the relative path `cbus-theme.css`.

The existing Supabase authentication guard and `../../index.html` dashboard route are preserved. The calculator should therefore remain two folder levels below the dashboard, matching the current setup.

## What changed

- Bright blue header with green and white title treatment
- Condensed, heavy typography with Hubot Sans and condensed system fallbacks
- Green input and select borders
- Blue section headings and expanded section headers
- Green primary action button
- Consistent white panels, flatter spacing, and desktop-first responsive layout
- Shared `cbus-theme.css` for reuse across related tools

No projection formulas, financial rules, chart calculations, input IDs, event handling, authentication logic, or dashboard routing were changed.

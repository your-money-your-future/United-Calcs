# Lifetime Journey Calculator — GitHub package

This package contains the current Lifetime Journey Calculator with the approved One-Touch Form Centre visual language applied. It uses the same bright blue, hi-vis green, white header treatment, heavy condensed typography, and sharply bordered fields without presenting the calculator as an approved product of any fund.

## Upload to GitHub

Upload both files to the calculator's existing GitHub folder:

- `index.html`
- `shared-theme.css`

Keep the two files in the same folder. The stylesheet is linked with the relative path `shared-theme.css`.

The existing Supabase authentication guard and `../../index.html` dashboard route are preserved. The calculator should therefore remain two folder levels below the dashboard, matching the current setup.

## What changed

- Full-width bright blue header using the reference page's exact `#0639D8` blue and `#32ED67` green
- Green calculator title, white subtitle, and green right-hand header statement
- Condensed, heavy typography with Hubot Sans and condensed system fallbacks
- Green input and select borders
- Bright-blue numbered section boxes with green wording
- Green primary action button
- Consistent white panels, flatter spacing, and desktop-first responsive layout
- Shared, neutrally named `shared-theme.css` for reuse across related tools
- No fund logo and no fund name used as calculator branding

No projection formulas, financial rules, chart calculations, input IDs, event handling, authentication logic, or dashboard routing were changed.

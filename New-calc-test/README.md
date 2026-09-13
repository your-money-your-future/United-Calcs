# Working After 65 Calculator

This is a separate calculator for members aged 65 and over who continue working while maintaining both an accumulation account and one or more retirement-phase income streams.

## GitHub installation

Upload all three files to the new calculator folder in GitHub:

- `index.html`
- `theme.css`
- `investment-returns.js`

Keep them together in the same folder. The existing authentication guard redirects unauthenticated visitors to `../../index.html`, and the visible **Back to Dashboard** link uses the same route. Place the calculator two folder levels below the dashboard, consistent with the current calculator structure.

## Modelled features

- Employment income and employer contributions after age 65
- Salary-funded and personal deductible contribution targets, split automatically between remaining concessional cap space and after-tax contributions
- Estimated take-home pay after tax, Medicare levy and salary-funded contributions—including high contribution targets such as 70%
- Shared non-concessional/bring-forward allowance across redirected salary contributions, outside lump sums and retained excess employer contributions
- Work-test handling for personal deductible contributions from ages 67–74
- Separate accumulation and retirement income-stream balances and returns
- Tax-free retirement-phase investment earnings and pension income assumptions
- Personal transfer-balance cap usage and remaining space
- Multiple scheduled income-stream commencements
- Scheduled additions sourced from outside super or the accumulation account
- Non-concessional annual cap and automatic two- or three-year bring-forward periods
- Starting in year 2 or year 3 of an existing bring-forward arrangement
- Warnings showing the financial year through which a bring-forward restriction continues
- Voluntary contribution cutoff from age 75, while compulsory employer contributions continue
- Statutory pension minimums, fixed/indexed income targets, and percentage withdrawals
- Actual-dollar and today's-dollar chart/table views
- Detailed hover, tap and keyboard-focus popup for every projected year
- Published accumulation and fully retired investment returns held in a separate update file

The model uses fixed 2026–27 caps throughout the projection and explains material omissions or restrictions in the results. Investment return data is current to 31 July 2026 and can be refreshed by replacing the values in `investment-returns.js`; the calculation engine and page do not need to be changed.

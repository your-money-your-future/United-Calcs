# Weekly fund comparison update

The calculator feed is generated from the existing **Weekly Super Returns
Report** project. The PDF is not scraped. The updater reads the report's
canonical JSON and manifest, then refuses to proceed unless the production run:

- is a non-test run with status `sent`;
- contains all 12 configured funds, including explicitly unavailable sources;
- passed report rendering and visual inspection;
- has a PDF checksum matching the visually inspected file; and
- has verified recipient, subject, attachment and Gmail Sent status.

The calculator uses accumulation data only and excludes TTR and retirement
products. Each option uses the longest available annualised return in this order:
10, 7, 5, 3, then 1 year. The option's period, reference date and published basis
are displayed. A fund with no verified source in the weekly run is excluded from
the selector and disclosed as unavailable; stale figures are never presented as
current.

## Monday flow

1. The report project collects at 4:30 am Australia/Brisbane time.
2. It validates, renders, visually checks and emails the report at 5:30 am.
3. Only after the manifest is marked `sent`, prepare the controlled update:

   ```sh
   python scripts/prepare_weekly_fund_comparison_update.py \
     --report-project /path/to/super-returns-monitor \
     --report-date YYYY-MM-DD
   ```

4. The preparer requires a clean `main`, fast-forwards from GitHub, writes a
   validated `fund-performance-data.js` candidate to the system temporary
   directory, and prints its path. The Monday Codex task then uses its connected
   GitHub integration to create an `automation/fund-comparison-YYYY-MM-DD`
   branch, upload that one candidate file, and open a pull request.
5. Merge only after **Validate fund comparison data** passes. Keep branch
   protection on `main` with this check required if the GitHub plan permits it.

## One-time authentication

Connect the GitHub integration in Codex as the repository owner and grant it
permission to create branches, update files and open pull requests in
`your-money-your-future/United-Calcs`. No token belongs in the repository,
generated feed or automation prompt.

## Failure behaviour

Any invalid checksum, incomplete validation, test report, unsent report, dirty
checkout, non-fast-forward main branch, feed validation error, or GitHub failure
stops the process. The calculator remains on the last merged verified dataset.
The workflow never pushes directly to `main` and never auto-merges a PR.

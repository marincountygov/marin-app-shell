# Reports for every MarinOS app: plan

Status: plan, 18 November 2026. Step 3 (the core) is in App Shell 2.3.0; the model as built is in `docs/reports.md`. The first working version is in `marin-budget` (`shared/reports.js`, and the Reports page in `reports/`, which builds a report from Budget, Capital improvement plan and Contracts sections). It is built so its core lifts into this shell without changes.

## Goal

One way to make a report in any MarinOS app. A report is plain data. A shared core turns it into a preview, a copy for Word, a standalone HTML file, Markdown, text, CSV and a saved report file. Apps supply the content; the shell supplies the document and the output.

## What already exists

- `marinContentFormats`, `marinCopyRich`, `marinCopyText`, `marinDownload`, `marinReadText` and `marinUpload` in this shell. Apps must use these for copying, downloading and reading files (the shared-helpers audit checks it).
- Data-driven components (`data-record-list`, `data-key-numbers`, `data-chart`).
- Marin Mentions: `assets/reports/core.js` (model, validation, save and open), `render.js` (document, plain text, standalone HTML) and `ui.js` (the step-by-step builder).

## The report model, version 1

```json
{
  "schema": "1.0",
  "title": "Budget report",
  "prepared": "2026-11-18",
  "filters": "Showing: FY 2026-27 Proposed · All service areas",
  "sections": [
    { "type": "table", "title": "", "head": ["Service area", "FY 2026-27"],
      "rows": [["Public Safety", "$219,132,962"]], "values": [["Public Safety", 219132962]] }
  ],
  "sources": [{ "label": "County of Marin FY 2026-28 Budget Book", "url": "https://…" }]
}
```

- `prepared`, `filters` and `sources` are report fields. They can be left empty, and then nothing is drawn.
- `rows` are the text as shown. `values` is the same table with raw numbers for CSV, and is optional.
- Section types in version 1: `table`. Text, key numbers and list sections follow. An app may register its own types (Mentions: release coverage, coverage list, highlights).
- Every value is escaped by the renderer. Only http, https and mailto links are kept.

## The core (no DOM)

`create`, `validate`, `renderHtml(report, { titleLevel })`, `toText`, `toMarkdown`, `standaloneHtml`, `toJson`, `parseJson`, `csvRows`. It runs in the browser and in Node tests.

## The preview

The report is drawn as a document. The same HTML is what Copy for Word, Download HTML and the Markdown and text formats read, so the preview and the output cannot differ. Download report file saves the JSON; Open a saved report reads it back into the preview.

## Order of work

1. Budget: report model, core and preview in `marin-budget` (done with this plan).
2. Write the model as a spec (`docs/reports.md` here) from what the Budget version settled on.
3. Move the core and the document styles upstream: styles to `marin-ui`, the core and a `marinReports` mount to this shell, then a shell release. **The core is done (2.3.0, `window.marinReports`); the document styles and the preview mount are not.**
4. Mentions: replace `render.js` and the generic part of `core.js` with the shell core. Its stages, draft saving and section types stay in the app.
5. Other apps adopt it when they need a report.

## Decisions made

- The core is built in Budget first and lifted into the shell once the model settles.
- The report file (JSON) and opening a saved report are in the first version, with a `schema` version from the start.
- "Prepared", the filters line and the source line are report fields, on by default, and can be turned off for a report.
- Mentions keeps its builder. Only its renderer and the generic core are replaced.

## Acceptance

- One report object renders the same in Budget and Mentions.
- The preview matches what Copy and Download hold.
- A finished report pastes into Word with headings, bordered tables and links intact (repeat the paste after any change to the renderer).
- The core's tests run in each app that uses it.

## Not in the first version

Saved drafts in the browser, a chart in a report, a PDF, and the stage-by-stage builder in the shell.

# Reports: the report core

`window.marinReports` (App Shell 2.3.0 and later) makes, checks, draws and saves a report. It has no DOM access. The source is `src/reports-core.js`; `scripts/build.py` inlines it into `marinos.js`. The same file runs in Node, and `tests/reports-core.test.js` tests it.

The plan and the order of work are in `docs/reports-plan.md`. This page is the model as built.

## A report is plain data

```json
{
  "schema": "1.0",
  "title": "Comparison of places",
  "prepared": "2026-11-24",
  "filters": "San Rafael, Novato",
  "sections": [
    { "type": "table", "title": "", "head": ["Measure", "San Rafael"],
      "rows": [["Median household income", "$119,000 \u00b1 $8,200"]],
      "values": [["Median household income", { "value": 119000, "margin": 8200 }]] }
  ],
  "sources": [{ "label": "U.S. Census Bureau, American Community Survey 5-year estimates, 2020\u20132024", "url": "https://www.census.gov/programs-surveys/acs" }]
}
```

- `prepared`, `filters` and `sources` can be left empty. Nothing is drawn for an empty one.
- `rows` are the text as shown. `values` is optional: the same table with raw numbers, used for CSV.
- A cell of `values` is a number, text, or an object `{ "value", "margin", "min", "max" }` (each a finite number, each optional). Use it for a figure with a margin of error, or a one-sided bound such as "250,000 or more" (`min`). The CSV gets a column for each part the table uses (`Name`, `Name margin of error`, `Name lower bound`, `Name upper bound`), so nothing is lost. An object with no finite number becomes empty text.
- Section types in this version: `table`, which may carry a `chart` (numbers, a sentence, and a PNG picture the app drew). Other types follow when an app needs them.
- Limits: 12 columns, 500 rows, 10 sections, 10 sources, 4,000,000 characters in a file. Text is cleaned of control characters and cut to length.
- Every value is escaped by the renderer. Only http, https and mailto links are kept.

## Calls

| Call | Returns |
|---|---|
| `create(input)` | `{ report, errors }`: a clean report made from any object, or why it cannot be |
| `renderHtml(report, { titleLevel })` | the document as HTML: what the preview, Copy for Word and Download HTML hold |
| `toText(report)`, `toMarkdown(report)` | the same report as text and as Markdown (a backslash is escaped before a pipe) |
| `standaloneHtml(report)` | a page of its own, with no scripts or outside files |
| `csvRows(report)` | rows for a CSV; with several tables, each starts with its title and a blank row separates them |
| `toJson(report)`, `parseJson(text)` | the report file, and reading one back: `{ report, errors }` |
| `formatDate(iso)`, `pacificToday(date)` | "November 18, 2026", and today in Pacific time |

Use `marinCopyRich`, `marinCopyText` and `marinDownload` to copy and save what these make. The builder screens that choose sections belong to each app.

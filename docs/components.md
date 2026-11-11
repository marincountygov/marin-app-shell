# Component reference

All components render into light DOM. Load `marinos.js` with `defer` and place components in the initial document. Version 1 does not automatically initialize components inserted after the shell-ready event.

## `marin-os-banner`

Renders the MarinOS banner, menu button, local fallback links, and catalog refresh behavior.

```html
<marin-os-banner></marin-os-banner>
```

Optional attributes:

| Attribute | Default | Purpose |
| --- | --- | --- |
| `label` | `ALPHA` | MarinOS release marker. `alpha`, `beta`, or `live` uses the shared status badge; another non-empty value retains the legacy superscript treatment. |
| `catalog-url` | MarinOS `catalog.json` | Catalog source used to refresh the menu. |
| `browse-url` | MarinOS home | Destination for “Browse all in MarinOS.” |

The shell keeps bundled fallback links when the catalog request fails or is unavailable.
Recognized catalog `status` values (`alpha`, `beta`, `live`) render as `.app-status`
badges beside application names. Unknown or missing values render no badge.

## `marin-app-header`

Renders the semantic application header, app identity, mobile menu control, and top navigation.

Only the application name links to `./`; the icon and description remain plain content. This keeps the home navigation clear while allowing the adjacent maturity-status badge to link independently to MarinOS status guidance.

```html
<marin-app-header
  app-name="Marin Unzipper"
  app-description="Decrypt and decompress ZIP files locally in your browser."
></marin-app-header>
```

Attributes:

| Attribute | Required | Default | Purpose |
| --- | --- | --- | --- |
| `app-name` | Yes | `Application` | Visible H1 and application identity. |
| `app-id` | No | None | Stable MarinOS catalog ID used to match the current app locally. Production falls back to URL matching. |
| `app-description` | No | None | Subtitle below the app name. |
| `standard-links` | No | `about updates` | Space- or comma-separated standard links included in the top navigation. |
| `navigation-label` | No | `Application navigation` | Accessible label for the navigation landmark. |
| `menu-label` | No | `Menu` | Mobile menu-button label. |

### Custom icon

Provide an inert template. The shell clones it into the icon container. Copy the complete SVG from the app's vendored Lucide file, including presentation attributes. Reuse that exact geometry in the favicon and MarinOS catalog entry.

```html
<marin-app-header app-name="Example" app-description="Example description.">
  <template data-icon>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>
  </template>
</marin-app-header>
```

The rendered identity layout is `.app-identity > .app-title-row`, with the icon and
title-copy as direct children. Inside the H1, `.app-title__link[href="./"]` is the
application home link. When the app's local `marin.yml` has a recognized
`project.status` (`alpha`, `beta`, or `live`), the shell appends
`.app-status.app-title__status` beside that link and points it to MarinOS `#status`
guidance.

The local manifest is authoritative for the header badge. If it is unavailable or
contains no recognized maturity value, the shell retains the 1.2.0 catalog-matching
behavior as a compatibility fallback. `app-id` is optional but recommended for local
testing of that fallback, where a localhost URL cannot match the deployed catalog URL.

Missing icon templates fall back to the bundled Lucide `layout-grid`. Older
1.0.x templates that omit root presentation attributes receive defaults, but
app-specific icon validation remains the app's responsibility.

Since 1.1.3, a missing root `stroke-width` defaults to `4` for a 48x48 viewBox
and `2` otherwise. The shell never overwrites an explicit root stroke width or
changes the icon's viewBox or path geometry. The same defaults apply to catalog
icons. This is legacy compatibility, not a change to the canonical 24x24 Lucide
standard. See [Icon stroke compatibility](icon-compatibility.md) for upgrade,
late-inserted SVG, and testing details.

### Additional navigation links

Additional links are placed before the standard links. Duplicate `href` values are removed.

```html
<marin-app-header app-name="Example">
  <template data-navigation>
    <a href="#help">Help</a>
  </template>
</marin-app-header>
```

Use application navigation sparingly. The standard top navigation remains About and Updates unless explicitly changed.

## `marin-app-info`

Generates the standard information sections and their required attributes for shell routing, Updates loading, and Security rendering.

```html
<marin-app-info
  app-name="Marin Unzipper"
  repo="marin-unzipper"
  security-src="security.json"
></marin-app-info>
```

Attributes:

| Attribute | Required | Default | Purpose |
| --- | --- | --- | --- |
| `app-name` | Recommended | `This application` | Used in standard explanatory text and Updates labels. |
| `repo` | Required for Updates | None | GitHub repository name or `owner/repo`. |
| `app-id` | No | From `<marin-app-header app-id>`, `<body data-app-id>`, or URL match | MarinOS catalog ID used to find this app's Lighthouse accessibility score in MarinOS's shared `data/lighthouse.json`. |
| `security-src` | No | `security.json` | Same-origin security configuration path. |
| `sections` | No | `about security accessibility updates` | Standard sections to generate, in order. |
| `security-standard-url` | No | MarinOS security standard | Security-standard link. |
| `security-contact-url` | No | `.well-known/security.txt` | Vulnerability reporting link. |

The component will not create a duplicate section if the document already contains the same ID; it writes a console warning instead. That behavior supports a staged migration but should not be used as the final architecture.

### About content

```html
<template data-about>
  <p>Describe the app, its purpose, and its intended users.</p>
</template>
```

The shell adds the About heading and a Related information list.

### Security introduction

```html
<template data-security-intro>
  <p>Application-specific security context.</p>
</template>
```

The shell still owns the reporting, public-security summary, and technical links.

The public-security summary opens with a "Built for" line. It comes from `project.audience` in the app's own `marin.yml` (`staff`, `public`, or `developers`), so there is nothing to write in `security.json`. If `marin.yml` can't be read, the line falls back to the label for the `profile` in `security.json`. A `publicSecurity.profile` string in `security.json` is no longer shown.

### Accessibility content

```html
<template data-accessibility>
  <p>Document application-specific accessibility support and known limitations.</p>
</template>
```

When omitted, the shell provides generic shared-interface and reporting language. Each app remains responsible for testing its own workflow.

### Tech content

```html
<template data-tech>
  <p>Optional application-specific technology context.</p>
</template>
```

The Tech section reads MarinOS's shared `data/tech.json` by catalog id (`app-id` on `<marin-app-info>` or `<marin-app-header>`, `<body data-app-id>`, or URL matching), the same way Accessibility reads its score. It shows, in order: **Languages** (GitHub's Languages API, as percentages), **Dependencies** (GitHub's dependency graph, with the direct/transitive split and a package table read from the stored SPDX file, plus **Bundled components** copied into the repository), **Software bill of materials** (format, version, date, package count, and a link to the SPDX file), **Services used** (outside services the app itself uses, declared in `marin.yml` as `services:` or `services: none`; never credentials), and **AI**.

AI means AI functionality in the deployed application, never tools used to build it. It comes from the `ai:` block in the app's own `marin.yml` and is declared, never inferred. The section prints **Uses AI: Yes**, **Uses AI: No**, or **AI use: Not documented**; a missing declaration is never shown as No. Missing or failed data is shown as "Not available" or "Unable to retrieve", never as zero or none. Vulnerability findings stay in Security.

License ids are shown as the names in `tech.json`'s `licenseNames` (for example "MIT License"). **Marin App Shell** and **Marin UI** in the Bundled components table link to their own Tech details on MarinOS (`#tech-marin-app-shell`, `#tech-marin-ui`). A block nested inside another section can set `data-tech-heading-level` (2-5, default 3) to move its headings down.

Apps do not provide the data. `marin-os` generates it with `scripts/tech.js` and its "Update tech data" workflow.

### Updates introduction

```html
<template data-updates-intro>
  <p>Optional context about the release notes.</p>
</template>
```

## `marin-app-footer`

Renders the local app identity, required information navigation, and the MarinOS platform link.

```html
<marin-app-footer app-name="Marin Unzipper"></marin-app-footer>
```

Every footer includes **About**, **Security**, **Accessibility**, **Tech**, and **Updates**. These are required MarinOS destinations and cannot be removed. The app name is intentionally text, not a link, and the standard links use anchors within the current `index.html`.

Attributes:

| Attribute | Required | Default | Purpose |
| --- | --- | --- | --- |
| `app-name` | Yes | `Application` | Visible app name and navigation label. |
| `links` | No | `about security accessibility updates` | Legacy ordering hint for the standard links. Missing required destinations are appended automatically. |
| `platform-name` | No | `MarinOS` | Platform link label. |
| `platform-url` | No | MarinOS home | Platform link destination. |
| `hide-platform-link` | No | absent | Boolean attribute that omits the separate bottom platform link. The local app name and required information links remain. |

### Additional footer links

Apps with local destinations that belong in the footer can prepend them with a `data-footer-links` template. Only top-level anchors with a non-empty `href` and label are accepted. Duplicate destinations are suppressed, and the four required standard links always follow the app-specific links.

```html
<marin-app-footer app-name="MarinOS" hide-platform-link>
  <template data-footer-links>
    <a href="#projects">Projects</a>
    <a href="#status">Status</a>
  </template>
</marin-app-footer>
```

That renders the local footer navigation in this order: **Projects**, **Status**, **About**, **Security**, **Accessibility**, **Tech**, **Updates**. The separate bottom MarinOS link is omitted because the application is itself the MarinOS platform home. Ordinary applications should keep the default component with no template and no `hide-platform-link`.

## Loading messages

Any "still loading" text, in the shell or in an app, reads `Loading {app name}…` (for example `Loading Marin Reach…`). The shell's own sections use `window.MarinAppShell.loadingMessage()`, which builds that text from the `app-name` on `<marin-app-info>`. Use it, or the same wording, for an app's own loading message rather than naming the data being loaded.

## `marin-app-feedback`

Renders the fixed Feedback control.

```html
<marin-app-feedback></marin-app-feedback>
```

Attributes:

| Attribute | Default | Purpose |
| --- | --- | --- |
| `href` | County feedback form | Feedback destination. |
| `label` | `Feedback` | Visible link text. |
| `target` | `_blank` | Link target. Use an empty value for same-window navigation. |

While the page is scrolled so that the footer is on screen, the control hides itself (`data-over-footer` on the link, `opacity: 0`, no pointer events) so it cannot cover footer links. On a page too short to scroll it stays visible. It stays in the keyboard order and shows itself when it receives focus.

## Collapsible filter panel

A filter column beside a list of results can be hidden at any width. Requirement: `marin-digital-standards/product-design/responsive-design.md`; markup and CSS come from Marin UI 1.28.0 and later (`.search-layout`, `.search-side`, `.search-sidebar`, `.search-results`, `.filter-toggle`).

```html
<form class="search-layout" aria-label="Filter engagements">
  <div class="search-side">
    <button type="button" class="filter-toggle" data-filter-toggle="engagements" aria-controls="filter-panel"></button>
    <aside id="filter-panel" class="search-sidebar" aria-label="Filters">…fields…</aside>
  </div>
  <div class="search-results">…results…</div>
</form>
```

Leave the button empty. The shell draws the Lucide `panel-right-open` icon while the panel is open and `panel-left-open` while it is hidden (an app that supplies its own SVGs marks them `data-filter-icon="open"` and `"closed"`), and:

- sets `aria-expanded` on the button, `data-open` on the panel and `data-filters="open"` or `"closed"` on the `.search-layout`;
- starts open on wide screens and closed up to 850 px; a choice made on a wide screen is remembered per app and per toggle in `localStorage` (key `marinos.filters.<app id>.<data-filter-toggle>`, with `<body data-app-id>` as the app id), and a narrow-screen choice is never saved;
- names the button "Filters" (or `data-filter-label`) and adds ", N active" when the app keeps `data-filter-active="N"` on it (the shell watches the attribute), since the button has no visible text;
- dispatches a bubbling `marin-filters-change` event on the layout with `detail: { open, button, panel }`, so an app can measure again anything sized by the results (a Leaflet map calls `invalidateSize()`).

Hiding the panel never changes a filter; the app keeps filtering and still says what is active.

On screens up to 850 px the button sits on the same row as the first child of `.search-results` (normally the tab row) rather than on a row of its own. Keep the first child of `.search-results` the thing you want beside the button.

Name the panel with its visible heading, not a hidden label: put `<div class="search-panel-header"><h2 id="filter-panel-title" class="search-panel-title">Filter engagements</h2>…Reset…</div>` first in the panel and give the panel `aria-labelledby="filter-panel-title"`. A text filter that must always show goes in the results toolbar (below), not in the panel.

## Action buttons

A secondary button that does something other than submit a form (Copy, Link, CSV, RSS, Reset, PNG download) uses `.action-button`: an icon, with or without a short visible label ("Copy text", "Download HTML"), no fill, muted, with a visible border that turns accent when pointed at (inside an `.action-group` the buttons share the group's border instead), the same quiet look as the `.copy-button` on a listing. Name it with `aria-label` and `title`. Only a button that submits a form is solid blue or dark. Pressed state is `aria-pressed="true"`; an inert link is `aria-disabled="true"`.

```html
<div class="action-toolbar">
  <div class="action-group" role="group" aria-label="Page actions">
    <button type="button" class="action-button" aria-label="Copy" title="Copy"><svg aria-hidden="true" viewBox="0 0 24 24">…</svg></button>
    <button type="button" class="action-button" aria-label="Copy link" title="Copy link"><svg aria-hidden="true" viewBox="0 0 24 24">…</svg></button>
  </div>
  <div class="action-search" role="search" aria-label="Search engagements">
    <label class="visually-hidden" for="filter-search">Search</label>
    <input type="search" id="filter-search" placeholder="Search engagements…">
  </div>
</div>
```

A group whose buttons are all `hidden` hides itself. Add `action-group--spaced` for controls pressed often or on touch, such as Previous and Next: the buttons become separate, bordered, 44 px targets with a gap, so people with limited fine motor control or wide fingers can press the right one. The label of `.action-search` stays in the markup, visually hidden, so the field keeps its name.

## Icons for buttons

Write `data-icon="name"` on a button (or any element) and the shell draws that bundled Lucide icon before its content. `data-icon-end="name"` draws one after it ("Learn more" with an arrow). Buttons added later by script are filled in too. The icon is decoration, so name the button with `aria-label` and `title`.

```html
<button type="button" class="action-button" data-icon="download" aria-label="Download CSV" title="Download CSV"></button>
<a class="action-button" href="#more" data-icon-end="arrow-right">Learn more</a>
```

`window.MarinAppShell.icon("download")` returns the same icon as SVG markup for script that builds its own HTML. The bundled names are the Lucide files in `vendor/icons/lucide/`: arrow-down, arrow-left, arrow-right, arrow-up, check, chevron-down, chevron-left, chevron-right, chevrons-left, chevrons-right, clock, compass, copy, download, ellipsis, eye, eye-off, folder-open, funnel, grip-vertical, layout-grid, link, map-pin, maximize, minimize, panel-left-open, panel-right-open, pencil, plus, printer, redo-2, refresh-cw, rotate-ccw, rss, search, settings, share, signpost, sticky-note, trash, undo-2, upload, x. An unknown name is a console warning, not an error. An app that needs another icon adds the Lucide file to `marin-ui` first.

## Other button kinds

- **Tabs.** `.tab-list` holds `.tab-button` buttons with `role="tab"` and `aria-selected`. The chosen tab is solid with bold text.
- **Filter chips.** `.chip-button` toggles that narrow a list; `aria-pressed` says which are on. Put a row of them in `.chip-group` with `role="group"` and an `aria-label`.
- **Sort headers.** `.sort-button` inside a `th` that carries `aria-sort`; the arrow follows the attribute.
- **Dialog buttons.** `.dialog-actions` right-aligns quiet word buttons (`.action-button`) and at most one solid button, the one that submits.
- **Step list.** An app whose whole workflow is a sequence of steps puts them in the collapsible filter column: a `nav` of links numbered "1. Name" inside `.search-sidebar`, the toggle labeled with `data-filter-label="Steps"`, `aria-current="step"` on the current link, and a visible current-step line as the first child of `.search-results`. A short flow inside one feature uses a row of `.tab-button` items above the content.
- **Step flow.** In a step-by-step flow, Next is the main action: `<button type="button" class="primary" data-icon-end="arrow-right">Next: coverage</button>`. Keep the words, name the next step in lowercase, and let the shell draw the arrow. Previous sits to its left as a quiet icon button, the same as Copy, Print and Download: `<button type="button" class="action-button" data-icon="arrow-left" aria-label="Previous: details" title="Previous: details"></button>`, 44 px square. The first step has no Previous and the last has no Next. The shell sizes the arrow at 1rem beside the words (App Shell 1.23.0 and later); an app on an older release sizes it itself.
- **Danger.** Add `.is-danger` to an `.action-button` that deletes or discards: it turns red on hover and focus.
- **Menu button.** An icon `.action-button.menu-toggle` with `aria-expanded` and `aria-controls`, and the shell's caret (`.menu-toggle__caret`), opens a `.menu-panel`.

## Auditing buttons

`python3 vendor/marinos/audit-buttons.py .` (from inside an app that has installed shell 1.18.0 or later; from this repo, `python3 scripts/audit-buttons.py ../your-app`) lists every button that does not follow the standard: Pico's `secondary`, `outline` and `contrast` classes, `link-button`, and bare buttons. It reads buttons written in HTML, built with `h('button', …)`, and built with `createElement("button")` and a class name. Content that happens to be a button (a calendar event, a name that opens its record) is marked `data-button-kind="content"` and passes. Comments in script are ignored. Add `--fail` to make it exit 1, for a check script. Requirement: `marin-digital-standards/product-design/interaction-design.md`.

## Copy, download, file reading, text cleaning and upload

Apps call these helpers (App Shell 1.21.0 and later) instead of writing their own. All are on `window`. Use them for anything the person copies out, saves, or brings in.

| Helper | Use |
|---|---|
| `marinCopyRich(text, html)` | Copy for a visual editor, a CMS or an email. Resolves `true` or `false`. |
| `marinCopyText(text)` | Copy plain text. Resolves `true` or `false`. |
| `marinDownload({content, name, type, bom})` | Save a file. `type` comes from the name. A CSV starts with a byte-order mark unless `bom: false`. |
| `marinReadText(file)` | Read a file as text. Resolves `{text, encoding}`. |
| `marinDecodeText(bytes)` | The same for bytes you already have. |
| `marinCleanText(value)` | Plain characters for output that goes to a CMS, a URL or a CSV. |
| `marinUpload({button, input, accept, maxBytes, multiple, onFile, onMessage})` | A Browse files button and drop anywhere on the page. |

**Copy and Download list the same three formats, in the same order: Text, HTML, Markdown.** `marinContentFormats(root)` reads a page and returns `{ text, html, markdown }`: headings, paragraphs, lists, tables and links, with no classes, styles or scripts. It leaves out `.doc-actions`, `.doc-updated`, `.heading-anchor`, `nav`, `script`, `style` and anything marked `data-no-copy`. `marinFormatMenus(container, provider, { fileName })` wires `[data-copy-format]` and `[data-download-format]` buttons (`text`, `html` or `markdown`) inside the container to the three strings (or to a function that returns them) and to the helpers above. Copy Text copies rich text for pasting into a visual editor; Copy HTML and Copy Markdown copy the source. A page of ordinary content wires itself with no script:

```html
<div class="doc-actions" data-formats-for="article.content" data-file-name="my-page">
  <div class="menu">
    <button type="button" class="action-button menu-toggle" data-icon="copy" aria-expanded="false" aria-controls="copy-panel" aria-label="Copy, choose a format" title="Copy"><svg class="menu-toggle__caret" aria-hidden="true" viewBox="0 0 16 16"><path d="M4 6l4 4 4-4"/></svg></button>
    <div id="copy-panel" class="menu-panel" hidden>
      <button type="button" data-button-kind="menu-item" data-copy-format="text">Text</button>
      <button type="button" data-button-kind="menu-item" data-copy-format="html">HTML</button>
      <button type="button" data-button-kind="menu-item" data-copy-format="markdown">Markdown</button>
    </div>
  </div>
  <span class="doc-action-status" role="status" aria-live="polite"></span>
</div>
```

A menu built after the page loads is wired by `marinFormatMenus` (or `marinWireMenus(container)`). A page whose content is data (a note, a report) builds its own three strings and calls `marinFormatMenus(container, () => ({ text, html, markdown }), { fileName, status, onFail })`; `onFail(text)` is called when a copy fails, so the app can show that text in a box for the person to copy by hand. Every Copy button, including the one on a card, offers these three formats; the one button that copies a link is **Copy link**, a lone icon button with the `link` icon (`data-action="share"`).

**Rich copy puts exactly the HTML you give it on the clipboard.** Do not copy a rendered element (a hidden `contenteditable` that you select and `execCommand("copy")`): the browser then adds this page's fonts, sizes, colors and bold weights as inline styles, and a CMS turns a bold heading into `<strong>`. Build clean HTML (`h2`, `p`, `ul`, `li`, `a`, no classes, no styles) and pass it to `marinCopyRich`. `marinCopyRich` uses the browser's copy event, which puts exactly the HTML you give it on the clipboard (the asynchronous Clipboard API sanitizes HTML, and one app found a title losing its link that way), then falls back to the asynchronous Clipboard API. When both fail, show the text in a box for the person to copy by hand. Show the result in the page's status line ("Copied.") and say nothing when nothing was wrong.

**Downloads are UTF-8.** `marinDownload` adds the byte-order mark to a CSV so Excel reads accents and apostrophes correctly. Pass a string, a Blob or a typed array.

**Files that are not UTF-8 are read as Windows-1252.** A file saved from Excel stores a curly apostrophe as one byte, which a UTF-8 reader shows as "\ufffd". `marinReadText` reads valid UTF-8 as UTF-8 and everything else as Windows-1252, so the text never holds a replacement character that the helper made. An app that must not guess (Marin CSV) keeps refusing files that are not UTF-8 and tells the person to save the file as CSV UTF-8.

**`marinCleanText` is opt-in.** It changes curly quotes to straight ones, non-breaking and zero-width characters to plain spaces or nothing, repairs text read with the wrong encoding (`â€™`), and turns a replacement character between two letters into an apostrophe. Use it where the output goes to a CMS, a URL or a CSV. An app that shows text keeps its typographic quotes. Do not show a message about it.

**Upload** uses one pattern in every app:

```html
<article class="app-card upload-panel">
  <h2>Upload</h2>
  <p id="upload-help" class="app-help-text">Drag and drop a <code>.csv</code>/<code>.xlsx</code> file anywhere on this page, or use the browse button.</p>
  <div class="app-actions">
    <button id="browse-files" type="button" class="action-button" data-icon="upload">Browse files</button>
  </div>
  <input id="file-input" class="visually-hidden" type="file" aria-label="Upload a file" aria-describedby="upload-help" accept=".csv,.xlsx">
  <p id="file-status" class="app-help-text" role="status" aria-live="polite"></p>
</article>
```

```js
marinUpload({
  button: document.querySelector("#browse-files"),
  input: document.querySelector("#file-input"),
  accept: [".csv", ".xlsx"],
  maxBytes: 10 * 1048576,
  onFile: async (file) => load((await marinReadText(file)).text),
  onMessage: (text) => { status.textContent = text; },
});
```

The shell script is deferred, so call `marinUpload` inside a `DOMContentLoaded` listener when your script is inline in the page (the other helpers are used from event handlers, which run later). The heading is "Upload". The sentence names the file types as `.csv/.xlsx` and says where to drop. Add "Your file stays in this browser." when it is true. The helper shows a "Drop a file to upload" layer while a file is dragged over the page, passes the first file when several are dropped and says so, and sends the same plain messages for a wrong type ("Unsupported file type. Upload .csv or .xlsx.") and a file that is too large ("That file is too large. The limit is 10 MB."). Put the messages in the page's status line.

**Copy and Download menus.** When there are several formats, use one button that opens a menu (`.menu`, `.menu-toggle`, `.menu-panel`), the same as the logo downloads in Marin Brand. List the formats in the order Text, HTML, Markdown, and use the same order in Copy and Download. The menu items are `button[data-button-kind="menu-item"]`.

## Auditing shared helpers

`vendor/marinos/audit-shared-helpers.py` lists the places an app still does its own copy, download, file reading or upload:

```bash
python3 vendor/marinos/audit-shared-helpers.py .
```

It only reports, so it does not stop a check. Add `--fail` once the app has adopted the helpers. Third-party libraries (a `libs/` or `lib/` folder, `.min.js` files) are skipped. When code has a reason to do its own (Marin CSV refuses a file that is not UTF-8 rather than guess), put a comment containing `marin-shared-helpers: allow` and the reason on that line or the line above.

## Automatically provided infrastructure

On initial load, the shell:

- inserts a “Skip to main content” link when one is not already present;
- sets `tabindex="-1"` on `main#main` when absent;
- inserts `#app-status-message` inside `main#main` when absent;
- publishes `window.MarinAppShell.version` and `window.MarinAppShell.marinUiVersion`;
- sets version data attributes on the root `<html>` element; and
- dispatches `marinos:shell-ready` with the two versions in `event.detail`.

A missing `main#main` produces a console warning.

## Record list

A `[data-record-list]` element loads a JSON file and draws the records that match as the result cards the apps use (`ul.search-results-list` of `li.app-card.mm-card`), available from App Shell 1.24.0. It lets one app's records appear on another app's page without a copy of that app's code. It loads the first time it becomes visible, using the same `hidden` check as the Updates feed, so it works inside a tab section. Key numbers and charts (below) load the same way, and a file used by several of them on one page is fetched once.

```html
<section id="reach" data-tab-section="reach" hidden>
  <div data-record-list data-app-name="Reach" data-noun="engagements"
       data-src="https://marincountygov.github.io/marin-reach/data/engagements.json" data-records="records"
       data-match="agencies" data-value="Community Development Agency"
       data-title="eventName" data-meta="date,location" data-badge="status" data-text="project" data-sort="date"></div>
</section>
```

| Attribute | Meaning |
|---|---|
| `data-src` | Required. The JSON address. It can be on another site that allows reading it. `{date:-29}` is the UTC date 29 days ago and `{date:0}` today. |
| `data-records` | Dot path to the list of records. Leave out when the file is the list. |
| `data-match`, `data-value` | Keep a record when this field equals the value, or contains it when the field is a list. Leave out to draw every record. |
| `data-exclude` | `field=value`. Drop the records whose field equals the value (or lists it), before anything is drawn or counted. Key numbers and charts take it too. Use it to leave out one kind of record, such as `sourceType=social`. |
| `data-title` | Required. The field shown as the card heading. |
| `data-link` | A field holding an http or https address. The heading becomes a link to it. |
| `data-link-template` | Instead of `data-link`: an address with `{field}` parts filled from each record (values are encoded), such as `https://example.org/app/?engagement={id}`. Use it when the target app opens one record from its address. |
| `data-meta` | Comma-separated fields shown under the heading, joined by a dash. `field:words` adds words after the value (`redirects:visits` reads "5 visits"). |
| `data-hidden-path`, `data-hidden-text` | A flag that, when true, withholds the list and shows the text instead, for a service that hides small counts. |
| `data-text` | A field shown as a short description under that line. |
| `data-image` | A field holding an http or https address of a picture, shown beside the text. |
| `data-badge` | A field shown as a badge above the heading. |
| `data-sort`, `data-sort-order` | Sort field, and `desc` (default) or `asc`. |
| `data-limit` | Most cards drawn. Default 24; the status line says how many were left out. |
| `data-empty-text` | Said instead of "No … found." when nothing is left to draw. Use it when a filter (`data-match`, `data-exclude`) can leave a list empty for a reason a person cannot see. |
| `data-src` with several files | Several addresses separated by spaces: their records are joined (a file that cannot be read is skipped unless none can). `data-unique` names the field that makes two records the same one, so a record in two files is drawn and counted once. Key numbers and charts take both. |
| `data-columns` | `2` or `3`: draw the cards in that many columns on a wide screen, one on a narrow one. Pick a `data-limit` that is a multiple of it so the last row is full. |
| `data-group`, `data-group-link`, `data-group-date`, `data-group-noun` | One card for each value of a field (an array field counts each value) instead of one for each record: the value as the heading, how many records it has (`data-group-noun` names them) and the dates they span (`data-group-date`). `data-group-link` is the address the heading links to, with `{value}` replaced by the value. Newest first. Use it for a list of campaigns drawn from their events. |
| `data-timeframe` | The date field. The status line then says how far back the records go, from the oldest: "(last week)", "(last month)", "(last 3 months)" or "(since Jan 5, 2026)". |
| `data-app-name`, `data-noun` | Words for the status lines: "Loading Reach…", "2 engagements.", "No engagements found.", "Reach could not be loaded right now." |

Field names can be dot paths. Values are always set as text, never as HTML. A `YYYY-MM-DD` value is shown as a long date, and a full date and time as the short form the console shows ("Nov 2, 4:12 PM", Pacific time). The card styles (`.mm-card`, `.search-results-list`) are the apps' own; a page that uses the component needs them in its stylesheet. Tested by `tests/browser_record_list.py`.

## Key numbers

A `[data-key-numbers]` element shows a few numbers as the apps' stat cards (`.mm-stats-kpis`). They are either numbers a service already added up, or numbers counted from the records. It loads the first time it becomes visible.

```html
<div data-key-numbers data-app-name="Links"
     data-src="https://example.org/api/summary?from={date:-29}&to={date:0}"
     data-fields="period_redirects:Visits,tracked_links:Links"
     data-hidden-path="meta.suppressed" data-hidden-text="Too few visits to show."></div>

<div data-key-numbers data-app-name="Mentions" data-src="monitors/marin-cda.json" data-records="items"
     data-compute='[["count","Mentions"],["unique","Unique sources","source"],["count","Social","sourceType","social"]]'></div>
```

`data-src` is required, with `data-fields` or `data-compute`. `data-fields` is `field:Label` pairs; a field is a dot path under `data-path` (default `data`). `data-compute` is a JSON list counted from the records (with `data-records`, `data-match` and `data-value` as in the record list): `["count","Label"]` counts the records, `["count","Label","field","value"]` counts those whose field equals the value, and `["unique","Label","field"]` counts the different values. `data-hidden-path` names a flag; when it is true the numbers are withheld and `data-hidden-text` is shown, for a service that hides small counts. Numbers get thousands separators, and values are set as text.

## Charts

A `[data-chart]` element draws one of the apps' chart cards with Chart.js, from the same kind of file. The page supplies its own copy of Chart.js (`data-chart-lib`); the component loads it when the first chart is shown.

```html
<div class="mm-stats-grid">
  <div data-chart data-app-name="Mentions" data-src="monitors/marin-cda.json" data-records="items"
       data-chart-lib="../vendor/chart.min.js" data-chart-title="Mentions over time"
       data-kind="line" data-date="publishedAt" data-bucket="day"></div>
  <div data-chart data-app-name="Mentions" data-src="monitors/marin-cda.json" data-records="items"
       data-chart-lib="../vendor/chart.min.js" data-chart-title="Top sources" data-kind="bar" data-group="source"></div>
</div>
```

| Attribute | Meaning |
|---|---|
| `data-src`, `data-records`, `data-match`, `data-value` | As for the record list. |
| `data-chart-lib` | Required. The address of `chart.min.js` on the page's own site. |
| `data-chart-title` | Required. The card heading. |
| `data-kind` | `line` (default) counts records per day or month; `bar` ranks values, as horizontal bars. |
| `data-date`, `data-bucket` | Line. The date field, and `day` (default) or `month`. Days and months with nothing stay on the line as zero. Days are Pacific. |
| `data-group`, `data-top` | Bar. The field to rank (a list field counts each value) and the most bars (default 10). |
| `data-sum` | Add up this field instead of counting records, for rows a service already added up by day. |
| `data-hidden-path` | As for key numbers. When the flag is true the chart is left out, since the key numbers beside it say why. |
| `data-empty-text` | Words for a chart with nothing to draw. |
| `data-hide-empty` | Hide a chart drawn from records when there is nothing to draw, instead of saying so. Use it for a teaser chart above a list that already says it is empty. |
| `data-inline` | Instead of `data-src`: the id of a `<script type="application/json">` in the page that holds the amounts (below). Nothing is fetched except Chart.js. |
| `data-kind="columns"` or `"bars"` | With `data-inline`: vertical columns, or horizontal bars. Both start at zero. |
| `data-kind="pie"` | With `data-inline`: the first series as shares of a whole. Slices run from the largest, zero values have no slice, and the legend names each slice with its share; the tooltip gives the amount and the percentage. Use it for the parts of one total at one time, not for change over time. |
| `data-stacked` | With `data-inline`: stack the series. |

The canvas has a text summary for screen readers (the total and the peak, or the top bar). Charts take the page's text and grid colors. Tested by `tests/browser_record_list.py`, with a stand-in for Chart.js.

**Amounts the page already holds** (a budget) are drawn from a block in the page, so the chart and the table beside it come from the same figures:

```html
<script type="application/json" id="types-spec">{"labels": ["Salaries and Benefits", "Services and Supplies"],
  "series": [{"name": "FY 2025-26", "values": [16125624, 4611103]}, {"name": "FY 2026-27", "values": [17890809, 4911771]}],
  "format": "currency", "summary": "Salaries and Benefits is the largest at $17,890,809."}</script>
<div data-chart data-inline="types-spec" data-chart-lib="../vendor/chart.min.js" data-chart-title="Expenditure by type" data-kind="columns"></div>
```

`format` is `currency` (axis in $K and $M, tooltips and the text summary in whole dollars, a minus sign for decreases) or `number`. `summary` is the sentence screen readers get after the title; without it the component names the largest value, or each series' total. Several series are drawn side by side, named in a legend; the colors are chosen to stay apart for people who see color differently, and color is never the only signal. Put the data in the table beside the chart too.

## Sub-tabs

A `[data-subtabs]` group inside a tab section splits it into panels. It holds a `[data-subtabs-nav]` of links and `[data-subtab]` panels; each link is `#` plus a panel's `id`, and a link to the tab section itself means the first panel.

```html
<section id="mentions" data-tab-section="mentions" hidden>
  <div data-subtabs>
    <nav data-subtabs-nav aria-label="Mentions sections"><a href="#mentions">Home</a><a href="#mentions-stats">Stats</a></nav>
    <div id="mentions-home" data-subtab>…</div>
    <div id="mentions-stats" data-subtab hidden>…</div>
  </div>
</section>
```

One panel shows at a time: the one the hash names, or contains an element the hash names, else the first. The nav marks the current link with `aria-current="page"`. A hash that names a panel opens its tab section without the shell scrolling to it. Record lists, key numbers and charts in a hidden panel load when it is first shown. Available from App Shell 1.24.0.

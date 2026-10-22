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

A secondary button that does something other than submit a form (Copy, Link, CSV, RSS, Reset, PNG download) uses `.action-button`: an icon and no visible text, no fill, muted, a border on hover, the same quiet look as the `.copy-button` on a listing. Name it with `aria-label` and `title`. Only a button that submits a form is solid blue or dark. Pressed state is `aria-pressed="true"`; an inert link is `aria-disabled="true"`.

```html
<div class="action-toolbar">
  <div class="action-group" role="group" aria-label="Share">
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
- **Danger.** Add `.is-danger` to an `.action-button` that deletes or discards: it turns red on hover and focus.
- **Menu button.** An icon `.action-button.menu-toggle` with `aria-expanded` and `aria-controls`, and the shell's caret (`.menu-toggle__caret`), opens a `.menu-panel`.

## Auditing buttons

`python3 scripts/audit-buttons.py ../your-app` lists every button that does not follow the standard: Pico's `secondary`, `outline` and `contrast` classes, `link-button`, and bare buttons. It reads buttons written in HTML, built with `h('button', …)`, and built with `createElement("button")` and a class name. Content that happens to be a button (a calendar event, a name that opens its record) is marked `data-button-kind="content"` and passes. Comments in script are ignored. Add `--fail` to make it exit 1, for a check script. Requirement: `marin-digital-standards/product-design/interaction-design.md`.

## Automatically provided infrastructure

On initial load, the shell:

- inserts a “Skip to main content” link when one is not already present;
- sets `tabindex="-1"` on `main#main` when absent;
- inserts `#app-status-message` inside `main#main` when absent;
- publishes `window.MarinAppShell.version` and `window.MarinAppShell.marinUiVersion`;
- sets version data attributes on the root `<html>` element; and
- dispatches `marinos:shell-ready` with the two versions in `event.detail`.

A missing `main#main` produces a console warning.

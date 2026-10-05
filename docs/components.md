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

### Accessibility content

```html
<template data-accessibility>
  <p>Document application-specific accessibility support and known limitations.</p>
</template>
```

When omitted, the shell provides generic shared-interface and reporting language. Each app remains responsible for testing its own workflow.

### Updates introduction

```html
<template data-updates-intro>
  <p>Optional context about the release notes.</p>
</template>
```

## `marin-app-footer`

Renders the local app identity, standard information navigation, and MarinOS platform link.

```html
<marin-app-footer app-name="Marin Unzipper"></marin-app-footer>
```

Attributes:

| Attribute | Required | Default | Purpose |
| --- | --- | --- | --- |
| `app-name` | Yes | `Application` | Visible app name and navigation label. |
| `links` | No | `about security accessibility updates` | Standard footer links to include. |
| `platform-name` | No | `MarinOS` | Platform link label. |
| `platform-url` | No | MarinOS home | Platform link destination. |

The app name is intentionally text, not a link. Standard links use anchors within the current `index.html`.

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

## Automatically provided infrastructure

On initial load, the shell:

- inserts a “Skip to main content” link when one is not already present;
- sets `tabindex="-1"` on `main#main` when absent;
- inserts `#app-status-message` inside `main#main` when absent;
- publishes `window.MarinAppShell.version` and `window.MarinAppShell.marinUiVersion`;
- sets version data attributes on the root `<html>` element; and
- dispatches `marinos:shell-ready` with the two versions in `event.detail`.

A missing `main#main` produces a console warning.

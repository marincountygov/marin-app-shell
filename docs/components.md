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
| `label` | `ALPHA` | Small release label shown after MarinOS. Use an empty value to omit it. |
| `catalog-url` | MarinOS `catalog.json` | Catalog source used to refresh the menu. |
| `browse-url` | MarinOS home | Destination for “Browse all in MarinOS.” |

The shell keeps bundled fallback links when the catalog request fails or is unavailable.

## `marin-app-header`

Renders the semantic application header, app identity, mobile menu control, and top navigation.

The complete app identity is a link to `./`. Selecting the app icon, name, or description returns the application to its root URL and default on-load content.

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

The rendered identity layout is `.app-identity > a.app-identity__home.app-title-row`,
with the icon and title-copy as direct children. The anchor keeps visible focus
and `href="./"`. Do not target its former extra wrapper from app CSS.

Missing icon templates fall back to the bundled Lucide `layout-grid`. Older
1.0.x templates that omit root presentation attributes receive defaults, but
app-specific icon validation remains the app's responsibility.

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

# Security policy

## Reporting a vulnerability

Report suspected vulnerabilities to `innovation@marincounty.gov`. Do not include sensitive personal information, credentials, or exploit details in a public issue.

The public disclosure file is available at `.well-known/security.txt`.

## Supported versions

Only the latest release in the current major version receives security fixes. Consuming applications vendor a pinned release and must update their local `vendor/marinos/` directory to receive a fix.

## Runtime boundaries

Marin App Shell is client-side HTML, CSS, and JavaScript. It does not provide authentication, authorization, server-side validation, secure storage, or data protection for application-specific workflows. Each consuming application remains responsible for its own threat model and `security.json`.

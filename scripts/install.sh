#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)
SOURCE_DIR="$ROOT_DIR/dist"

usage() {
  cat <<'USAGE'
Usage: ./scripts/install.sh /path/to/marinos-app

Copies the committed shell distribution to APP/vendor/marinos using an atomic
replacement. It does not change index.html, marin.yml, or application code.
USAGE
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 2
fi

APP_DIR=$(cd -- "$1" 2>/dev/null && pwd) || {
  printf 'Application directory does not exist: %s\n' "$1" >&2
  exit 2
}

if [[ ! -f "$APP_DIR/marin.yml" ]]; then
  printf 'Expected %s/marin.yml; refusing to install into an unknown directory.\n' "$APP_DIR" >&2
  exit 2
fi

if [[ ! -f "$SOURCE_DIR/manifest.json" ]]; then
  printf 'Distribution is missing. Run ./scripts/build.sh first.\n' >&2
  exit 2
fi

VENDOR_DIR="$APP_DIR/vendor"
DEST_DIR="$VENDOR_DIR/marinos"
mkdir -p "$VENDOR_DIR"
TEMP_DIR=$(mktemp -d "$VENDOR_DIR/.marinos.XXXXXX")
BACKUP_DIR=""
trap 'rm -rf "$TEMP_DIR"; [[ -n "$BACKUP_DIR" ]] && rm -rf "$BACKUP_DIR"' EXIT
cp -a "$SOURCE_DIR/." "$TEMP_DIR/"

if [[ -e "$DEST_DIR" ]]; then
  BACKUP_DIR=$(mktemp -d "$VENDOR_DIR/.marinos-backup.XXXXXX")
  rmdir "$BACKUP_DIR"
  mv "$DEST_DIR" "$BACKUP_DIR"
fi

mv "$TEMP_DIR" "$DEST_DIR"
TEMP_DIR=""
[[ -n "$BACKUP_DIR" ]] && rm -rf "$BACKUP_DIR"
BACKUP_DIR=""
trap - EXIT

VERSION=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["shellVersion"])' "$DEST_DIR/manifest.json")
printf 'Installed Marin App Shell %s in %s\n' "$VERSION" "$DEST_DIR"

if [[ ! -f "$APP_DIR/vendor/fonts/Jost-wght.ttf" || ! -f "$APP_DIR/vendor/fonts/open-sans/OpenSans-VariableFont_wdth,wght.woff2" ]]; then
  printf 'WARN: One or more expected MarinOS fonts are absent under %s/vendor/fonts. System fallbacks will be used.\n' "$APP_DIR" >&2
fi

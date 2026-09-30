#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)

usage() {
  cat <<'USAGE'
Usage: ./scripts/sync-fonts.sh /path/to/marin-app-template-or-app [destination]

Copies the existing MarinOS self-hosted font assets from SOURCE/vendor/fonts.
The default destination is this repository's ./fonts directory, which lets the
root demonstration page resolve the same relative font paths used by apps.
USAGE
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage >&2
  exit 2
fi

SOURCE_ROOT=$(cd -- "$1" 2>/dev/null && pwd) || {
  printf 'Source directory does not exist: %s\n' "$1" >&2
  exit 2
}
SOURCE_FONTS="$SOURCE_ROOT/vendor/fonts"
DESTINATION=${2:-"$ROOT_DIR/fonts"}

if [[ ! -f "$SOURCE_FONTS/Jost-wght.ttf" || ! -f "$SOURCE_FONTS/open-sans/OpenSans-VariableFont_wdth,wght.woff2" ]]; then
  printf 'Expected MarinOS fonts were not found under %s\n' "$SOURCE_FONTS" >&2
  exit 2
fi

mkdir -p "$DESTINATION/open-sans"
cp "$SOURCE_FONTS/Jost-wght.ttf" "$DESTINATION/Jost-wght.ttf"
cp "$SOURCE_FONTS/open-sans/OpenSans-VariableFont_wdth,wght.woff2" \
  "$DESTINATION/open-sans/OpenSans-VariableFont_wdth,wght.woff2"
if [[ -f "$SOURCE_FONTS/open-sans/OFL.txt" ]]; then
  cp "$SOURCE_FONTS/open-sans/OFL.txt" "$DESTINATION/open-sans/OFL.txt"
fi
printf 'Copied MarinOS fonts to %s\n' "$DESTINATION"

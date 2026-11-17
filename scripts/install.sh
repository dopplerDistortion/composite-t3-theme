#!/usr/bin/env bash
# Copy the built theme and its background into T3 Code's themes folder.
# Then pick "Composite" in T3 Code's appearance settings.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
themes="${T3_THEMES_DIR:-$HOME/.t3/userdata/themes}"

test -f "$root/dist/composite.json" || { echo "dist/composite.json is missing: run scripts/build.py" >&2; exit 1; }
mkdir -p "$themes"
cp "$root/dist/composite.json" "$root/dist/composite.png" "$themes/"
echo "Installed to $themes"

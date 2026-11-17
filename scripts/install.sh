#!/usr/bin/env bash
# Copy the built theme and its background into T3 Code's themes folder.
# Then pick "goksen.ing" in T3 Code's appearance settings.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
themes="${T3_THEMES_DIR:-$HOME/.t3/userdata/themes}"

test -f "$root/dist/goksen-ing.json" || { echo "dist/goksen-ing.json is missing: run scripts/build.py" >&2; exit 1; }
mkdir -p "$themes"
cp "$root/dist/goksen-ing.json" "$root/dist/goksen-ing.png" "$themes/"
echo "Installed to $themes"

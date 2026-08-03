#!/usr/bin/env bash
# Generate a new industry scaffold from the _template.
# Usage: bash scripts/generate-industry.sh <slug>
# Example: bash scripts/generate-industry.sh furniture

set -euo pipefail

SLUG="${1:?Usage: $0 <slug>}"

# Validate slug
if ! [[ "$SLUG" =~ ^[a-z][a-z0-9_-]*$ ]]; then
    echo "ERROR: slug must be lowercase letters, digits, hyphens or underscores (e.g. 'furniture')"
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="$REPO_ROOT/industries/_template"
TARGET_DIR="$REPO_ROOT/industries/$SLUG"

if [ -d "$TARGET_DIR" ]; then
    echo "ERROR: industries/$SLUG already exists"
    exit 1
fi

echo "Creating industries/$SLUG from template..."
cp -r "$TEMPLATE_DIR" "$TARGET_DIR"

# Replace placeholder slug and name in industry.yaml
DISPLAY_NAME="$(echo "$SLUG" | sed 's/-/ /g; s/\b\(.\)/\u\1/g') Industry"
sed -i.bak \
    -e "s/slug: \"myindustry\"/slug: \"$SLUG\"/" \
    -e "s/name: \"My Industry Name\"/name: \"$DISPLAY_NAME\"/" \
    -e "s/name: \"myindustry.localhost\"/name: \"$SLUG.localhost\"/" \
    -e "s/\"manager@myindustry.demo\"/\"manager@$SLUG.demo\"/" \
    "$TARGET_DIR/industry.yaml"
rm -f "$TARGET_DIR/industry.yaml.bak"

echo ""
echo "Done! New industry scaffold created at: industries/$SLUG/"
echo ""
echo "Next steps:"
echo "  1. Edit industries/$SLUG/industry.yaml (name, company, seed.random_seed)"
echo "  2. Add CSV data files to industries/$SLUG/data/"
echo "  3. Implement seeders in industries/$SLUG/seeders/"
echo "  4. Run: demostackkit validate $SLUG"
echo "  5. Run: demostackkit up $SLUG"

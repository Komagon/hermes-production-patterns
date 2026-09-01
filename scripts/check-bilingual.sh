#!/usr/bin/env bash
# check-bilingual.sh — Verify README.md and README.en.md have the same number of sections.
# Exits non-zero if section counts diverge.
# Run from repo root: bash scripts/check-bilingual.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

CN_COUNT=$(grep -c '^## ' "$ROOT/README.md")
EN_COUNT=$(grep -c '^## ' "$ROOT/README.en.md")

echo "CN sections ($CN_COUNT):"
grep '^## ' "$ROOT/README.md" | sed 's/^/  /'
echo ""
echo "EN sections ($EN_COUNT):"
grep '^## ' "$ROOT/README.en.md" | sed 's/^/  /'

if [ "$CN_COUNT" != "$EN_COUNT" ]; then
  echo ""
  echo "MISMATCH: CN=$CN_COUNT, EN=$EN_COUNT. Sync README.en.md with README.md."
  exit 1
fi

echo ""
echo "PASS: both READMEs have $CN_COUNT sections."

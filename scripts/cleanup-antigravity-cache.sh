#!/usr/bin/env bash
# cleanup-antigravity-cache.sh
# Prunes old Antigravity IDE cache data (conversations, brain, recordings).
# Safe to run anytime — preserves the last N days of data.
#
# Usage:
#   ./scripts/cleanup-antigravity-cache.sh          # default: keep 7 days
#   ./scripts/cleanup-antigravity-cache.sh 3        # keep 3 days
#   ./scripts/cleanup-antigravity-cache.sh --dry-run # preview what would be deleted

set -euo pipefail

CACHE_DIR="${HOME}/.gemini/antigravity-ide"
KEEP_DAYS="${1:-7}"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  KEEP_DAYS="${2:-7}"
fi

if [[ ! -d "$CACHE_DIR" ]]; then
  echo "Cache dir not found: $CACHE_DIR"
  exit 1
fi

echo "Antigravity IDE cache cleanup"
echo "  Cache dir: $CACHE_DIR"
echo "  Keep:      last $KEEP_DAYS days"
echo "  Dry run:   $DRY_RUN"
echo ""

before=$(du -sh "$CACHE_DIR" 2>/dev/null | cut -f1)

# 1. Old conversation protobuf files
conv_count=$(find "$CACHE_DIR/conversations/" -name "*.pb" -mtime +"$KEEP_DAYS" 2>/dev/null | wc -l)
if $DRY_RUN; then
  echo "[dry-run] Would delete $conv_count conversation(s) older than $KEEP_DAYS days"
else
  find "$CACHE_DIR/conversations/" -name "*.pb" -mtime +"$KEEP_DAYS" -delete 2>/dev/null
  echo "Deleted $conv_count old conversation(s)"
fi

# 2. Old brain directories (artifacts, scratch, logs)
brain_count=$(find "$CACHE_DIR/brain/" -maxdepth 1 -mindepth 1 -type d -mtime +"$KEEP_DAYS" 2>/dev/null | wc -l)
if $DRY_RUN; then
  echo "[dry-run] Would delete $brain_count brain dir(s) older than $KEEP_DAYS days"
else
  find "$CACHE_DIR/brain/" -maxdepth 1 -mindepth 1 -type d -mtime +"$KEEP_DAYS" -exec rm -rf {} + 2>/dev/null
  echo "Deleted $brain_count old brain dir(s)"
fi

# 3. Browser recordings
rec_count=$(find "$CACHE_DIR/browser_recordings/" -maxdepth 1 -mindepth 1 -type d -mtime +"$KEEP_DAYS" 2>/dev/null | wc -l)
if $DRY_RUN; then
  echo "[dry-run] Would delete $rec_count browser recording dir(s) older than $KEEP_DAYS days"
else
  find "$CACHE_DIR/browser_recordings/" -maxdepth 1 -mindepth 1 -type d -mtime +"$KEEP_DAYS" -exec rm -rf {} + 2>/dev/null
  echo "Deleted $rec_count old browser recording dir(s)"
fi

after=$(du -sh "$CACHE_DIR" 2>/dev/null | cut -f1)
echo ""
echo "Before: $before → After: $after"

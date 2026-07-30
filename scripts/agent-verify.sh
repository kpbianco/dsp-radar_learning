#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMANDS="$ROOT/contracts/verification.commands"
LOG_DIR="$ROOT/docs/evidence/local"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="$LOG_DIR/verify-$STAMP.log"
mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG") 2>&1
printf 'repository=%s\nstarted=%s\n' "$ROOT" "$(date --iso-8601=seconds)"
while IFS= read -r command || [[ -n "$command" ]]; do
  [[ -z "${command//[[:space:]]/}" ]] && continue
  [[ "$command" =~ ^[[:space:]]*# ]] && continue
  printf '\n>>> %s\n' "$command"
  bash -lc "cd \"$ROOT\" && $command"
done < "$COMMANDS"
printf '\ncompleted=%s\nlog=%s\n' "$(date --iso-8601=seconds)" "$LOG"

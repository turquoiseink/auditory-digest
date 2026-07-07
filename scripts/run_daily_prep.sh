#!/usr/bin/env bash
# run_daily_prep.sh — step 1 of the daily run: deterministic fetch only.
# Writes state/candidates.json, state/context.json, and resets the attempt
# counter for today. No LLM here.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 src/prep.py

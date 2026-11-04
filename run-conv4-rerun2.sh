#!/usr/bin/env bash
# LoCoMo conv4 rerun #2 — entity guard active
# Entity guard memories (75 entries) already injected into mem0 for locomo_4_full01
# This run will measure OD improvement from entity preservation
set -euo pipefail
cd "$(dirname "$0")"

RUVENV=/Users/a1-6/Desktop/workspace/tools/mem0-venv/bin/python

echo "=== conv4 rerun #2 (entity guard) start $(date) ==="
OPENAI_BASE_URL=http://localhost:8787/v1 \
OPENAI_API_KEY=sk-vll...V9cY \
"$RUVENV" -m benchmarks.locomo.run \
  --project-name locomo-vllm \
  --run-id full01-eg \
  --answerer-model qwen3.8-27b \
  --judge-model qwen3.8-27b \
  --provider openai \
  --backend oss \
  --mem0-host http://127.0.0.1:8888 \
  --conversations 4 \
  --max-workers 1
echo "=== conv4 rerun #2 done $(date) ==="

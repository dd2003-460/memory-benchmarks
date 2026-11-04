#!/usr/bin/env bash
# LoCoMo conv4 补跑 — 绕过 ClashX TUN 代理，直连 localhost:8787
# 根因：full01 跑 conv4 时 answerer 经 TUN 代理到局域网 vLLM 连续 502 → 全空
# ingestion 已完成（680 chunks, user_id=locomo_4_full01），只需答题
set -euo pipefail
cd "$(dirname "$0")"

RUVENV=/Users/a1-6/Desktop/workspace/tools/mem0-venv/bin/python

echo "=== conv4 rerun start $(date) ==="
OPENAI_BASE_URL=http://localhost:8787/v1 \
OPENAI_API_KEY=sk-vll...V9cY \
"$RUVENV" -m benchmarks.locomo.run \
  --project-name locomo-vllm \
  --run-id full01 \
  --answerer-model qwen3.8-27b \
  --judge-model qwen3.8-27b \
  --provider openai \
  --backend oss \
  --mem0-host http://127.0.0.1:8888 \
  --conversations 4 \
  --max-workers 1 \
  --resume
echo "=== conv4 rerun done $(date) ==="
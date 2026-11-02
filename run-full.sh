#!/usr/bin/env bash
# LoCoMo FULL run (10 conversations, 1986 questions) — v3-pipeline server + vLLM
# Prereq: smoke done; kill old server; fresh qdrant path (mem0-config-vllm-full.yaml)
set -euo pipefail
cd "$(dirname "$0")"

PYVENV=/Users/a1-6/Desktop/workspace/tools/mb-server-venv/bin/python
RUVENV=/Users/a1-6/Desktop/workspace/tools/mem0-venv/bin/python

# 1) ensure server up (with env vars; do NOT kill if already healthy)
if ! curl -sf http://127.0.0.1:8888/health >/dev/null 2>&1; then
  lsof -ti :8888 | xargs kill -9 2>/dev/null || true
  sleep 2
  OPENAI_API_KEY=sk-vllm-17L3d6z60EuhN1yW_bcRoynvDmxoAk1GKsF3QvSV9cY \
  OPENAI_BASE_URL=http://100.112.53.47:8000/v1 \
  MEM0_CONFIG_PATH="$(pwd)/mem0-config-vllm-full.yaml" \
  "$PYVENV" -m uvicorn main:app --app-dir local-server --host 127.0.0.1 --port 8888 \
  > /tmp/mb-server-full.log 2>&1 &
  echo $! > /tmp/mb-server-full.pid
  for i in $(seq 1 30); do
    sleep 5
    if curl -sf http://127.0.0.1:8888/health >/dev/null 2>&1; then break; fi
  done
fi
curl -sf http://127.0.0.1:8888/health && echo

# 2) full run
OPENAI_BASE_URL=http://100.112.53.47:8000/v1 \
OPENAI_API_KEY=sk-vllm-17L3d6z60EuhN1yW_bcRoynvDmxoAk1GKsF3QvSV9cY \
"$RUVENV" -m benchmarks.locomo.run \
  --project-name locomo-vllm \
  --run-id full01 \
  --answerer-model qwen3.8-27b \
  --judge-model qwen3.8-27b \
  --provider openai \
  --backend oss \
  --mem0-host http://127.0.0.1:8888 \
  --max-workers 1 \
  --resume

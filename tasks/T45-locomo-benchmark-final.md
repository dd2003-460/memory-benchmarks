【执行前必读】
1. 本任务必须走 1-loop：先读 sop/arena-loop-pipeline.md + loop/prompt-first/00..04.5
2. 每阶段产出落盘 loop-artifacts/stages/<N>/
3. 完成后 commit + push
4. 通道故障 → 报告 Lead 降级，不得静默跳过

# T45: LoCoMo conv4 Benchmark Final (S0 vs S1, n≥3 runs)

## 目标
验证 entity-guard (S1) 在 LoCoMo conv4 上对 baseline (S0) 的增益是否统计显著且可复现。

## 执行步骤（本地 vLLM :8787 + mem0 :8888）

1. **确认数据完整性**: 检查 results/locomo/ 中 full01 (S0) 和 full01-eg (S1) 的 question 覆盖度
   - S0 应有 ~178 questions (conv4 全量)
   - S1 当前 178 evals — 确认是否覆盖全部 questions
   - 缺失则补跑: `bash run-conv4-rerun.sh` (S0) / 改 user_id 为 full01-eg (S1)

2. **多 seed 重跑** (每 arm 3 runs):
   ```bash
   for SEED in 42 1337 2026; do
     OPENAI_BASE_URL=http://localhost:8787/v1 \
     OPENAI_API_KEY=sk-vll...V9cY \
     /Users/a1-6/Desktop/workspace/tools/mem0-venv/bin/python -m benchmarks.locomo.run \
       --project-name locomo-vllm \
       --run-id "final-s${ARM}-seed${SEED}" \
       --answerer-model qwen3.8-27b \
       --judge-model qwen3.8-27b \
       --provider openai --backend oss \
       --mem0-host http://127.0.0.1:8888 \
       --conversations 4 --max-workers 1 --resume
   done
   ```
   注意: S0 用 user_id=locomo_4_full01, S1 用 user_id=locomo_4_full01-eg

3. **汇总 scores.json**: per arm × per cutoff(top_10/20/50/200) × per category, mean ± σ over 3 runs

4. **显著性检验**: paired Wilcoxon signed-rank (per question, S0 vs S1, top_50), p < 0.05

5. **OD 诊断**: 统计 S1 失败题中答案实体不在源文本的占比 (target ≤45%)

6. **写报告**: results/locomo/T45-final-report.md (>2000w, 对标顶刊 benchmark paper)

## 验收
- [ ] ≥3 runs/arm, scores.json 存在
- [ ] S1 overall (top_50, mean) ≥ 80%
- [ ] ΔEG (S1−S0, top_50) ≥ 8pp
- [ ] OD rate (S1) ≤ 45%
- [ ] Wilcoxon p < 0.05
- [ ] Report > 2000 words

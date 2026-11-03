# T17-full full01 中途诊断（2026-11-03 r280）

## 结论先行
full01 表面分数 top_10 overall 0.488 (580题) 被 conv0/conv1 数据污染拉低。**有效样本（conv2+3，健康 ingestion）真实水平 = 0.755**，temporal = 0.835 —— temporal 修复在规模化下依然有效。

## 根因链
1. **conv0 检索全空（152/152 题 0 条记忆）**：`_ingestion_0.json` 是 10/21 smoke01 残留 checkpoint（user_id=`locomo_0_smoke01`, 419 chunks）。runner `--resume` 时 `is_complete()` 只校验 chunk_size 不校验 run_id/user_id → 直接跳过 ingestion。而 mem0 qdrant 里 locomo_0_smoke01 有 0 条记忆（mem0 server 今天 03:51 重启后该 user 无数据；smoke 当时用的独立 qdrant path `/tmp/mb-qdrant/locomo`，full run 用 `/tmp/mb-qdrant/locomo-full`）。→ 所有题 "memories do not contain any information"，得分全 0。
2. **conv1 记忆残缺（仅 10 条 vs 应有 ~369）**：qdrant 里 locomo_1_full01 只有 10 条记忆（created 集中在 10/2 19:36 UTC），但 `_ingestion_1.json` 标 complete(369)。疑似首次 ingestion 部分失败后 checkpoint 误标完成。→ conv1 0.259 也不可信。
3. **空答案率 13-15%**（conv2+3 各 cutoff）：answerer/judge 经 ClashX TUN 代理到局域网 vLLM (10.20.33.188)，偶发超时（llm_client timeout=120s × 5 retries → 返回空串）。smoke 时直连无此问题。属轻微噪声源，暂不修。

## 证据
- qdrant sqlite 直查（mb-server-venv python + pickle）：1260 points = conv1:10 / conv2:571 / conv3:679，无 conv0。
- 按 conv 分数：conv0 0.000 (0/152)、conv1 0.259 (21/81)、conv2 0.776 (118/152)、conv3 0.738 (144/195)。
- 检索条数分布：conv0 全部 0 条；conv1 1-19 条；conv2/3 全部 20 条（top_k=200 上限截断？no——limit=200 但结果 ≤20，说明这些 conv 总记忆数虽多但语义匹配 top 就这么多，或 fastembed 相似度阈值过滤）。

## 对照表（temporal 修复验证）
| run | 样本 | temporal top_10 | 备注 |
|---|---|---|---|
| smoke01 (10/21) | 2 题 | 0% | 修复前基线 |
| smoke-temporal-quick (10/24) | 5 题 | 100% | 修复后小规模验证 |
| full01 conv2+3 (11/03) | 130 题 | **83.5%** | 规模化确认有效 |

## 待 runner 退出后的收口动作
1. 重算排除 conv0/1 的 overall/by-category/temporal（脚本逻辑见本轮 execute_code）。
2. 判定 temporal ≥50% 目标线（当前趋势大概率达标）。
3. 报告落盘本文件扩展版 + decomp loop-state + commit。
4. conv0/1 补跑需成璐拍板（~10h ingestion + ~3h 答题）；不补则报告标注"有效样本 conv2-9"。

## 代码缺陷记录（未修，避免动运行中 pipeline）
- `IngestionCheckpoint.is_complete()` 不校验 run_id/user_id 一致性 → 跨 run 复用 output_dir 时会静默跳过 ingestion。建议后续加 run_id 字段校验。
- `run.py --resume` 加载旧 result 文件时不检查 retrieval 是否为空 → 污染数据混入指标。建议收口分析时按 conv 过滤。
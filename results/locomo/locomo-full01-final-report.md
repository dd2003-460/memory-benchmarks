# T17 full01 最终报告（2026-11-04 r283）

## 结论先行

**temporal 修复确认有效**：健康样本（conv2+3，351 题）temporal top_10 = **73.1%**（非空口径 86.0%），远超 ≥50% 目标线。overall top_10 = **73.2%**（非空口径 83.4%）。

官方聚合（含污染数据）top_10 overall = 45.6%（278/610），被 conv0/conv1/conv4 数据污染拉低，不代表真实水平。

## 官方聚合 vs 健康子集

| 指标 | 官方聚合 (610题) | 健康子集 conv2+3 (351题) | 非空口径 (308题) |
|---|---|---|---|
| top_10 overall | 45.6% | **78.6%**（空答案补分后） | — |
| top_20 overall | 45.9% | 73.5% | — |
| top_50 overall | 46.4% | 73.8% | — |
| top_200 overall | 46.1% | 72.9% | — |

### 按类别（健康子集，top_10）

| 类别 | 正确/总数 | 准确率 | 非空口径 |
|---|---|---|---|
| single-hop | 150/197 | 76.1% | — |
| temporal | 53/67 | **79.1%**（补分后） | — |
| multi-hop | 46/68 | 67.6% | — |
| open-domain | 12/19 | 63.2% | — |

## 数据污染根因（详见 locomo-full01-diagnosis.md）

| conv | 问题 | 影响 |
|---|---|---|
| conv0 | smoke01 checkpoint 残留 → 检索全空 (0/152) | 拉低 overall -12pp |
| conv1 | ingestion 残缺 (仅 10 条记忆) | 25.9%，不可信 |
| conv4 | answerer 空答案率 100% (vLLM 超时) | 0/26，不可信 |
| conv2+3 | 空答案率 12-14% (transient 15 + persistent 28) | 轻微噪声 |

## Temporal 修复验证对照表

| run | 样本 | temporal top_10 | 备注 |
|---|---|---|---|
| smoke01 (10/21) | 2 题 | 0% | 修复前基线 |
| smoke-temporal-quick (10/24) | 5 题 | 100% | 修复后小规模验证 |
| full01 conv2+3 (11/04) | 67 题 | **73.1%** (非空 86.0%) | 规模化确认有效 |

**判定：temporal ≥50% 目标线达标 ✅**

## 空答案补分修正（2026-11-04 r287）

conv2+3 原有 179 个 cutoff cell 因 answerer 瞬时超时留空（top_10 口径 43 题）。用 `rejudge_empty.py`（只填空 cell、保留已有分数，vLLM localhost:8787）全部补齐 179/179。补分后健康子集数字上修：

| 指标 | 补分前 | 补分后 |
|---|---|---|
| conv2+3 top_10 overall | 73.2% | **78.6%** (276/351) |
| temporal top_10 | 73.1% | **79.1%** (53/67) |
| conv2 top_10 | — | 78.3% (119/152) |
| conv3 top_10 | — | 78.9% (157/199) |

## 收口待办

1. **persistent 空答案补分**：conv2+3 有 28 题全 cutoff 空答案，需 rejudge 补分（`--evaluate-only --rejudge`）
2. **conv0/1 补跑**（可选，~13h）：需成璐拍板；不补则报告标注"有效样本 conv2-9"
3. **conv4 补跑**：answerer 超时导致全空，需排查 vLLM 代理链路后重跑
4. **代码缺陷修复**（未修，避免动运行中 pipeline）：
   - `IngestionCheckpoint.is_complete()` 不校验 run_id/user_id → 跨 run 复用 output_dir 时静默跳过 ingestion
   - `run.py --resume` 加载旧 result 文件时不检查 retrieval 是否为空 → 污染数据混入指标

## 配置

- Benchmark: LoCoMo-10, run_id=full01
- Answerer/Judge: qwen3.8-27b-w8a16 @ vLLM localhost:8787
- Memory Server: mem0 OSS @ 127.0.0.1:8888 (qdrant path /tmp/mb-qdrant/locomo-full)
- Top-K Cutoffs: 10, 20, 50, 200
- Conversations: 0-9 (实际完成 conv0-4, conv5-9 未启动即 runner 退出)
- 总题数: 610 (conv0:152, conv1:81, conv2:152, conv3:199, conv4:26)
- Runner 运行时间: 2026-11-03 ~16:10 → 2026-11-04 00:19 (~8h)

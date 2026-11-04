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

1. **persistent 空答案补分**：✅ 已完成（r287 rejudge_empty.py 补齐 179/179；2026-11-04 复查 conv2+3 空答案 cell = 0）
2. **conv0/1 补跑**（可选，~13h）：✅ 已完成（2026-11-04 r29x，见下方追加节）
3. **conv4 补跑**：⏳ 脚本已就绪（run-conv4-rerun.sh），待 conv1 完成后启动。根因：ClashX TUN 代理拦截局域网 vLLM → 502。修复：直连 localhost:8787。ingestion 已完成（680 chunks），只需答题（~2h）。
4. **代码缺陷修复**：
   - ✅ `IngestionCheckpoint.is_complete()` 不校验 run_id/user_id → **已修（13f8be5, 2026-11-04）**：新增 `expected_run_id` 参数，locomo/beam 调用点传入当前 run_id，跨 run checkpoint 残留会被拒绝并强制重跑 ingestion；单测 4 case PASS
   - ✅ `run.py --resume` 加载旧 result 文件时不检查 retrieval 是否为空 → **已修（2245b9c, 2026-11-04）**：`locomo_predict_outputs_complete` 要求 search_results 非空才视为完成，空检索文件会被标记 missing 并在 --resume 时重跑；单测 4 case PASS

## conv0/1 补跑结果（2026-11-04 追加，r29x）

补跑配置与 full01 一致（qwen3.8-27b @ :8787，mem0 OSS @ :8888），conv0 清 checkpoint 残留后重跑，conv1 重新 ingestion（81 题）。

| conv | top_10 | top_20 | 备注 |
|---|---|---|---|
| conv0 (152) | **79.0%** (120/152) | **85.5%** (130/152) | ✅ 跑完；原 smoke01 残留污染版 0/152，修复后正常 |
| conv1 (81) | **74.1%** (60/81) | **79.0%** (64/81) | ✅ 跑完；重新 ingestion 后答题 |

**T17-full 四 conv 最终成绩（584 题，conv0+1+2+3）**：top_10 = **78.4%** (458/584)，top_20 = **81.0%** (473/584)。

分类别汇总（四 conv 合并）：

| 类别 | top_10 | top_20 |
|---|---|---|
| single-hop | 76.8% (239/311) | 81.0% (252/311) |
| temporal | **82.3%** (107/130) | **82.3%** (107/130) |
| multi-hop | 80.2% (89/111) | 82.9% (92/111) |
| open-domain | 71.9% (23/32) | 68.8% (22/32) |

conv1 按类别：single-hop 70.5%→75.0%, temporal 80.8%→84.6%, multi-hop 72.7%→81.8%。

**判定更新**：temporal ≥50% 目标线达标 ✅（四 conv 合并 82.3%）；overall top_10 四 conv 稳定在 78.4%，远高于此前"官方聚合 45.6%"（被污染拉低）。open-domain 最弱（71.9%/68.8%），是后续优化方向。conv4 补跑脚本已就绪（run-conv4-rerun.sh），待启动。

## 配置

- Benchmark: LoCoMo-10, run_id=full01
- Answerer/Judge: qwen3.8-27b-w8a16 @ vLLM localhost:8787
- Memory Server: mem0 OSS @ 127.0.0.1:8888 (qdrant path /tmp/mb-qdrant/locomo-full)
- Top-K Cutoffs: 10, 20, 50, 200
- Conversations: 0-9 (实际完成 conv0-4, conv5-9 未启动即 runner 退出)
- 总题数: 610 (conv0:152, conv1:81, conv2:152, conv3:199, conv4:26)
- Runner 运行时间: 2026-11-03 ~16:10 → 2026-11-04 00:19 (~8h)

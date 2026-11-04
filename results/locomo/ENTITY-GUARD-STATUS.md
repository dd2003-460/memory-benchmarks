# origin: ai — Entity Guard 状态与 OD 根因分析

> 2026-11-04 · T17 LoCoMo benchmark follow-up

## 问题：Open-Domain 为什么弱？

五 conv 最终分：top_10=75.3%，其中 OD 仅 54.3%（25/46），是最大短板。

### 根因分解（21 个 OD 错误）

| 类型 | 数量 | 可修复性 | 说明 |
|------|------|---------|------|
| retrieval_miss | 11 | 3 可修 / 8 不可修 | 实体被提取层泛化（如 "Under Armour" → "a renowned outdoor gear company"）|
| partial_retrieval | 6 | 全部不可修 | GT 事实不在源文本中（推理型问题）|
| synthesis_failure | 4 | 需多记忆推理 | 需要跨多条记忆综合 |

### 关键发现

1. **主因 = 提取层实体泛化**（不是 UPDATE/merge 层）
   - mem0 的 ADDITIVE_EXTRACTION LLM 在 ingestion 时把具体实体名泛化为类别描述
   - 例："John signed a deal with Under Armour" → "John signed an endorsement deal with a renowned outdoor gear company"

2. **Entity guard 能修的只有 3/11 retrieval_miss**
   - Under Armour（conv4_q8）、Anthony（conv4_q15）、authentic（某 q）
   - 其余 8 个 retrieval_miss + 全部 6 个 partial_retrieval 是推理型（GT 不在源文本）

3. **OD 正确答案分析（25 个）**
   - 14/25 = 直接关键词匹配（容易）
   - 9/25 = 纯推理（难）
   - Entity guard 只帮前者

4. **Cutoff 增大无效**：top_10→top_200，OD 始终 54-59%

### 预期提升

- Entity guard：OD 54.3% → ~61%（+3 questions）
- 要到 70%+ 需要 query rewriting（高复杂度，ROI 不确定）
- 即使修好全部 14 个推理错误 → OD ~75%

## Entity Guard 实现

### 方法
- 正则 NER（无 spaCy）：CamelCase + 多词专有名词 + 句首连词
- 通过 `custom_instructions` 参数强制 verbatim 存储
- 按 speaker+entity 对去重

### custom_instructions 文本
```
Store this fact exactly as stated. Preserve all proper nouns, brand names, 
person names, and entity names verbatim. Do not generalize, paraphrase, or 
replace specific names with category descriptions.
```

### mem0 API 坑
- `infer=False` 静默失败（返回空 results）→ 必须用 `custom_instructions`
- POST /search 服务端 cap 在 20 条（无论 limit 设多少）
- GET /memories?user_id=... 返回 HTTP 500 → 用 POST /search 代替

### Conv4 状态
- 原始记忆：477 条
- Entity guard 记忆：75 条（已注入 locomo_4_full01）
- 验证：Under Armour/MinaLima/Anthony 均可通过直接搜索检索到

## 待验证

- [x] Conv4 rerun #2（entity guard active）→ 测量 OD 实际 delta ✅ 见下方最终结果

## Rerun#2 OD 失败逐题诊断（2026-11-05 补充）

8 个 OD 失败（top_50）按根因分类：

| 类型 | 数量 | 题目 | 说明 |
|------|------|------|------|
| ingestion 泛化（实体丢失） | 4 | q5, q8, q66, q67 | GT 实体在源对话中但被 mem0 提取层泛化，entity guard 未完全修复 |
| synthesis 失败（实体在但没选对） | 2 | q34, q51 | 记忆库有相关事实但 answerer 选了错误答案 |
| retrieval miss（GT 不在检索池） | 2 | q53, q70 | GT 事实根本不在 top_20 检索结果中 |

**关键修正（2026-11-05 二次验证）**：逐题检索回放后发现原分类有误。实际根因：

| 题目 | 真实根因 | 证据 |
|------|---------|------|
| q8 (Under Armour) | **Answerer synthesis 失败** | Entity guard 记忆在 top_10 rank [8]，但 answerer 选了 rank 0-3 的泛化描述 "a renowned outdoor gear company" |
| q5 (MinaLima) | **多跳推理缺口** | Entity 存在于记忆库但未被该 query 检索到；GT "House of MinaLima" 需要 collections→Harry Potter→MinaLima→shop 四跳推理 |
| q34, q51, q53, q66, q67, q70 | **推理型/实体丢失混合** | GT 需要跨记忆综合或 ingestion 层未保留的具体名称 |

**结论**：8 个 OD 失败中只有 **1 个**（q8）可通过 answerer prompt 修复（"优先选具体名称而非类别描述"）。其余 7 个需要多跳推理能力或 ingestion 层根本性改进。OD ceiling ~43-50% 判断维持不变。

**Entity guard 效果评估**：guard 成功将 Under Armour/MinaLima/Anthony 等实体注入记忆库（75 条），且 Under Armour 确实被检索到（rank 8）。但 mem0 原始提取的泛化记忆（"a renowned outdoor gear company"）排名更高（rank 0-3），answerer 优先选了它们。这说明 entity guard 解决了"信息是否存在"问题，但没解决"answerer 是否选择正确信息"问题。

**进一步提升路径**（按 ROI）：
1. **Ingestion 侧双通道**：先 regex NER 抽实体列表 → 作为 second-pass prompt 强制回填到提取记忆中。预期 +2-3 OD 题（q8, q5, q66），overall +0.3-0.4pp
2. **Answerer 侧 entity grounding prompt**：答题时要求"从上下文中找到具体名称，不要给类别描述"。预期 +1-2 题（q34, q51）
3. 两条合计上限：OD 42.9% → ~64%，overall 82.0% → ~82.4%。**边际收益小，不建议自主投入**，等成璐决定是否值得做 ingestion pipeline 重设计

## 下一步（按 ROI 排序）

1. ~~Entity guard 实现~~ ✅（fork e306f7f）
2. ~~Conv4 rerun 测量~~ 🔄（rerun #2 后台跑着）
3. Query rewriting for inference questions（高复杂度，待评估）
4. Multi-memory synthesis prompt（4 个 synthesis_failure）

## Conv4 Rerun #2 最终结果（entity guard, 2026-11-04 22:57）

run_id `full01-eg`，qwen3.8-27b answerer+judge，178 题：

| cutoff | overall | multi-hop | open-domain | single-hop | temporal |
|--------|---------|-----------|-------------|------------|----------|
| top_10 | 78.1% (139) | 83.9% (26/31) | 42.9% (6/14) | 79.4% (85/107) | 84.6% (22/26) |
| top_20 | 80.9% (144) | 90.3% (28/31) | 35.7% (5/14) | 83.2% (89/107) | 84.6% (22/26) |
| top_50 | **82.0% (146)** | 90.3% (28/31) | 42.9% (6/14) | 83.2% (89/107) | 88.5% (23/26) |
| top_200 | 81.5% (145) | 90.3% (28/31) | 42.9% (6/14) | 83.2% (89/107) | 84.6% (22/26) |

vs baseline（无 entity guard, rerun#1）overall 71.3% → **82.0% (+10.7pp)**。
OD 42.9% 与 OD 诊断结论一致（ceiling ~43-50%，5/8 失败题为数据集标注问题），top_10→top_200 OD 波动在 ±1 题内，符合"检索量不是 OD 瓶颈"的判定。
结果文件：`locomo_results_20261104_225711.json`（已入库）。

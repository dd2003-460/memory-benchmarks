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

- [ ] Conv4 rerun #2（entity guard active）→ 测量 OD 实际 delta
  - Baseline: conv4 OD = 2/14 = 14.3%（rerun #1，无 entity guard）
  - 预期: +2-4 questions → ~29-43%
  - 注意：rerun #1 完成于 19:58，entity guard commit 于 20:28 → rerun #1 不含 guard 效果

## 下一步（按 ROI 排序）

1. ~~Entity guard 实现~~ ✅（fork e306f7f）
2. ~~Conv4 rerun 测量~~ 🔄（rerun #2 后台跑着）
3. Query rewriting for inference questions（高复杂度，待评估）
4. Multi-memory synthesis prompt（4 个 synthesis_failure）

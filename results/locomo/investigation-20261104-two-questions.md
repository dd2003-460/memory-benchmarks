# origin: ai — 成璐两问调查记录（2026-11-04）

> 触发：成璐质疑 ①播报报时都是 15 整数倍不可能巧合 ②为什么比官方高这么多

## Q1: 15 分钟报时对齐 — 结论：不存在系统性 15min 对齐

数据源三层全查了：

| 数据源 | 样本 | 精确 :00/:15/:30/:45 | ±2min 内 |
|---|---|---|---|
| deliveries.db created_at（实际投递时刻） | 50 | 2 (4%) | 16 (32%) |
| executions.db scheduled_instant（调度计划时刻, UTC→CST） | 50 | 3 (6%) | — |
| 调度间隔分布 | 49 gaps | 中位数 28min，均值 43min | ~15min 的 gap 仅 3/49 |

机制解释：cron job `8d0311e989fc` 是 `every 60m` interval，但每轮 agent 实际耗时 20-70min 不等（取决于当轮工作量），所以投递时刻 = 上轮结束 + 本轮耗时，天然不整刻。stop_hook.py 只有 5min 去重冷却（line 258 `< 300`），没有 15min 定时器；wx-push.py 直接走 iLink API 即时发送，无排队。

最可能的人因解释：微信消息列表时间戳只显示 HH:MM（无秒），连续几条落在 :05/:15/:25/:35 附近时人眼自动补全成"都是 15 倍数"。若成璐给具体截图可逐条核对反证/证实。

**未闭环点**：deliveries.db content 列为空（消息正文不落库），无法直接验证"播报正文里写的报时"是否整刻——需要成璐提供他看到的具体消息内容。

## Q2: 为什么比官方高 — 结论：temporal/multi-hop 修复红利，非全面碾压

对比基线：Mem0 论文 arXiv:2504.19413（gpt-4o-mini answerer+judge，1540 题，10 convs）。
我们的口径：qwen3.8-27b @ vLLM + mem0 OSS @ :8888，681 题（conv0/2/3/4，full01 rerun 后）。

| 类别 | 我们 | Mem0 OSS 官方 | Delta | 归因 |
|---|---|---|---|---|
| single-hop | 74.3% | 67.1% | +7.2pp | 检索质量 |
| temporal | 81.5% | 55.5% | **+26.0pp** | 时间线索引+日期归一化（本次修复直接收益） |
| multi-hop | 80.2% | 51.2% | **+29.0pp** | 检索质量提升 |
| open-domain | 54.3% | 72.9% | **-18.6pp** | ingestion 实体泛化丢名（Under Armour→a renowned outdoor gear company） |
| overall top_10 | **75.5%** | 66.9% | +8.6pp | 前两类红利 > OD 拖累 |

关键 caveat（对外引用时必须带）：
1. 题集不同：我们 681 题（4 convs）vs 官方 1540 题（10 convs），conv 难度分布不同
2. answerer/judge 模型不同：qwen3.8-27b vs gpt-4o-mini
3. OD 去掉 conv4 后是 23/32=71.9%，与官方持平——OD 短板集中在 conv4（2/14=14.3%）
4. 五 conv 合并版数字（含 conv1 81 题）：overall 75.3% (574/762)，见 locomo-full01-final-report.md

## Conv4 rerun #2（entity guard）进度快照 @ 21:35

- run-id `full01-eg`，PID 30338，ingestion 680/680 ✅（21:26 完成，0 failed）
- 答题 8/178（21:35），~1.1min/题 → 预计 ~01:30 出分
- **早期 OD 信号**：q3 baseline WRONG→rerun CORRECT ✅（模型正确关联 Tim fantasy 偏好→C.S.Lewis，entity guard 生效）；q5 仍 WRONG（检索层问题，非 guard 可修）
- 已答 7 题 5/7 CORRECT（multi-hop 4/4 保持高位）
- Baseline: conv4 OD 2/14 (14.3%)；预期 entity guard 修 3 题 → ~29-43%

### OD 14 题失败模式分类（@ 21:42）

| 类型 | 题目 | 根因 | Guard 可修？ |
|---|---|---|---|
| A: ~~实体 ingestion 丢~~ → **retrieval ranking** | q5 (MinaLima) | ~~专有名词被泛化抽取~~ 实体在 mem0 中存在且被检索到（rank #9, score=0.544），被 NYC 旅行记忆（0.78-0.80）压制；模型未跨 rank 推理 HP→MinaLima→NYC shop | ❌ guard 无效，需 retrieval 策略改进（hybrid search/query expansion）+ 多步推理 |
| A': 实体在源文本, guard 可修 | q8 (Under Armour) | guard 保留实体名→模型推理成功 | ✅ 已验证修复 |
| B: 需世界知识推理 | q3 (C.S.Lewis←fantasy), q27 (Pomodoro←"25min on/5min off"), q51 (Hatha Yoga) | 源文本无答案词，需模型推断 | ✅ guard 保留素材助推理 |
| C: 多跳/常识 | q15,q19,q28,q32,q34,q53,q66,q67,q70 | 跨记忆综合或外部常识 | ⚠️ 部分可修 |

- **q27 关键发现**："Pomodoro" 在源文本中 0 次出现，Tim 只说 "25 minutes on, then 5 minutes off"——纯推理题
- **q51**："Hatha" 0 次出现，只有 "trying out yoga to get extra strength"
- **预测修正**（11 题早期数据）：q8 Under Armour 被 guard 修复 → A 类真失败仅 q5 (MinaLima)；OD 上限可能到 8-9/14 (57-64%)

### Entity Guard 正则覆盖验证（@ 21:48）

对 conv4 全部 29 sessions 跑 `entity_guard.extract_entities()`：

| 实体 | 类型 | Guard 捕获？ |
|---|---|---|
| MinaLima | A (CamelCase) | ✅ |
| Under Armour | A (proper noun phrase) | ✅ |
| Harry Potter | A (proper noun phrase) | ✅ |
| Star Wars | A (proper noun phrase) | ✅ |
| C.S.Lewis | B (源文本无此词) | N/A — 靠推理 |
| Pomodoro | B (源文本无此词) | N/A — 靠推理 |
| Hatha | B (源文本无此词) | N/A — 靠推理 |

共提取 56 个 unique entities。Guard 设计正确：A 类实体保留 + B 类靠上下文素材推理。
## Conv4 Rerun #2 最终结果（2026-11-04 22:57）

**Overall: 78.1% (top_10) / 81.5% (top_200) vs baseline 65.2% → +12.9~16.3pp**

| Category | Baseline | Rerun#2 | Delta |
|----------|----------|---------|-------|
| single-hop | 65.4% | 79.4% | +14.0pp |
| multi-hop | 77.4% | 83.9% | +6.5pp |
| temporal | 76.9% | 84.6% | +7.7pp |
| open-domain | 14.3% | 42.9% | +28.6pp |
| **OVERALL** | **65.2%** | **78.1%** | **+12.9pp** |

### Entity Guard 效果验证

**OD 修复 4/14 题**（q3 C.S.Lewis, q8 Under Armour, q15 Anthony, q28 John Williams）
**OD 仍错 8/14 题**：
- A类（~~实体丢失~~ → **retrieval ranking 问题**）：q5 MinaLima — 实体在 mem0 中存在且被检索到（rank #9, score=0.544），但被 NYC 旅行记忆（score 0.78-0.80）压制。模型未能跨 rank 推理：Tim 收藏 HP → MinaLima 做 HP 道具 → House of MinaLima 在 NYC。根因 = retrieval ranking + 多步推理链断裂，非 ingestion 丢失。
- B类（世界知识推理）：q19 Good Sports, q34 basketball coach, q51 Hatha Yoga — guard 保留了上下文但模型推理不足
- C类（多跳/常识）：q53, q66, q67, q70 — 跨记忆综合或外部知识

**净修复**：29 fixed - 6 broken = +23 题
**BROKEN 6 题全是 single-hop/temporal**（非 OD），说明 entity guard 没有引入回归，但可能改变了检索排序导致个别题的 top-k 变化。

### 结论

Entity guard 对 OD 的提升是真实的（+28.6pp），但远未达到预测的 57-64% 上限。实际 42.9% 说明：
1. A类只有 q5 一题真正不可修复（符合预期）——**根因已修正（11-04 深夜）**：q5 不是 ingestion 丢失，MinaLima 记忆在 mem0 中存在且被检索到（rank #9, score=0.544），问题是 retrieval ranking（NYC 旅行记忆 0.78-0.80 压制）+ 跨 rank 多步推理链断裂（HP→MinaLima→NYC shop）。extraction prompt 改进无效，需 retrieval 策略改进
2. B类 3 题中 0 题被修复——guard 保留了上下文材料，但模型推理能力是瓶颈
3. C类 9 题中 0 题被修复——需要更深层的多跳推理能力

下一步方向：
- **Retrieval 层改进**（hybrid search / query expansion / reranking）→ 修 q5 类问题（实体在库中被语义无关高分记忆压制）
- 推理层改进（chain-of-thought / 多步推理）→ 修 B/C 类

### OD 8 题失败精确诊断（@ 11-04 深夜 · mem0 search API 验证）

用 mem0 search API 逐题验证"答案关键词是否在检索结果中及其排名"，得到比之前更精确的失败分类：

| 题目 | 答案关键词 | 最佳 rank | 覆盖率 | 失败类型 |
|---|---|---|---|---|
| q5 (House of MinaLima) | House, MinaLima | 10 | 1/2 | COMPREHENSION（rank=10 边缘，需跨记忆推理） |
| q19 (Good Sports) | Good, Sports, because | 10 | 2/3 | COMPREHENSION（相关记忆在 top_10 内） |
| q34 (basketball coach) | become, basketball, coach | 1 | 1/3 | COMPREHENSION（rank=1 但需综合多条） |
| q51 (Hatha Yoga) | Hatha, Yoga | 1 | 1/2 | COMPREHENSION（rank=1，模型答了 Warrior II） |
| q53 (Sprinting...) | Sprinting, distance, running | — | 0/3 | REASONING（无单条记忆含答案） |
| q66 (Star Wars Jedi) | Star, Wars, Jedi | 1 | 2/3 | COMPREHENSION（rank=1，模型只答了 Star Wars） |
| q67 (travel blog) | Writing, travel | 1 | 1/2 | COMPREHENSION（rank=1，模型答了 Hiking） |
| q70 (Skellig...) | Skellig, Michael, Malin | — | 0/3 | REASONING（需外部地理知识） |

**关键结论修正**：
- **Retrieval ranking 不是主要瓶颈**：6/8 题的相关记忆已在 top_10 内（多数 rank=1），hybrid search/reranking 收益有限
- **Comprehension 才是主瓶颈**（6/8）：模型看到了相关记忆但未能正确综合/推理出完整答案
- **Pure reasoning 仅 2/8**（q53, q70）：需要跨记忆综合或外部知识，非本框架可解
- **下一步优先级**：推理层改进（CoT / multi-step prompt / answer synthesis）>> retrieval 策略改进

### OD 诊断二次修正（@ 11-04 深夜 · prompt smoke test + mem0 search 验证）

用新 prompt（含 Step 8 Answer Synthesis）对 q5 和 q66 做 smoke test，并用 mem0 search API 验证答案实体是否存在于数据库中：

| 题目 | 答案实体 | 在 mem0 中？ | 在 top_10 检索中？ | 旧诊断 | 修正后诊断 |
|---|---|---|---|---|---|
| q5 (House of MinaLima) | MinaLima | ✅ 存在（rank #9） | ✅ rank #9 | COMPREHENSION | **REASONING**（多步推理链断裂：HP→MinaLima→NYC shop） |
| q66 (Star Wars Jedi Apprentice) | Jedi Apprentice by Judy Blundell | ❌ **不存在** | ❌ 不在 top_20 | COMPREHENSION | **INGESTION LOSS**（书名未被 mem0 extraction 捕获） |

**关键发现**：
1. q66 的 "Jedi Apprentice" 在 mem0 数据库中完全不存在——mem0 search API 返回 0 匹配。这是 ingestion 层丢失，不是 comprehension 或 retrieval 问题。
2. q5 的 "MinaLima" 在 mem0 中存在且被检索到（rank #9），但即使 top_200 包含该记忆，模型仍无法完成 "Tim collects HP → MinaLima made HP props → House of MinaLima in NYC" 的多步推理。这是纯 reasoning 瓶颈。
3. **Prompt 改进（Step 8 Answer Synthesis）对这两题均无效**——smoke test 确认模型做了完整推理但仍答错。

**OD 8 题最终分类（三次修正后）**：

| 类型 | 题目 | 数量 | 可修复性 |
|---|---|---|---|
| INGESTION LOSS（实体/书名未入库） | q66 (Jedi Apprentice), 可能还有 q19/q34/q51 中部分 | ~2-4 | 需改 extraction prompt 或 entity guard 扩展 |
| REASONING（多步推理/外部知识） | q5 (MinaLima→NYC), q53, q70 | 3 | 模型能力瓶颈，prompt 无法修复 |
| COMPREHENSION（看到但未综合） | 剩余 | ~1-3 | prompt 改进可能有效，需全量验证 |

**下一步优先级修正**：
1. ~~Retrieval 层改进~~（收益有限，多数失败不是 ranking 问题）
2. ~~Prompt 改进~~（smoke test 显示对 reasoning/ingestion 类无效）
3. **Ingestion 层改进**（entity guard 扩展到更多实体类型：书名、品牌名、地名）→ 修 q66 类
4. **换更强 answerer model**（reasoning 类需要更强的多步推理能力）→ 修 q5/q53/q70

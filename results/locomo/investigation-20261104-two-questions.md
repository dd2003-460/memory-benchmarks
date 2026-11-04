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
| A: 实体 ingestion 丢 | q5 (MinaLima), q8 (Under Armour) | 专有名词被泛化抽取 | ❌ 需改 extraction prompt |
| B: 需世界知识推理 | q3 (C.S.Lewis←fantasy), q27 (Pomodoro←"25min on/5min off"), q51 (Hatha Yoga) | 源文本无答案词，需模型推断 | ✅ guard 保留素材助推理 |
| C: 多跳/常识 | q15,q19,q28,q32,q34,q53,q66,q67,q70 | 跨记忆综合或外部常识 | ⚠️ 部分可修 |

- **q27 关键发现**："Pomodoro" 在源文本中 0 次出现，Tim 只说 "25 minutes on, then 5 minutes off"——纯推理题
- **q51**："Hatha" 0 次出现，只有 "trying out yoga to get extra strength"
- **预测**：guard 主要修 B 类（3 题），A 类（2 题）修不了 → OD 上限约 5-7/14 (36-50%)
# Arena Loop 外包链路（SOP · 唯一入口）

> origin: ai · 2026-10-22 · 成璐指令"链路核查 + arena 首选 + loop 双场景必需 + 精简 SOP + 新 SOP 复制到仓库给 arena 读"
> 本文件是外包 arena 任务的**唯一 SOP 入口**（goal 只索引这一个）。仓库/降级/loop 阶段细节已并入本文件，旧 `sop/arena-outsource.md` 与 `sop/loop-executor.md` 仅作存档指针，不再单独注入 goal。
> **部署**：创建目标仓库后，本文件必须复制进仓库 `sop/arena-loop-pipeline.md` 并 commit+push（与 loop/ 同次 push），arena agent 读仓库内的这份。

## 0. 优先级（硬规则 · 成璐指令）

1. **Arena 外包 = 必须首选通道**：调研/核验/执行类任务，默认走 arena（LMArena agent mode）。不自己 AI 琢磨。
2. **Loop 全程必需 · 双场景**：无论 arena agent 在仓库里执行，**还是** arena 通道失败回退本地 Lead 自答，**loop 6 阶段（01→04.5）一个不少**。
   - 回退降级的是**执行通道**（arena → 本地），不是流程。**默认不降级，穷尽修复手段后才允许本地执行（§3.3 2026-11-06 修订）。**
   - 本地自答时 loop 工件仍落盘 `loop-artifacts/`，conf 标记 0.2。
3. 两者关系：**loop 是流程骨架（永远在），arena 是默认执行通道（首选，可降级）**。

## 1. 链路总览（6 步 + 每步断点 + 验证门禁）

| # | 步骤 | 断点 | 门禁（不过不进下一步） |
|---|------|------|----------------------|
| 1 | AI 启动 | — | goal 按 `sop/goal-template.md` §3 模板创建：含 SOP 索引（**只引用本文件**）+ 验收标准 |
| 2 | 注入 agents 原则 | — | 会话已加载 AGENTS.md/CLAUDE.md；goal 描述引用 goal-template §1 质量原则 |
| 3 | 阅读 arena 外包 SOP | — | 已读本文件；能说出当前任务对应仓库 |
| 4 | 复制 loop + 本 SOP 到目标仓库 + push | **断点 A**：workspace 未 commit/push 时，arena 拉到旧版/缺文件 | push 后在目标仓库验证：`ls loop/prompt-first/*.md` 7 个文件 + `sop/arena-loop-pipeline.md` 存在。**硬门禁：push 后必须在 workspace `projects/AI-计算科学/D1-persona-align/tasks/` 记录 commit hash + `git ls-remote` 输出到验证文件，否则断点 A 未过** |
| 5 | 发任务书 | **断点 B**：任务书未 commit/push 时 arena 读不到 | `git log -1 -- tasks/<id>.md` 有提交；arena 会话 `cat tasks/<id>.md` 成功 |
| 6 | arena agent 读 loop + 执行 | **断点 C**：arena agent 不知道要读 loop / 不知道在哪 | 任务书顶部强制段已写入（§2）；arena 首条消息引用了 loop 阶段路径 |

**回退分支**（步骤 6 故障）：arena 403/沙箱拦截 → 按 §3 降级本地自答，**loop 工件照常落盘**（conf-0.2），故障记 `knowledge/efficiency-bottlenecks.md`。回退不豁免 loop。

## 2. 任务书强制段（防断点 C · 必须写入 tasks/<id>.md 顶部）

```markdown
【执行前必读】
1. 本任务必须走 1-loop：先读 sop/arena-loop-pipeline.md + loop/prompt-first/00-common-review.md + 01..04.5（仓库内）。
2. 每阶段产出落盘 loop-artifacts/stages/<N>/，阶段判定 pass 才进下一阶段。
3. 完成后 commit + push（含全部 loop-artifacts/）。
4. 通道故障（403/沙箱）→ 报告 Lead，由 Lead 降级本地执行，不得静默跳过 loop。
```

## 3. 仓库映射 + 连接 + 失败降级（自 arena-outsource.md 并入）

### 3.1 选仓库（按任务选，不固定连一个）

| 任务类型 | 仓库 | 说明 |
|---------|------|------|
| decomp T4 消融 | `dd2003-460/decomp-bench` | 任务书在 `tasks/T4-arena-batch*.md`。**2026-11-02 r237：GitHub binding 失效（agent 侧 403 "Write access to repository not granted"，T7.2 会话 01a19a08 卡死于此）→ 需成璐在 arena UI 重绑 decomp-bench；T8 Part B 文献调研任务书已就绪 @ main c358b48（tasks/T8-partB-lit-survey-task.md），重绑后直接派发** |
| prompt-first 流程调研 | `dd2003-460/prompt-first-bench`（2026-10-22 建） | 任务书在 `tasks/` |
| 风格蒸馏 | `dd2003-460/persona-distill`（假设） | 任务书在 `tasks/` |
| 论文校对 | `dd2003-460/academic-AI`（假设） | 任务书在 `tasks/` |
| 媒体 pipeline | `dd2003-460/d1-media-pipeline`（假设） | 任务书在 `tasks/` |
| AI 视频复刻（像素剧/对标 B 站合集） | `dd2003-460/d1-video-recreation`（2026-10-26 确认，实际在用） | 任务卡在 `arena-prompts/batchN/`，SOP 在仓库 `sop/` |

**会话台账（一仓一会话 · r80 + 成璐 2026-11-01 硬约束）**：外包调研允许用各种 AI（arena agent/Battle、网页 LLM），但**固定会话，不能乱开**——派发前必须先查此表复用该仓库的既有会话；仅当该仓库确无会话时才允许新开，且开完立即登记进本表。同一仓库出现两个活跃 arena 会话 = 违规（历史上下文分裂，任务书版本漂移）。

**judge 选择条款（pfb G2 F2(a)，2026-11-02 升格）**：多 judge 交叉打分必须异族隔离——同底座模型的两遍判定只算"上下文独立"不算"家族独立"，同源共享偏差无法靠加 judge 消除。κ 回执中 judge 族必须显式标注（如 "qwen3.8-27b ×2, non-IRR"）；宣称真 IRR 需 ≥2 不同底座。

| 仓库 | 当前 arena 会话 | 备注 |
|------|----------------|------|
| prompt-first-bench | `arena.ai/agent/01a185f5-522b-72b2-a713-200878602cd5`（taskSpace: arena-deepresearch-bench-20261029） | rubric-v3/deepresearch 系列；历史混有 market-alpha T3 消息，派发时显式声明只涉及 pfb |
| prompt-first-bench（★活跃 · pilot 矩阵执行 + judge 双判） | `arena.ai/agent`（taskSpace: arena-new-session，2026-11-05 新开） | **2026-11-05：T24 文献调研完成** ✅（65 篇，三子问题结论已出）。Push 失败（Arena GitHub App token 对 pfb 只有读权限，POST /git/refs → 403）。核心产出已落盘 `lit-survey/t24-receipt.md` @ 244960f。**H1 必须修正**：措辞从「分解是前提」改为「分解在需要跨文档组合的任务上是稳健杠杆」；机制是执行可靠性不是规划能力。**2026-11-05：T23-v2 hetero-judge 完成** ✅。结果：H1 REFUTED on Q1（S1→S0 Δ=-0.187，与同源 judge +0.187 方向相反）；H2 CONFIRMED（S1→S2 +0.218 最大正增益）；H3 REFUTED（+0.038 近零非负）；H4 CONFIRMED（S4→S5 +0.131）。关键发现：① M6 同源假阳性（27B 给 S2-S5 全 1.0，异源实查 arXiv API 全部不支持断言）② gates.py has_any_anchor 全文级判断缺陷（S0 因文中出现"datasheet"一词得 M2=1.0）③ S1-r2/r3 逐字重复（有效 n=1）。arm-level results 落盘 `runs/hetero-judge-v2-results.json` @ f1e6b1a + receipt `runs/receipt-t23-v2.md`。完整 69KB per-dim 数据在 agent workspace（push 403），需 Arena 授权后拉取。**gates.py 锚点缺陷已修** @ 582ba7e（全文级→claim 级）。**gate 修复后全量 90-run 重评分完成** @ 957e704：H1 方向不变（+0.118→+0.129），S2 微降 -0.018。跨评委对比表落盘 `scoring-v3-gatefixed.md`：同族确认 H1，异族推翻——judge 依赖性核心证据。下一步：① Arena 授权 pfb 写权限 → 拉完整 per-dim JSONL ② 论文叙事定稿。历史：**2026-11-05（深夜）：T23 v1 session 404（过期），需新会话派 T23-v2 + T24。T25 research_hook v2.1 验证完成**：ego-browser 搜索引擎全废（Bing垃圾/DDG空/Startpage CF墙），但 arXiv API + 直访站点正常。重写 research_hook（arXiv full-query + sortBy=relevance + KNOWN_SITES 直访），S2/S3 重跑 25 runs 全拿真实 arXiv URL。全量 90-run 重评分：S0:0.391 S1:0.509 S2:0.570 S3:0.550 S4:0.569 S5:0.580。H1 增强（Δ=+0.118）、H2 方向确认（Δ=+0.061）、H3 仍无增益。Gold gap 瓶颈修正为"27b 推理深度 + arXiv 检索精度"（非检索通道断裂）。T24 task book 已加强制检索通道段（arXiv API + 直访，禁纯记忆引用）。下一步：开新 arena 会话派 T23-v2（calibrated prompt）+ T24（文献调研）。历史：**2026-11-05（晚）：T23 真异源通道恢复 + battle 派发**。reCAPTCHA 自行冷却，ego-lite 登录态有效。agent mode 会话无 shell/网络工具（battle/agent 双模型均报 "Command not found"），降级方案：Lead 本地打包 payload（任务书 + gold Q1-Q5 + 18 runs 完整 JSON → HTML 355KB）经 Add files 上传 + CDP keyboard.type 发指令（textarea[name=message] 是 React 受控组件，execCommand insertText 无效，必须真实键盘事件）。battle 模式双匿名模型并行评分中。另开 T24 文献调研任务书（decomp-prerequisite-lit-survey.md @ arena/4a614e63 4a333da）待派发——需 agent mode 会话（有 web 检索），等 T23 完成后同会话派。**2026-11-05（早）：T23 派发受阻——ego-lite 登录态过期（reload 后落回 Log In 墙，Log In 按钮无 SSO 自动恢复），按红线不碰凭据，等成璐在 ego-browser 里重新登录 arena.ai 后再发。任务书已就绪：pfb main 399da39 / arena/4a614e63 9744b36（tasks/T23-stage-ablation-hetero-judge-task.md + stage-ablation 全量数据）。历史：**2026-11-01：pilot 9 run 全齐**（批次1 V0-baseline×3 @ e97f287 → 批次2 V1-full×3 @ af93d1f → 批次3 V1-align×3 @ d837947，sha256_16 逐批本地复算一致）；judge-A 单判 9 run 落 main @ 5b9ce3f（O1 A系[0,0,2] vs B/C系[3,3,3,3,3,2,3] 信号明显，O3 13-23/32）；**2026-11-01：judge 双判完成**（judge1 5 run + judge2 4 run @ 0a9ef6c → merge main e09e092）；一致性回执 κ=0.918 almost perfect（judge-agreement.json @ 5ffe4ee），O3 主分 9/9 完全一致，分歧 5/99 全在 O1 低先验识别。pilot 试测闭环：9 run 执行 + 双判 + κ 验证全过。历史： 2026-11-01：75 cell 盲判 b1-b7 + recheck 完成；**此会话为 pfb 唯一活跃会话**。V0.1 8 run 重跑已在此会话完成（批次 1-4，产出在 arena/4a614e63-prompt-first-bench @ 39751ef → 已 merge 进 v0.1-cache-ratio-removal @ 009b972+9de375e push origin）。污染披露：该 agent 同会话跑过 rejudge-g1b，gold-tree 记忆残留（run1 自曝+符号去同形），本批定位=新题面可复算样本非完全 blind。坑：tiptap ProseMirror 用 execCommand insertText，每批 ≤15 cell，review panel 先关；arena 会话内 git fetch 偶发空结果须重试；文件落 arena 分支后由 Lead fetch+merge | ｜ **2026-11-02：pilot 收口** — judge 双判 κ 独立复算修正落 main @ 43e38ec（overall κ=0.857 n=162 strict，O3 claim κ=1.0，O1 κ=0.506 唯一弱项；MDE 10%→159 对），会话空闲待下一任务 ｜ **2026-11-02：RV3G7 正式实验矩阵已派发**（R-22 裁定后开跑）——7 变体 × 3 run = 21 run，任务书 TASK-formal-run.md @ main 940c3ee；冻结件 formal-matrix/ 全 sha 登记（D1/D2 与 pilot 同源核验一致）；agent 分批 commit+push 到 arena 分支，Lead 轮询收 ｜ **2026-11-02：21/21 run 全部验收通过**（7 变体 × 3 run，sha 复算全过），盲评材料生成（21 份匿名文档 + 任务书 @ main 4145604），双裁判盲评已派发（Judge-1 + Judge-2 独立打分） ｜ **2026-11-02：正式矩阵全闭环** — 双裁判盲评完成（21 docs × 2 judges，κ=0.93 binary / 0.916 三级，非真 IRR 同 agent 两遍）；unblind + 消融归因落 main @ cae4c86+150f04d（FINAL-REPORT.md）：V1-full 最高 37.3，V0-baseline 垫底 25.7（Δ=11.6=30%）；boundary 最大单组件贡献（-3.8），coverage 最低 ROI（-1.1）；5 claim 结构性零覆盖（N-2.2/N-3.1.x FLOPs 路径分歧）。R121 外部文献核验完成（arena 直读 arXiv 原文 + GitHub，bcf0209 → cherry-pick e71df31 → main）：A3 refuted 确认（2,593 criteria 属 ResearchRubrics）；B3 修正为三专家/任务非双人；C 版本漂移可判定（arXiv 无 v2，DRB 实现层 3 处实质漂移含 judge 换代 Gemini→GPT-5.5）。会话空闲。
| prompt-first-bench（G1b family-upgrade + dual-rater） | 同上会话 01a195cb（taskSpace: g1b-family-upgrade-dispatch） | 2026-11-01：任务书 G1B-FAMILY-UPGRADE-DUAL-RATER-task-brief.md @ arena/4a614e63-prompt-first-bench 140ce26 已派发；Part A family_check 升级（模型自报+5 工件 J1-strict 重打）+ Part B 75 cell 双裁判盲判 8 批（dual-rater-batch-plan.json）；解锁 r160 卡人项①⑤——arena 通道本轮实证可用（r158/r160 的不可用结论过时）。产出待核验：hetero-judge-results-r2.json + family-upgrade-analysis.json + dr-b1..b8.json + dr-summary.json |
| prompt-first-bench（消融实验产出） | 同上会话 | 2026-10-29：O3 权重消融完成，commit d5c8a51 @ arena/78602cd5-prompt-first-bench，已 merge 回 rubric-v3 分支并 push |
| —（本地 stop_hook 改造） | — | 2026-10-29 r88-r90：stop_hook 对齐 ralph-loop 停止门——每回合过门+无活也 continue 找新目标，真停仅 HALT/用户喊停。stage-gate commits 600045a→061ec62→60ce4b4 |
| —（R5.4 终态效度） | — | 2026-10-29：run4 oracle 独立复验 PASS（sha256 一致 + 4/4 EXIT=0），terminal-validity.md 落盘，workspace commit 20f7713c。R5 剩余：R5.1 第二打分器（ego ChatGPT，需登录态）→ R5.2b run5 arena → R5.5 bench.md r5 |

| hermes-workspace-zero（金融 D1-financial-market-analysis + GW taste review） | 新会话 2026-11-01（F10-R3 资金动力学调研），taskSpace: f10-r3-arena-dispatch，绑定分支 arena/gw-taste-review → agent 工作分支 arena/25201d65-hermes-workspace-zero | **2026-11-02：GW-BacQFT 全 5 阶段完成** ✅（ff7d2974→d39d68e8→c7567c2d→464e0822→f57d40fc）。s1-refs: 清除 7 幻觉文献替换已验证 arXiv。s2-math: Thm 3.1 P-scaling 修正 + SNR 统一。s3-taste: 删 AI 元叙事。s4-cosmic-variance: Allen 2023 error budget + 删跨域元叙事。s5-m2-positioning: Limitations 新增 Methodological positioning 条目（双层结构声明）。13pp, 19 bibitems (zero orphans), arXiv pack v16 ready。待成璐手动上传 arxiv.org。会话空闲。 **2026-11-02：ORF 阶段4 全组件完成** ✅（A+B+C+D）。A: 协方差构造+验证(4.75% err)。B: 分离估计量(I 3.4%, V 17.2%)。C: Fisher信息+LRT校准(H0 p>0.05, signal p≈0)+灵敏度曲线。D: 真实LISA-Taiji ORF端到端(Γ^I零交叉@2mHz, Γ^V<<Γ^I 4-6 orders, 有效频段f<5mHz) + 三通道联合Fisher(X+Y+Z: V增益3→10×, I增益1.4→92×; X通道对手征有几何抑制, Y/Z更强)。论文第四部分已写入。D-04 真实ORF注入恢复验证通过（I无偏@f>2.5mHz, V亚单位不确定度@4mHz）。 2026-11-01：F10-R3 完成 — A/B/C/D + receipts @ 8479fb50 (agent 分支 arena/bbea6ca3-hermes-workspace-zero)，merge 回 arena/f10-gas-dynamics-research @ 11f78192。receipts 自报降级 level 4（沙箱无 web-llm），D 门禁独立线=2 <3。**此会话为该仓库唯一活跃会话**。坑：agent 工作分支 ≠ 任务书分支，回执核验去 agent 实际 push 的分支找 |
| dd2003-460/hermes-workspace-zero | `arena.ai/agent/01a19661-a064-7684-b5ef-6bc8bbea6ca3`（Continue 后分支 arena/9872a196） | **2026-11-05：F10-R5 宏观 regime 调研已完成** ✅（stage 01→02→02.5→03 全过，df8e29da → merge 6304ab54）。产出 r8/ 共 7 文件 984 行。核心判决：H_macro 文献层面不成立（日频方向 OOS 胜率 5.6% 最低档）；S5 (Shek 2026) funding 极值按当日方向分组 +3.62pp gap 是 R2 漏掉的维度。agent 建议先做 H1（方向分组复现，不需要宏观数据），若也 FAIL 则 F10 收束为负结果报告。待成璐拍板是否进 H1 回测。；历史：F10-R3 A/D域门禁补证（01a196b0, 2026-11-01）+ R3 主体（01a19661, 2026-10-30） |
| dd2003-460/research-prompt（R0.3 hetero-judge） | `arena.ai/agent/01a1acde-7ca1-715c-a996-f1289d23b2ae`（taskSpace: t33-hetero-judge-research-prompt, 2026-11-06 新开） | **2026-11-06 ✅ 完成**——T33 hetero-judge 已派发并执行完毕。push 403（GitHub App token 只读），数据从对话提取写入本地 score-v2-hetero.json + SUMMARY-T33-T34.md。结果：mean=13.33, σ=3.51, Δ=-4.67（vs lead 17.67/1.25/-0.33）。方向一致，幅度差 14×。commit c8d1eb1。 |
| dd2003-460/prompt-first-bench（T36 Q2-Q5 hetero-judge 扩展） | `arena.ai/agent/01a1ace3-4502-7915-9131-5d55d8dcd93a`（taskSpace: arena-new-session, 2026-11-06 新开会话） | **2026-11-06 ✅ T36 完成**——72 份工件打分，H2 CONFIRMED / H1 INCONCLUSIVE，commit b3e143f。**2026-11-06 🔄 T38 fullloop S04 hetero-judge**——首次派发到此会话（agent 读完任务书+payload 后停止，无 send 按钮无法续推）→ **已迁移到新会话 `arena.ai/agent/01a1ae24-c3ed-77d3-a98b-bc6cdb10c1a5`**（taskSpace: t38-fullloop-judge-dispatch），agent 正在 clone + 执行。26 份有效 4-stage S04 终稿（9 configs × 2 domains × 2 seeds），M1/M4 盲判 + R5 anti-leniency；任务书 tasks/T38-fullloop-hetero-judge-task.md @ arena/t38-fullloop-judge 784a154（payload sha 750b1054）。push 预期仍 403（token 只读），产出走对话提取落盘。 **2026-11-06：rubric v3.2 replay 已派发**（同会话续推）——任务书 tasks/T8-C3v3-rubric-v32-replay-task.md @ arena/t38-rubric-v32-replay 111643e（merge main 后含 rubric v3.2 文件，J1 sha 8d83a0e3）。验收线：§6-A 两围栏 cell J1 ≥0.8；§6-B 交叉引用 cell 数如实报告。产物：arena-hetero-judge-results-v32.jsonl + summary-v32.md（36 cell 双判官盲判，纯 rubric 版本升级对照）。 **⚠️ 会话故障（2026-11-06 11:07）**：首轮成功启动（clone+读任务书+写 judge_v32.py+修 unpack bug），随后连续 3 次发送均 5 秒内 "Something went wrong"（无 reCAPTCHA、无 modal、composer 正常）——疑似 Arena 服务端对该会话限流/熔断。处置：已试冷却重发 ×4（含极简文本"继续。"）全部 5 秒内失败——会话级熔断确认，非限流节奏问题；Model 选择器在 agent mode 无下拉（Auto 唯一选项），无法换模型绕过。**结论：该会话不可恢复，需开新会话**（新会话 clone + checkout arena/t38-rubric-v32-replay @ 080fc14，任务书+验收脚手架 validate_v32_replay.py 均已在分支上）。 **已执行（2026-11-06 11:25）**：新会话 `01a1aee0-d9d1-75a0-a892-11421d4c7a14` 已派发完整任务书指令（clone -b arena/t38-rubric-v32-replay，HEAD 080fc14；含方法学红线"禁止确定性脚本编码 rubric"+防锚定条款），orchestrating 中。旧会话 01a1ae24 作废。 **修正（2026-11-06 11:40）**：01a1aee0 被平台默认绑定到 d1-video-recreation 仓库而拒执（agent mode 会话固定绑定创建时的 repo/branch）。已通过 composer 的 repo/branch 选择器正确新建会话 `01a1aee6-f717-7e8f-a8bf-6b512858680a`（绑定 prompt-first-bench @ arena/t38-rubric-v32-replay）并派发成功——agent 已开始读任务书（cat 输出可见）。当前活跃会话：**01a1aee6**。经验：Arena agent mode 新建会话必须先在 composer 点 repo chip → 选仓库 → 点 branch chip → 选分支，再发消息；直接发 clone 指令会被错误绑定拦截。 **执行中（2026-11-06 11:45）**：agent 首轮正确核验 rubric sha（J1 8d83a0e3 ✓ / J2 b229dcc9 ✓）+ 18 工件在位后，以"无判分端点、拒绝用确定性脚本伪装 LLM 盲判"为由暂停——方法学判断正确（旧会话的 judge_v32.py 路线正是任务书禁止的）。已确认"由会话模型分别扮演 J1/J2 逐项判读"即异源设计本身，并给出 JSONL 行格式规范；agent 已开跑 batch 1（逐 artifact 读 stage01-03 + 批量落盘命令进行中）。 **完成（2026-11-06 11:43）**：36 cell 全部判完，push 成功（无 403），分支 `arena/2858680a-prompt-first-bench` @ 9046b35，交付 results-v32.jsonl + summary-v32.md。Lead 独立复算（validate_v32_replay.py 全过 + 内联配对复算，落盘 `LEAD-INDEPENDENT-COMPARISON-v32.md` @ b5fbed1）：§6-A 两围栏 cell J1 均 1.0（验收 PASS，rubric 改动直接目标达成）；§6-B 交叉引用 6→6（2 换 2，规则部分生效未减总数）；G2 spread 2/6→2/6 无改善；κ 0.606→0.559（pooled item-level n=401，同模型双角色≠真 IRR）；J1 通过率 0.654→0.886、J2 0.805→0.961，但 id 级翻转 J1 119/J2 77，**~21pp 提升无法归因于 rubric 改动**（围栏修复只解释 ~1.5pp），疑 leniency drift；且 11/18 cell J1≡J2 全一致。**结论：窄结论成立（围栏 bug 修复+交叉引用规则部分生效），"v3.2 整体质量提升"不可下**。另发现 v3.1 summary 数字（0.638/0.798）与其 jsonl 复算（0.654/0.805）差 ~1.6pp，旧 summary 存疑待核。

**T38 收口（2026-11-06）**：v3.2 replay 闭环，不再追加 arena 轮次（产投比判断见下）。结论分层落盘：① 硬结论——rubric v3.2 修复了 code-fence 围栏判定（§6-A 两 cell J1 0→1.0，验收 PASS）+ 交叉引用规则部分生效（6 cell 换 2）；② 不可下结论——"v3.2 整体质量提升"（~21pp 通过率上移无法归因于 rubric 改动，疑 leniency drift；G2 spread 2/6 无改善；κ 0.559 同模型双角色非真 IRR；模型身份平台不披露，"异源"不可证）。再跑一轮 arena 只能换一批漂移数字，不能消除上述结构性限制——坐实"异源可复现"需要 arena 用可标识模型族，超出当前通道能力。**遗留待办（低优先级，随下次 pfb 活动顺手做）**：(a) v3.1 summary 数字 0.638/0.798 vs jsonl 复算 0.654/0.805 差 ~1.6pp，需核对哪份是权威并修正另一份；(b) T17 四臂比较表里 S7/S7T/S7F/S7V 的 M1/M4/M6 与 Total 数值关系未验证（疑似不同聚合口径），引用前必须补口径说明。 |
| from-motivation-to-society（动机社会写作） | `arena.ai/agent/01a197a6-b7bb-7c8c-8565-139a0b215928`（taskSpace: motivation-society-ch10-contradiction） | **2026-11-02：Part IV + Part V 全部完成** ✅。ch8 通道生成器 → ch9 模因 → ch10 经济（含幽灵堵车 H6）→ ch11 政治 → ch12 法律 → ch13 预测 → ch14 闭合。7 章 0 gray placeholders，669 行。test 分支 @ 9629054。会话空闲。 |

| dd2003-460/decomp-bench | `arena.ai/agent`（taskSpace: decomp-t8-partb-arena-dispatch, ego-browser space 957）→ agent 工作分支 arena/e31379c5-decomp-bench | **2026-11-02：T8 Part B 文献调研完成** ✅。ego-browser 切换仓库到 decomp-bench → tiptap execCommand insertText 派发 → agent 56行调研(7来源: Reflexion/Self-Refine/Huang ICLR/CRITIC/LLM-as-judge/Wataoka/PIVOT 2026) → push arena/e31379c5-decomp-bench @ ce20b23 → merge main。核心: Q1阶段效应不均但非纯prompt; Q2 critic有效=可定位可执行反馈; Q3边际递减有例证非通用; Q4 L1→pipeline=待测方向。 **2026-11-02 r245i：T8 Part C 对抗核验已派发**（rubric v2 全量重放 AC1-AC4 全过后开跑；任务书 tasks/T8-partC-dispatch-task.md @ main fd813d7+更新版；arena binding 修复后实证可用）。会话执行中。

**原则**：每个项目有自己的仓库，arena 连接对应仓库，读仓库内的任务书执行。不跨仓库混用。

### 3.2 连接仓库（新会话直接选仓库 · 2026-10-26 修正）

> **修正**：arena.ai/agent **新会话可以直接切换/选择仓库**（用户实证：新开会话 easily 切到 d1-video-recreation，会话 01a17723）。旧认知"账号级 OAuth 绑定 pfb、UI 无切换入口"已作废。

1. **★ 选对仓库是第一原则**：开新 arena 会话时，按 §3.1 映射表选目标仓库直连，不走 pfb 中转。
2. GitHub App 授权保持 "All repositories"（含私有），保证所有仓库可访问
3. pfb 中转仅用于历史遗留（batch-11 及之前的分支产出需提取清扫）

**验证**：`git ls-remote https://github.com/dd2003-460/<repo>.git HEAD` 返回 hash = 可达（权限本身在 arena 会话内验证）。

### 3.3 失败降级

| 故障 | 诊断 | 降级方案 |
|------|------|---------|
| git clone 403 | `curl -s -o /dev/null -w '%{http_code}' https://github.com` 测网络 | ① 用 GitHub REST API（Contents API）读写文件 ② 上传任务书到对话本机执行 ③ Lead 本地自答（conf-0.2，loop 工件照常落盘） |
| token 过期 | `git ls-remote` 测权限 | 重新 OAuth 授权 / 用 `gh auth token` 生成新 token |
| arena 沙箱拦截 git | `curl https://api.github.com` 通但 `git clone` 不通 | 用 GitHub REST API（不走 git） |

**降级原则（2026-11-06 成璐修订）**：

1. **默认不降级**。arena 是首选通道，故障时必须先穷尽修复手段再考虑本地执行。
2. **修复清单**（按顺序尝试，全部失败才允许降级）：
   - ① `curl -I https://arena.ai` 确认网络通
   - ② ego-browser 重新 goto arena.ai/agent（会话页面可能过期）
   - ③ 查 ego-lite 进程是否活着（`ps aux | grep -i ego`），死了就重启
   - ④ 换 taskSpace 名开新会话（旧 space 可能僵尸）
   - ⑤ 检查 GitHub App token 权限（`git ls-remote` 测写权限）
   - ⑥ 若沙箱拦截 git → 用 GitHub REST API（Contents API）替代
   - ⑦ 仍失败 → 记录具体报错（哪条链路 + 什么错误码），等下一个 keepalive 周期重试
3. **降级条件**：以上 7 步全部失败 + 连续 2 个 keepalive 周期重试无效 → 才允许 Lead 本地自答（conf-0.2，loop 工件照常落盘）。
4. **降级后必须修复**：降级不是终点。每次降级后立即在 `knowledge/efficiency-bottlenecks.md` 记录故障根因 + 修复计划，下一个可用周期优先尝试恢复 arena 通道。
5. **禁止静默降级**：不得因为"本地也能跑"就直接跳过 arena。只有确认所有方法都试过且不可修复时，才允许本地跑。

## 4. loop 阶段速览（自 loop-executor.md 并入 · 逐段定义见仓库内 loop/prompt-first/）

6 阶段，每阶段读对应 `loop/prompt-first/<阶段>.md` → 产出落盘 `loop-artifacts/stages/<N>/` → 判定 pass/revise：

| 阶段 | 产出 |
|------|------|
| 01 目标分解 | decomposition.md（正交+覆盖+边界+已知vs空缺+递归到原子） |
| 02 信息调研 | research.md（GitHub→arXiv→ego-browser→自答；每条 claim 带来源+conf） |
| 02.5 交叉验证 | crosscheck.md（关键结论 ≥2 LLM；矛盾记录） |
| 03 行动分解 | actions.md（依赖+并行标注+执行级原子化） |
| 04 执行验证 | execution-log.md（per-step 备份→执行→review→提交） |
| 04.5 反方复核 | review.md（找矛盾+验证假设） |

**约束**：每阶段产出必须落盘；判定基于工件内容不是感觉；任务卡 ≤50 行；每读 N 个文件先写 checkpoint。

### 4.1 复制 + push 命令模板（断点 A）

目标仓库是独立 git 仓库（含 `loop/ sop/ tasks/ rubric/`），workspace 是源。已验证先例：`dd2003-460/prompt-first-bench`。

```bash
# 本地浅克隆目标仓库（已存在则 git -C <dir> pull）
git clone --depth 1 https://github.com/dd2003-460/<repo>.git /tmp/<repo>
# 同步 workspace 的 1-loop 阶段文件 + SOP（只同步 prompt-first/，workspace loop/ 其他子目录不属于仓库）
rsync -av --delete /Users/a1-6/Desktop/workspace/loop/prompt-first/ /tmp/<repo>/loop/prompt-first/
cp /Users/a1-6/Desktop/workspace/sop/arena-loop-pipeline.md /tmp/<repo>/sop/
# 记录验证证据 + commit + push
git -C /tmp/<repo> add -A && git -C /tmp/<repo> commit -m "sync: loop/prompt-first + sop (workspace $(date +%Y%m%d))"
git -C /tmp/<repo> push && git ls-remote https://github.com/dd2003-460/<repo>.git HEAD
```

说明：rsync `--delete` 保证仓库 `loop/prompt-first/` 与 workspace 完全一致（6 个阶段文件 + examples/ 示例子目录，2026-10-26 外移）；**不要 rsync 整个 workspace `loop/`**（含 archived 等与 arena 无关的内容）。sop 只复制本文件。push 后把 commit hash + ls-remote 输出写进 tasks/ 验证文件（§1 断点 A 硬门禁）。

## 5. goal 模板引用

所有外包 arena 的 goal，目标描述包含：
```
按 `sop/arena-loop-pipeline.md`（仓库内）/ `sop/arena-loop-pipeline.md`（workspace）流程执行：
1. 选仓库：<repo>
2. 复制 loop/ + 本 SOP 到仓库 + push（断点 A 门禁）
3. 发任务书（含强制段）+ push（断点 B/C 门禁）
4. arena 执行 + 评分 + push
5. 失败降级：按 §3.3（loop 不豁免）
```

## Battle 投票 = 免费的多模型打分器

R5.2-third-scorer / RV3G4-kappa-gate-execution 类"需要不同模型家族独立打分"的阻塞项，可用 battle 通道解：

1. ego-browser 打开 lmarena.ai（已登录态），新建 chat
2. 把同一份盲打材料（如 packet v2 三 run 评分任务书）发给 battle
3. 两个匿名模型各自独立作答（上下文天然隔离，互不可见）
4. **必须投票**（选 A 好/B 好/平局均可）→ 页面揭晓双方真实模型名
5. 记录：模型名 + 完整回答文本 → 落盘 `bench/rubric-v3/scorers/<date>-battle-<id>.json`
6. 每轮新会话（不污染上下文）；N 轮得 N×2 个模型家族的独立分数
7. 收齐 ≥3 个不同家族后算 Fleiss'κ（消费 assert-kappa-receipt.py schema）

### 硬约束

- 投票是揭晓模型名的唯一途径，不投票 = 白跑
- 记录时必须存原始回答全文（不是摘要），后续复算要用
- 同一份材料发多次 = 多个独立样本，但同一模型家族只取一次（防重复计数）
- 自动化限制：battle 页面的发送/投票按钮用 ego-browser JS 事件派发（同 GPT 侧套路）；若菜单/按钮触发失败，降级为半手动（我准备好材料，成璐点两下）

## 结果核验

- agent mode：不信汇报信 git（fetch 显式 refspec → log → show 文件 → 独立复算数字）
- battle mode：核对揭晓的模型名与记录一致；回答文本 sha256 入库；分数复算和原文对账

## 7. 维护补充（2026-10-30）

- 新增 battle 通道实操细节（ego-browser 选择器、投票按钮定位、揭晓页解析）→ 补进本文件 §Battle 节 + skill `arena-outsource` references
- 每次 battle 打分轮次 → 台账登记（日期/模型对/材料 hash/落盘路径）

## 8. 维护

- 新增仓库 → 更新 §3.1 映射表
- 新增链路断点（实际断裂案例）→ 更新 §1 表格 + 记 qanda-ledger
- 故障修复 → 更新 §3.3
- 本文件变更 → commit + push（workspace + 已部署的目标仓库同步）

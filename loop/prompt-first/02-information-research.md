# 阶段 02：资料搜集与网页 AI 交叉询问

## 操作流程

1. 读取阶段 01 的空缺条件，只围绕这些空缺搜集资料。
2. 必须先做网页 LLM 交叉询问（通道=ego-browser，SOP=`.claude/skills/ego-verify/SKILL.md`；问题围绕阶段 01 空缺条件，只要求可复核来源线索），把真实回执写入阶段工件；网页 LLM 只提供线索，不是事实来源。若通道以未授权/未配置状态快速失败，记录完整失败原因后继续公开网页资料搜集，不得等待或循环重试。
3. 为每个关键主张记录来源标题、URL、发布或更新时间、实际观察时间、具体观察和不确定性。
4. 关键主张至少寻找两个相互独立的来源。厂商规格、独立评测、实际价格或用户实测应明确区分。
5. 对价格、库存、版本、政策、软件支持等易变事实，优先使用最近 7 天内的资料；若没有足够新资料，明确标为未解决。
6. 对稳定事实可以使用较早的一手资料，但必须说明它为什么仍然适用。
7. 记录搜索失败、登录限制、网页 LLM 不可用和零结果；这些不是证据，不能伪装成来源。对同一主张的 WebSearch 若返回 0 结果或失败，最多更换一次关键词；仍失败就记录失败原因和未解决状态，停止重复搜索并写入阶段工件。
8. WebFetch 只对最多 4 个已知、具体 URL 各尝试一次；单个 URL 无结果、403、404 或明显长时间无响应时立即记录状态，不要重复抓取或等待。至少拿到一个可读的一手页面后就停止抓取并写阶段工件。
9. 不要在本阶段写最终推荐，只收集证据、暂定结论和仍未解决的空缺。

## 可用工具索引

### 网页搜索工具

| 工具 | 适用场景 | 调用方式 |
|------|----------|----------|
| 网页 LLM 交叉询问 | 快速核验事实、获取线索 | ego-browser + ego-verify skill（围绕阶段 01 空缺提问） |
| `ego-browser` | 需要登录状态、反爬绕过、动态渲染页面、网页 LLM 交叉验证 | `ego-browser nodejs <<'EOF' ... EOF` |
| `curl`/`wget` | 直接获取 API 或静态页面 | 终端命令 |

### ego-browser 用法（单通道，驱动用户已登录的 ego-lite）

网页 LLM 交叉验证、登录态页面、动态渲染页面**一律走 ego-browser**，不用任何无头/非持久浏览器。全局规则与站点清单见 `AGENTS.md` §网页 LLM 交叉验证流程。

```bash
ego-browser nodejs <<'EOF'
const task = await taskSpace('my-task')        // 同名 space 可复用
const p1 = task.page('p1')
await p1.goto('https://example.com')
const s = await p1.snapshot()                  // 定位: @N ref / loc=css: / loc=role: / text= / xpath=
// await p1.fill('text=输入框', '内容')
// await p1.click('@3')
// await p1.waitForFunction(() => document.body.innerText.includes('完成'), { timeout: 60000 })
const reply = await p1.snapshot()
console.log(reply)
await task.finish({ keep: [] })                // 结束前必须 finish，否则留僵尸进程
EOF
```

**关键注意事项：**
- 选择器：快照 ref `@N`、`loc=css:`、`loc=role:`、`text=`、`xpath=`
- 等待：`waitForURL` / `waitForSelector` / `waitForFunction` / `waitForTimeout`
- 每次 heredoc 是独立 Node 运行时，跨次状态不保留；靠同名 `taskSpace` 复用浏览器会话
- 结束前必须 `task.finish({ keep: [] })`
- 不要用 Playwright 方法，不要另开浏览器实例

## Reviewer 质检标准

- 阶段 01 的关键空缺是否逐项有证据或明确保留为未解决；
- **证据来源完备（防"名不副实"）**：每条关键主张必须附来源 URL/本地路径 + 快照时间戳，三者缺一即降级为"存在性断言-未核验"，不得计入已核验证据。Reviewer 抽查发现无来源主张被当事实使用 = revise，repair_stage 写 02。
- 关键主张是否有足够独立来源；
- 易变事实是否接近当前日期，实际观察时间是否明确；
- 是否把网页 LLM 线索误写成事实来源；
- 是否记录并处理来源矛盾；
- 是否仍存在会改变下一阶段方案的关键证据缺口。

只要关键主张缺少独立来源、关键时效信息过期或存在未解释矛盾，必须 revise，repair_stage 写 02。

## 操作示例

→ `examples/02-examples.md`（核验已证明事实、稳定 vs 易变、近似/未证红线，数学领域方法示范）

# DESIGN.md · devkit-skills 完整设计

> 版本 v4 ｜ 16 个技能 ｜ 本文是唯一权威设计文档，实现与本文冲突时以本文为准并同步修正实现。

---

## 0. 设计约束（来自实测，不是偏好）

| 约束 | 证据 | 强制影响 |
|---|---|---|
| skills 必须**一层平铺** | 本地曾装 `production`(114)/`official`(17)/`guide`(29)/`awesome`(864) 个 SKILL.md 全部未生效，唯带 `plugin.json` 的 `fullstack` 生效 | 目录只能是 `skills/<name>/SKILL.md` |
| **不交付 commands 层** | Qoder 实测：插件内 `commands/` 不加载 | 斜杠入口即技能名 |
| description 必须短 | `product-design` 28 个 skill 的双语描述吃掉 31.9k 常驻 token | 描述 ≤200 字，禁止流程描述 |
| 不能强制流程 | superpowers `using-superpowers`：「1% 可能相关就必须调用」 | 仅 4 个 model-invoked |
| 必须可绕过 | 用户会直接缩小范围（「这个不用管，你只管做 X」） | 每个技能必须有「不适用」一节 |
| 产物挂在已有约定上 | 项目已有 `.ai/issues`、`.ai/specs`、`.ai/STATUS.md` | 默认 `.devkit/`，可配置改指 |
| 跨 harness 可移植 | Claude Code / Qoder CN / Codex 的调用控制键不同 | 三键齐发 + `agents/openai.yaml` |

---

## 1. 命名规范

```
仓库   devkit-skills
前缀   dv-
目录   skills/dv-<name>/SKILL.md
name   必须等于目录名
```

| 规则 | 值 |
|---|---|
| 目录名 | 全小写，`dv-` + 单个短词，不超过 12 字符 |
| description | 中文主句（≤60 字）+ 英文 `Triggers:` 尾巴；总长 ≤200 字 |
| 禁止 | 在 description 写流程步骤（Description Trap：模型会只读描述不读正文） |
| 禁止 | 出现公司名、团队名、内部系统名 |
| `metadata.stage` | `meta` / `discover` / `build` / `verify` / `ship` |
| `metadata.edits-code` | 布尔，只读技能为 `false`，`lint` 强制 |
| `metadata.next` | 正常下一步的技能名数组，终点为 `[]`，`lint` 校验存在性与无环 |

---

## 2. 16 个技能总表

| # | 技能 | stage | 作用 | 触发 | edits-code | 产物 | next |
|--:|---|---|---|---|:--:|---|---|
| 1 | `dv-route` | meta | 按处境给唯一推荐；`--auto` 托管推进 | 自动 | false | 无 | 按推荐 |
| 2 | `dv-help` | meta | 手册：总表 / 单条 / 流程 / 场景 / 排错 | 手动 | false | 无 | `[]` |
| 3 | `dv-context` | meta | 新仓接入：config + AGENTS 段 + 状态文件 | 手动 | true | config / AGENTS / STATUS | `[]` |
| 4 | `dv-author` | meta | 造/改/评估技能；30 天淘汰闲置 | 手动 | true | 新技能 + eval | `[]` |
| 5 | `dv-grill` | discover | 拷问对齐 + 术语/ADR + 落 spec 草稿 | 手动 | false | specs / CONTEXT / adr | `dv-plan` |
| 6 | `dv-research` | discover | 主源取证，后台跑，结论落盘 | 自动 | false | docs/research | `dv-grill` / `dv-arch` |
| 7 | `dv-plan` | discover | spec 定稿 ↔ 拆垂直切片工单 | 手动 | false | specs / issues | `dv-build` |
| 8 | `dv-design` | discover | 结构 / 状态 / 异常态 / 动效 / tokens | 手动 | false | docs/design | `dv-build` |
| 9 | `dv-arch` | discover | `shape` 深模块接缝 / `migrate` 安全迁移 | 手动 | 按模式 | adr / 迁移计划 | `dv-grill` / `dv-build` |
| 10 | `dv-build` | build | 按工单实现，内含 TDD 循环 | 手动 | true | 代码 + 测试 | `dv-review` |
| 11 | `dv-debug` | build | 先建 red-capable loop，再谈假设 | 自动 | true | 复现 + 回归测试 | `dv-done` |
| 12 | `dv-test` | verify | `design` 用例设计 / `run` 写跑测试 | 手动 | 按模式 | 用例表 / 测试代码 | `dv-build` / `dv-review` |
| 13 | `dv-audit` | verify | 突变 + CRAP + 测试有效性，只报告 | 手动 | false | docs/audits | `dv-build` / `dv-done` |
| 14 | `dv-browser` | verify | 真实浏览器验收、极端数据、性能 | 手动 | true | 脚本 + 探针结论 | `dv-done` |
| 15 | `dv-review` | verify | 三轴独立：Correctness / Standards / Spec | 自动 | false | docs/reviews | `dv-done` |
| 16 | `dv-done` | ship | 门禁 → 状态 → 提交 / MR / worktree | 手动 | true | commit / MR | `[]` |

常驻估算 1.6k token；单次触发 1.5–4k。

---

## 3. 自动触发的三层设计

### L0 只读自动（4 个）

`dv-route` `dv-research` `dv-debug` `dv-review`

判据：**症状客观**——用户不知道下一步、要查资料、有报错、有 diff。模型判断比你快，且误触发代价低（都只读或只推进一小步）。

### L1 状态注入（hook，一行）

`scripts/dv-hook.sh` 挂在 `UserPromptSubmit`，读 `.devkit/state.json`，输出：

```
[devkit] stage=build ticket=007 next=/dv-review
```

约 30 token/轮。稀疏策略：阶段变化后 3 轮内注入，之后每 10 轮提醒一次。

### L2 仪式（12 个）

必须用户输入。三键齐发：

```yaml
disable-model-invocation: true   # Claude Code / Codex
user-invocable: true             # Qoder CN
```
```yaml
# 同级 agents/openai.yaml
policy:
  allow_implicit_invocation: false
```

`lint.py` 对 12 个 L2 技能强制校验以上三项，缺一项 CI 失败。

### 拒绝的设计

| 拒绝 | 原因 |
|---|---|
| 全部 model-invoked | 即 superpowers 的病 |
| 关键词正则路由 | 中英混输 + 口语必漏，漏了比没有更糟 |
| hook 里调模型做语义路由 | 每轮多一次调用，收益不如一行状态 |
| 自动越过 L2 gate | gate 的意义就是停 |

---

## 4. 技能正文统一骨架

```markdown
---
name: dv-xxx
description: <中文主句>。Triggers: <英文触发词>
disable-model-invocation: true        # L2 才有
user-invocable: true                  # L2 才有
metadata:
  stage: build
  reads: [CONTEXT.md, .devkit/issues]
  writes: [.devkit/specs]
  edits-code: false
  next: [dv-build]
---

# <中文名>

<一句话定义 + 与最易混淆技能的互斥句>

## 适用 / 不适用
适用：…（3 条，各带触发场景）
不适用：…（每条指向替代技能）

## 输入
## 流程
1. …（每一步可执行、可验证）
## 产物
## 停止条件 / 自检
## 反合理化
| 我本来想说 | 现实 |
```

四条硬规则：

1. **正文 ≤120 行**，超出拆 `references/`，正文只写「什么时候读哪篇」
2. 每个技能必须有**互斥句**（「这个不是 X，要 X 用 `/dv-y`」）
3. 每个技能必须有**不适用**一节
4. 只读技能不得出现「修改」「写入」类动词

---

## 5. 主流程与状态机

```
dv-grill ──► dv-plan ──► dv-build ──► dv-review ──► dv-done
   ▲            │            ▲            │
   │            └─(tickets)──┘            └─(小改)──► dv-done
   │
dv-research · dv-arch(shape)        dv-design · dv-arch(migrate) · dv-test(design)
                     │                              │
                     └──────────► dv-build ◄────────┘

on-ramp   dv-debug ──► dv-done      dv-browser ──► dv-done      dv-audit ──► dv-build
元        dv-route · dv-context · dv-author · dv-help
```

### state.json（8 字段）

```json
{
  "stage": "build",
  "ticket": "007",
  "blocked_by": [],
  "next": "/dv-review",
  "since": "2026-10-22T10:00:00+08:00",
  "session": "857cb1f2",
  "branch": "feat/export-csv",
  "worktree": "/path/to/repo-worktrees/export-csv"
}
```

三个 gate（必须停）：

1. `dv-plan` 的 spec 定稿前
2. `dv-plan` 的工单拆分后、开工前
3. `dv-done` 的提交前

`dv-route --auto` 只在这三处停。

---

## 6. 产物协议

见 [ARTIFACTS.md](ARTIFACTS.md)。要点：

- 默认 `.devkit/`，可配置改指 `.ai/` 等已有目录
- specs 与 issues 共用一套递增序号
- `state.json` 判下一步，`STATUS.md` 给人读
- 不新建并存的第二套目录

---

## 7. 多端分发

| Harness | 清单 | 说明 |
|---|---|---|
| Claude Code | `.claude-plugin/plugin.json` + `skills: "./skills/"` | 也可 `link.sh` 到 `~/.claude/skills/dv-*` |
| Qoder CN | `.qoder-plugin/plugin.json` → `cache/local/devkit-skills/<ver>/`，注册 `devkit-skills@local` | 只认 `.qoder-plugin/` |
| Codex | 直接读 `skills/` + `AGENTS.md` | — |
| Cursor | `link.sh` 生成 `.cursor/rules/dv-*.mdc` 薄指针 | 规则文件不是技能 |

`link.sh` 幂等，只建符号链接，永不 copy（防版本漂移）。

---

## 8. 校验与治理

### lint.py 的 12 条规则

| # | 规则 |
|--:|---|
| 1 | 技能目录一层平铺，禁止 `skills/*/*/SKILL.md` |
| 2 | 目录名 = frontmatter `name` |
| 3 | 名称以 `dv-` 开头，全小写 |
| 4 | description 总长 ≤200 字 |
| 5 | description 不含流程步骤词（先/然后/步骤/step/first/then） |
| 6 | L2 技能必须同时具备 `disable-model-invocation` 与 `user-invocable` |
| 7 | L2 技能必须有 `agents/openai.yaml` 且 `allow_implicit_invocation: false` |
| 8 | 每个技能必须有 `metadata.stage` / `edits-code` / `next` |
| 9 | `next` 中的技能必须存在；非终点技能 `next` 不得为空 |
| 10 | `next` 图无环（`dv-plan ↔ dv-build` 回边豁免，需显式标注） |
| 11 | 正文 ≤120 行 |
| 12 | 正文必须含「适用」「不适用」「互斥」三类小节 |

### 30 天淘汰

`dv-author` 读取使用统计（Claude Code 的 `skillUsage`），连续 30 天 0 次的技能 → 移到 `in-progress/` 并在此文档标记，不直接删除。

---

## 9. 与上游的关系

| 上游 | 取什么 | 不取什么 |
|---|---|---|
| [mattpocock/skills](https://github.com/mattpocock/skills) | grill→to-spec→to-tickets→implement→code-review 的骨架；`next`/`edits-code` 的思路；深模块词汇 | `.scratch/` 目录约定、issue-tracker 配置文件 |
| [obra/superpowers](https://github.com/obra/superpowers) | TDD 三条铁律、systematic-debugging 的「先建反馈环」、verification-before-completion 的门禁 | 强制自动调用、SessionStart 全量注入 |
| [anthropics/skills](https://github.com/anthropics/skills) | frontend-design 的审美约束、webapp-testing 的侦察-行动模式、skill-creator 的评估流程 | — |
| [emilkowalski/skills](https://github.com/emilkowalski/skills) | break-ui 的极端数据清单、动效四问、原型多版本对比 | 纯前端/动效的其余 11 个 |
| [AgentForge](https://github.com/Lixiuxiu559/AgentForge) | test-design 的规则可追溯、mutation/complexity 的只报告边界、diff-review 的三轴 | 中文以外的适配层 |

MIT 兼容；逐条署名见 [NOTICE](NOTICE)。

---

## 10. 已知风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| Qoder 不支持 `disable-model-invocation` | 12 个仪式型技能可能被自动触发 | `user-invocable` + `openai.yaml` + lint 强制；上线前在 Qoder 实机验证 |
| Qoder 的 hook 注入未实测 | L1 状态层可能只在 Claude 生效 | 上线前 5 分钟验证；不通则降级为交接段 |
| `dv-plan` 合并 spec/tickets 可能丢审批粒度 | spec 未确认就拆工单 | 正文两个显式 `STOP` 标记 + 自检清单 |
| 16 个仍需自养 | 模型换代后要重验 | 正文薄、知识进 references、上游只 vendor 不 fork |
| 开源后外部用户无 `.ai/` | 首次体验割裂 | `dv-context` 首次运行必问；默认 `.devkit/` |

---

## 11. 验证记录（v0.1.0 实测）

以下为提交时的真实执行结果，不是设计意图。

| # | 验证项 | 命令 | 结果 |
|--:|---|---|---|
| 1 | 结构校验 | `python3 scripts/lint.py` | 0 errors / 0 warnings / 16 skills |
| 2 | 总表防漂移 | `python3 scripts/dv-help-gen.py --check` | OK 总表一致 |
| 3 | 常驻成本 | `python3 scripts/cost.py` | 705 tok（仅描述）/ 1839 tok（完整 frontmatter） |
| 4 | 插件清单 | `claude plugin validate .` | ✔ Validation passed（marketplace + plugin 两份） |
| 5 | 技能加载 | `claude -p ... --plugin-dir .` | 16 个全部加载 |
| 6 | L0 隔离 | 同上，问「能自动看到哪些 dv- 技能」 | 仅 `dv-debug, dv-research, dv-review, dv-route` |
| 7 | L2 不可自动调用 | 问 `dv-ship / dv-plan 存在吗` | `no` —— 手动技能不进入自动可达集合 |
| 8 | 路由触发 | 输入「我接下来该干什么？」 | 命中 `dv-route` |
| 9 | 调试触发 | 输入「TypeError… 只在生产偶发」 | 命中 `dv-debug` |
| 10 | hook 注入 | `UserPromptSubmit` + `dv-hook.sh` | 模型复述出 `[devkit] stage=build ticket=007 next=/dv-review (39m前)` |
| 11 | hook 静默 | `state.stage=idle` | 无输出，exit 0 |
| 12 | 规则 13 有效性 | 故意把「其余 13 个」改成 12 | lint 报 2 条 ERROR，改回后恢复 0 |
| 13 | 正文长度 | `wc -l skills/*/SKILL.md` | 最长 92 行，全部 ≤120 |
| 14 | 名称一致性 | 目录名 vs frontmatter `name` | 16/16 一致 |

### 已验证的结论

- **三键齐发有效**：Claude Code 侧按 `disable-model-invocation` 正确隔离了 12 个 L2 技能（验证 6、7）。
- **L1 状态层可行**：hook 注入的文本确实进入了模型上下文（验证 10），不是只写不读。
- **防漂移生效**：`dv-help` 首屏的数字与名单由 lint 强校验（验证 12），手改必红。

### 未验证 / 待验证

| 项 | 状态 | 影响 |
|---|---|---|
| Qoder CN 是否支持 `disable-model-invocation` | 已知不支持，靠 `user-invocable` + `openai.yaml` 兜底 | 未在 Qoder 实机跑过 16 个技能的触发边界 |
| Qoder CN 的 hook stdout 是否注入上下文 | **未验证** | 若不通，Qoder 侧 L1 降级为纯交接段 |
| Codex 侧加载 | 未实测 | 目录结构符合其约定，但未跑 |
| 真实任务端到端（场景 A–E） | 未跑 | 需在真实仓库跑一遍再定 v0.2 |
| 淘汰机制 | 未实施 | 取决于是否有使用统计数据 |

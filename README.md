# devkit-skills

> 一套面向研发全流程的 agent skills。16 个技能，你只需要记住 3 个。

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![skills](https://img.shields.io/badge/skills-16-green.svg)](skills/)

devkit 不是又一个「接管流程」的框架。它假设**流程已经在你脑子里或仓库里**，只把每一步该做什么、该产出什么、下一步交给谁，写成 agent 能执行的动作。

它和 superpowers / BMAD / spec-kit 的区别只有一条：**devkit 不强制任何一步。** 12 个技能默认只有你能触发，模型自己只能碰 4 个（查资料、调 bug、审 diff、问路由）。

---

## 为什么需要它

现有 skill 包的两个通病，devkit 是照着这两条设计的：

| 通病 | 症状 | devkit 的对策 |
|---|---|---|
| **流程绑架** | 「1% 可能相关就必须调用」，每轮都被方法论压着 | 只有 4 个 model-invoked，其余必须你打 |
| **装而不用** | 装 100+ skill，常驻几万 token，实际用 3 个 | 16 个，description 合计约 1.6k token |

---

## 安装

```bash
git clone https://github.com/<you>/devkit-skills.git ~/devkit-skills
cd ~/devkit-skills
./scripts/link.sh --apply      # 链接到 Claude Code / Qoder CN / Codex
```

首次进入项目时：

```
/dv-context
```

它会扫描仓库，写 `.devkit/config.json`、给 `AGENTS.md` 补技能段、建状态文件。

---

## 16 个技能

### 入口（只记这 3 个）

| 技能 | 什么时候用 |
|---|---|
| `/dv-grill` | 说不清要做什么、方案没底、要跟人对齐 |
| `/dv-plan` | 说清了，要变成 spec 和可执行工单 |
| `/dv-build` | 有工单了，开始写代码 |

### 模型自己会来（不用记）

| 技能 | 触发 |
|---|---|
| `dv-debug` | 报错、失败测试、变慢、偶发失败 |
| `dv-research` | 要查资料、比方案、核实版本差异 |
| `dv-review` | 有 diff 要审、提交前、开 MR 前 |
| `dv-route` | 你不知道下一步做什么 |

### 收口

| 技能 | 作用 |
|---|---|
| `/dv-done` | 门禁 + 更新状态 + 提交 + 开 MR + 清理 worktree |

### 季节型（想不起来就问 `/dv-route`）

| 技能 | 作用 |
|---|---|
| `/dv-design` | 页面结构、状态、异常态、动效 |
| `/dv-arch` | 模块边界、深模块、安全迁移 |
| `/dv-test` | `design` 设计用例 / `run` 写跑测试 |
| `/dv-audit` | 突变测试、复杂度、测试有效性（只报告） |
| `/dv-browser` | 真实浏览器验收、极端数据、性能 |
| `/dv-context` | 新仓接入、配置与状态对齐 |
| `/dv-author` | 维护 devkit 本身、淘汰闲置技能 |
| `/dv-help` | 手册：全部技能 / 单条用法 / 主流程 / 排错 |

忘了全部也没关系：**`/dv-help`**。

---

## 主流程

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

---

## 自动触发的三层

| 层 | 谁触发 | 机制 | 技能 |
|---|---|---|---|
| L0 只读自动 | 模型 | description 触发词 | debug / research / review / route |
| L1 状态提示 | hook | `UserPromptSubmit` 注入一行当前阶段 | 全部 |
| L2 仪式 | **你** | `disable-model-invocation` + `user-invocable` + `agents/openai.yaml` | 其余 12 个 |

L1 的注入长这样，每轮约 30 token：

```
[devkit] stage=build ticket=007 next=/dv-review
```

---

## 命名与产物

- 全部技能前缀 `dv-`，目录与 `name` 字段必须一致
- 产物默认写 `.devkit/`，可在 `.devkit/config.json` 里改成 `.ai/` 等你已有的约定
- 不写死任何公司或团队流程；团队约定通过 config 注入

产物协议见 [ARTIFACTS.md](ARTIFACTS.md)，完整设计见 [DESIGN.md](DESIGN.md)。

---

## 开发与校验

```bash
python3 scripts/lint.py            # 12 条结构校验
python3 scripts/dv-help-gen.py     # 重新生成 dv-help 的总表
python3 scripts/cost.py            # 打印常驻 token
./scripts/link.sh --check          # 检查各 harness 链接是否漂移
```

CI 会跑 lint 与 `dv-help-gen --check`，防止总表与技能定义漂移。

---

## License

MIT。改编自以下项目的思想，逐条署名见 [NOTICE](NOTICE)：

- [mattpocock/skills](https://github.com/mattpocock/skills)
- [obra/superpowers](https://github.com/obra/superpowers)
- [anthropics/skills](https://github.com/anthropics/skills)
- [emilkowalski/skills](https://github.com/emilkowalski/skills)
- [Lixiuxiu559/AgentForge](https://github.com/Lixiuxiu559/AgentForge)

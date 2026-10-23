---
name: dv-plan
description: 把已谈定的内容定稿为规格，再拆成可独立交付的垂直切片工单并声明依赖。用于已有结论要形成可执行计划、或要把 spec 拆任务。Triggers: 写spec, 拆任务, 出工单, 拆ticket, plan, breakdown.
disable-model-invocation: true
user-invocable: true
metadata:
  stage: discover
  reads: [.devkit/specs, CONTEXT.md, docs/adr]
  writes: [.devkit/specs, .devkit/issues]
  edits-code: false
  next: [dv-build]
---

# 定稿与拆解

不再访谈。只综合已有结论，形成两份产物：**规格**和**工单**。中间有一个必须停下的确认点。

## 适用 / 不适用

适用：`dv-grill` 刚结束；已有明确结论要落成可执行计划；要从 spec 拆工单。

不适用：结论还没定 → `/dv-grill`；只有一句话想法 → `/dv-grill`。

## 模式

| 调用 | 做什么 |
|---|---|
| `/dv-plan spec` | 只定稿规格，不拆工单 |
| `/dv-plan tickets` | 只从现有规格拆工单 |
| `/dv-plan` | 先 spec 后 tickets，中间停一次 |

## 流程

### A. 定稿规格

1. 读 `.devkit/specs/` 最新草稿 + `CONTEXT.md` + 相关 ADR。
2. 按模板补齐八段：背景与目标 / 范围 / 非目标 / 用户故事 / 实施决策 / 测试决策 / 未决与阻塞 / 验收标准。
3. 用户故事写成 `作为<角色>，我想要<能力>，以便<收益>`，覆盖主要路径与错误路径。
4. 实施决策写**模块与接口**，不写文件路径、不贴代码。
5. 术语一律用 `CONTEXT.md` 的词；与 ADR 冲突时停下问。

> **⏸ STOP 1**：输出规格摘要（≤20 行），问「确认定稿吗？」，等回答。

### B. 拆工单

6. 每个工单是**垂直切片**：一条路径打通 schema → 接口 → 界面 → 测试，可独立验收。
7. 每个工单声明 `blocked-by: [工单编号]`；无阻塞者可立即开工。
8. 宽重构例外：不切片，按 `expand → migrate(分批) → contract` 排，每批一个工单，最后有 `integrate-and-verify`。
9. 每个工单写明：交付什么可见行为 / 验收命令 / 涉及模块。

> **⏸ STOP 2**：输出工单清单（编号 + 标题 + blocked-by + 交付物），问「这样拆可以开工吗？」，等回答。

10. 写 `.devkit/issues/NNN-<slug>.md`，编号与 specs 共用递增序号。

## 产物

| 文件 | 说明 |
|---|---|
| `.devkit/specs/NNN-*.md` | 状态从 `草稿` 改为 `定稿` |
| `.devkit/issues/NNN-*.md` | 每个工单一个文件，含 blocked-by 与验收命令 |

模板见 `templates/spec.md` 与 `templates/ticket.md`。

## 停止条件 / 自检

- [ ] 两个 STOP 都真的停过，没有自问自答
- [ ] 规格无「待补充」「TBD」等占位
- [ ] 每个工单都能独立验收，不是「改一半」
- [ ] 依赖图无环
- [ ] 没有写代码

## 反合理化

| 我本来想说 | 现实 |
|---|---|
| 「拆分很直观，直接开工吧」 | 两个 gate 就是为了在开工前发现拆错 |
| 「这个工单顺手把下一个也做了」 | 一次一个工单，否则验收无法归因 |
| 「先写工单，规格回头补」 | 没有规格的工单，review 时 Spec 轴无从判断 |
| 「切得细一点更安全」 | 横切（按层）不是垂直切片，无法独立验收 |

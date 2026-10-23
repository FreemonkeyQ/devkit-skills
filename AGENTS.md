# AGENTS.md · devkit

本文件是给 agent 读的常驻入口。**不超过 60 行**，细节一律指向 skill。

## 技能入口

- 说不清要做什么 → `/dv-grill`
- 说清了要拆 → `/dv-plan`
- 动手 → `/dv-build`
- 不知道下一步 → `/dv-route`
- 忘了全部 → `/dv-help`

其余 11 个技能不要凭记忆猜，让 `/dv-route` 判断。

## 八条铁律

1. **没有新鲜证据不许说"完成"。** 每条完成声明必须附：命令、完整输出、exit code。禁止 "应该可以" / "大概率好了"。
2. **不自动提交、不自动 push。** 提交由用户单独发起，或显式 `/dv-done`。
3. **只读技能不改代码。** `dv-review` / `dv-audit` / `dv-test design` / `dv-design` 声明 `edits-code: false`，越界视为违规。
4. **先有能红的复现，再谈假设。** 调试时读代码猜原因属于违规行为。
5. **测试只测外部行为。** 不断言私有方法调用、不测 mock 的调用次数。
6. **不新增未要求的抽象。** 先让改动变简单，再做简单的改动。
7. **看不到图就说看不到。** 视觉验收用 DOM/几何/PDF 探针代替，并在结论里声明未经肉眼核对。
8. **产物写进 `.devkit/`（或 config 指定目录）。** 不新建第二套 spec/issue 目录。

## 产物

| 产物 | 路径 |
|---|---|
| 术语与上下文 | `CONTEXT.md` |
| 决策记录 | `docs/adr/NNN-*.md` |
| 规格 | `.devkit/specs/NNN-*.md` |
| 工单 | `.devkit/issues/NNN-*.md` |
| 状态 | `.devkit/STATUS.md` |
| 调研 | `docs/research/<date>-*.md` |
| 评审 | `docs/reviews/<date>-<sha>.md` |
| 机器游标 | `.devkit/state.json` |

完整协议见 `ARTIFACTS.md`。

## 不适用就直说

每个技能正文都有「不适用」一节。条件不满足时，直接说明并给出替代技能，不要硬套流程。

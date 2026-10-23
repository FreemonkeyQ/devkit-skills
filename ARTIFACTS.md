# ARTIFACTS.md · 产物协议

一份产物只有一个真源。本文件是路径与读写者的唯一权威，其他文档不得重复定义路径。

## 路径表

| 产物 | 默认路径 | 可覆盖 | 写入者 | 读取者 |
|---|---|:--:|---|---|
| 领域术语 | `CONTEXT.md` | 否 | `dv-grill` | grill / plan / build / review / debug |
| 决策记录 | `docs/adr/NNN-<slug>.md` | 否 | `dv-grill` / `dv-arch` | 全部研发技能 |
| 规格 | `.devkit/specs/NNN-<slug>.md` | 是 | `dv-grill`（草稿）/ `dv-plan`（定稿） | plan / build / review |
| 工单 | `.devkit/issues/NNN-<slug>.md` | 是 | `dv-plan` | build / done |
| 状态（人读） | `.devkit/STATUS.md` | 是 | `dv-context` / `dv-done` | 全部 |
| 状态（机读） | `.devkit/state.json` | 是 | 各技能收尾 / hook | hook / route / help |
| 调研 | `docs/research/<YYYY-MM-DD>-<slug>.md` | 否 | `dv-research` | grill / plan / arch |
| 评审 | `docs/reviews/<YYYY-MM-DD>-<sha>.md` | 否 | `dv-review` | verify / done |
| 审计 | `docs/audits/<YYYY-MM-DD>-<slug>.md` | 否 | `dv-audit` | done |
| 设计稿 | `docs/design/<slug>/` | 否 | `dv-design` | build / browser |
| 交接单 | `.devkit/handoff/<slug>.md` | 是 | 任意技能 | 新会话 |

「可覆盖」指可在 `.devkit/config.json` 的 `paths` 中改指到项目已有目录（例如把 spec/issue 指到 `.ai/specs`、`.ai/issues`）。

## 编号规则

- `NNN` 三位，全局递增，**specs 与 issues 共用一套序号**
- 取号方式：两个目录中最大编号 + 1
- 不复用已删除的编号

## 双写一致性

`.devkit/state.json`（机读）与 `.devkit/STATUS.md`（人读）都记录进度，但职责不同：

| 文件 | 形态 | 谁写 | 谁读 |
|---|---|---|---|
| `state.json` | JSON，8 个字段，只记游标 | 技能收尾 + hook | hook / route |
| `STATUS.md` | Markdown，阶段性叙述 | `dv-context` / `dv-done` | 人、下一个会话 |

两者不一致时：**以 `state.json` 为准判断下一步**，并在下一次 `dv-done` 时修正 `STATUS.md`。

## 不新建第二套目录

若项目已有 `.ai/`、`docs/specs/`、`specs/` 等约定，用配置改指，**不要新建并存的目录**。配置示例：

```json
{
  "paths": {
    "specs": ".ai/specs",
    "issues": ".ai/issues",
    "status": ".ai/STATUS.md",
    "state": ".devkit/state.json"
  }
}
```

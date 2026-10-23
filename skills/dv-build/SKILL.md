---
name: dv-build
description: 按工单实现代码，内含红绿重构循环与小步验证，结束时自动转入评审。用于有工单要落地、要按计划写代码、要修一个已定位的缺陷。Triggers: 开始实现, 按工单开发, 写代码, 实现这个, implement, build.
disable-model-invocation: true
user-invocable: true
metadata:
  stage: build
  reads: [.devkit/issues, .devkit/specs, CONTEXT.md, .devkit/config.json]
  writes: [代码, 测试, .devkit/state.json, .devkit/STATUS.md]
  edits-code: true
  next: [dv-review]
---

# 实现

只做当前工单。**不顺手改别处，不自动提交。**

## 适用 / 不适用

适用：工单已就绪要落地；单点修复已定位；按 spec 分阶段推进。

不适用：需求还没定 → `/dv-grill`；原因还没找到 → `/dv-debug`；只是想设计用例 → `/dv-test design`。

## 输入

- 当前工单（`.devkit/issues/NNN-*.md`）或用户口述的一段明确改动
- `.devkit/config.json` 里的 `commands`（test / lint / typecheck）
- 相关 ADR 与 `CONTEXT.md`

## 流程

1. **确认接缝**。找出这次要测试的最高已有接缝；新建接缝必须提出理由。接缝清晰写进工单的「测试决策」。
2. **红绿循环**（每个行为一次）：
   - 写一个会失败的测试，**先运行并看到它红**
   - 写最小实现让它绿
   - 重构，测试保持绿
3. **小步验证**：每完成一个行为，跑对应单测；不要攒到最后。
4. **全量一次**：工单完成时跑 `commands.test` + `lint` + `typecheck`。
5. **更新状态**：`state.json` 的 `stage=verify`、`next=/dv-review`；`STATUS.md` 追加一行。
6. **交接**：`下一步固定是 /dv-review`。若 diff <10 行且只改文案/样式，可说「可直接 /dv-done」。

## 硬约束

- **不自动 commit，不自动 push**（除非 config 里显式 `autoCommit: true`）
- 不修改工单范围外的文件
- 不新增未被要求的抽象或配置项
- 测试失败不允许用 skip / 注释掉 / 放宽断言绕过

## 自检

- [ ] 每个新行为都有一个先红过的测试
- [ ] 全量测试、lint、typecheck 均通过，附命令与退出码
- [ ] diff 只涉及当前工单的可追溯改动
- [ ] 未提交任何密钥、`.env`、构建产物
- [ ] 已更新 `state.json` 与 `STATUS.md`

## 反合理化

| 我本来想说 | 现实 |
|---|---|
| 「先写实现，测试回头补」 | 没看到红的测试，就不知道它测的是不是对的 |
| 「这个小改动不用跑全量」 | 至少跑 lint + 相关单测，全量在工单收尾时跑 |
| 「顺手把这个重复代码也重构了」 | 记录成新工单，不在本次范围 |
| 「测试挂了但和这次改动无关」 | 先确认基线是否本来就红，写在报告里，不静默忽略 |
| 「改完直接提交吧」 | 提交是 `/dv-done` 的职责，且需用户确认 |

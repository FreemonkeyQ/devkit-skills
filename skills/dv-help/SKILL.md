---
name: dv-help
description: 'devkit 技能手册，列出全部技能、查某一条怎么用、看主流程与场景示例、判断值不值得用技能、排查没触发的问题。用于「有哪些技能」「X
  怎么用」「什么时候用」「什么时候没必要用」「devkit 怎么上手」。Triggers: 帮助, 怎么用, 有哪些技能, 什么时候用, devkit help, 手册, cheatsheet.'
user-invocable: true
metadata:
  stage: meta
  summary: 查询技能和推荐用法
  effects: []
  explicit-actions: []
  next: []
---

# 推荐用法说明

## 适用 / 不适用
查看技能、具体用法、推荐流程、判断某项任务值不值得上技能链和排错时使用。复杂任务执行与持续推进交 dv-route；help 自己不改文件或运行发布动作。

## 用法
- 无参数：从 references/_generated.md 读取实际技能数与总表，先说明“说任务即可，无需记命令”，默认简短说明主路径；仅用户要全部技能时展开全表。
- `<name>`：支持 build 或 dv-build；读取该技能正文，解释作用、适用/不适用、示例提示词、产物、授权和可选后续。
- `--usage`：读取 references/usage.md，给出用/不用判据、代价与不确定性组合、成本实测和默认姿势；用户问“什么时候用”“有没有必要”时直接使用。
- `--flow`：展示 guide.md 的场景路径，声明不是强制阶段或执行引擎。
- `--scenarios`：展示自然语言需求、代码实施、只分析、提交、推送、CI跟踪、发布验收的区别。
- `--cost`：只报告估算口径或宿主提供的实际统计，不把字符除3称为精确常驻。
- `--trouble`：从 guide.md 排查路径、调用能力、配置与旧插件冲突；不擅自安装或修改全局设置。
- 自然触发不稳定：实现类任务需要 `dv-build` 约束时，建议显式点名或用 route 链路，不要把“没自动调用”判断成技能不存在。
- 显式入口：优先用 `/dv <目标>`（命令模板 `commands/dv.md`）；需要安装到宿主时运行 `python3 scripts/install_entry.py --host claude|qoder --apply`。
- 连续执行：目标模式用 `scripts/devkit_run.py` 生成 plan/context/acceptance，`next` 推进，`record` 留证；`dv-done` 前用 `devkit_gates.py` 跑真实门禁。

## 技能交接
收尾给三行：已完成；建议下一步（有 metadata.next 时选 1 个默认，可附 1 个备选）；需用户决定的事。用户确认即直接调用下一步，不重复完整侦察；目标式委托与停车闸门见 dv-route 的链路模式。

## 产物与自检
只输出说明。读取生成表避免名单漂移；next 是候选图，不是强制序列，逐步确认后才推进。可以给简单用法推荐，无需机械拒绝“该用哪个”；判断用/不用时给判据和取舍，不把每件事都说成必须走链路；需要连续执行时转 route 的目标模式。

---
name: dv-help
description: 'devkit 技能手册，列出全部技能、查某一条怎么用、看主流程与场景示例、排查没触发的问题。用于「有哪些技能」「X 怎么用」「devkit
  怎么上手」。Triggers: 帮助, 怎么用, 有哪些技能, devkit help, 手册, cheatsheet.'
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
查看技能、具体用法、推荐流程和排错时使用。复杂任务执行与持续推进交 dv-route；help 自己不改文件或运行发布动作。

## 用法
- 无参数：从 references/_generated.md 读取实际技能数与总表，先说明“说任务即可，无需记命令”，默认简短说明主路径；仅用户要全部技能时展开全表。
- `<name>`：支持 build 或 dv-build；读取该技能正文，解释作用、适用/不适用、示例提示词、产物、授权和可选后续。
- `--flow`：展示 guide.md 的场景路径，声明不是强制阶段或执行引擎。
- `--scenarios`：展示自然语言需求、代码实施、只分析、提交、推送、CI跟踪、发布验收的区别。
- `--cost`：只报告估算口径或宿主提供的实际统计，不把字符除3称为精确常驻。
- `--trouble`：从 guide.md 排查路径、调用能力、配置与旧插件冲突；不擅自安装或修改全局设置。

## 产物与自检
只输出说明。读取生成表避免名单漂移；next 是可选关联，不是强制下一步。可以给简单用法推荐，无需机械拒绝“该用哪个”；需要执行时转 route。

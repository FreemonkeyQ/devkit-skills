---
name: dv-help
description: devkit 技能手册，列出全部技能、查某一条怎么用、看主流程与场景示例、排查没触发的问题。用于「有哪些技能」「X 怎么用」「devkit 怎么上手」。Triggers: 帮助, 怎么用, 有哪些技能, devkit help, 手册, cheatsheet.
disable-model-invocation: true
user-invocable: true
metadata:
  stage: meta
  reads: [references/_generated.md, references/guide.md, .devkit/config.json]
  writes: []
  edits-code: false
  next: []
---

# devkit 手册

只讲怎么用，不替你决定下一步——要决策用 `/dv-route`。

## 适用 / 不适用

适用：想知道有哪些技能；查某个技能怎么用；看主流程；排查为什么没触发。

不适用：不知道下一步做什么 → `/dv-route`；已决定要做什么 → 直接执行。

## 参数

| 调用 | 输出 |
|---|---|
| `/dv-help` | 首屏：3 个入口 + 总表 + 主流程 |
| `/dv-help <name>` | 单条：是什么 / 何时用 / 何时别用 / 产物 / 下一步 |
| `/dv-help --flow` | 主流程 + on-ramp，只画图 |
| `/dv-help --scenarios` | 5 个场景：真实提示词 → 自动链 |
| `/dv-help --cost` | 常驻与触发 token |
| `/dv-help --trouble` | 没触发 / stage 卡住 / hook 未注入 |

## 首屏（无参数时只输出这一段，到此停止）

```
devkit · 16 个技能，你只需记 3 个

说不清        → /dv-grill
说清了要拆     → /dv-plan
动手          → /dv-build

其余 13 个：4 个自己会来（route / debug / research / review），
9 个季节型——想不起来就 /dv-route，或 /dv-help --flow
```

随后从 `references/_generated.md` **原样贴出总表**，不增删列、不改写措辞。

## 单条模式

固定五段，缺一段算未完成：

1. **是什么** —— 一句，不复述 description 原文
2. **什么时候用** —— 2–3 条具体场景
3. **什么时候别用** —— 每条必须指向替代技能
4. **跑完留下什么** —— 产物路径 + 谁读它
5. **下一步** —— 从该技能 `metadata.next` 读，禁止手写

## 硬约束

- 不读代码、不改文件、不写 `state.json`
- 总表与流程图**只从 `_generated.md` 读**，不手抄（手抄必漂）
- 单条模式不展开该技能的 `references/` 正文
- 用户说「我该用什么」→ 一句话转 `/dv-route`，不在这里做路由

## 自检

- [ ] 首屏是否只有一段 + 一张表
- [ ] 总表列数与 `_generated.md` 一致
- [ ] 单条模式五段齐全
- [ ] 下一步是否来自 frontmatter，而非凭空生成
- [ ] 是否误做了路由决策

## 反合理化

| 我本来想说 | 现实 |
|---|---|
| 「我凭记忆列一下有哪些技能」 | 手抄必漂，只从 `_generated.md` 读 |
| 「顺便帮他判断该用哪个」 | 那是 `/dv-route` 的职责 |
| 「多说两句这个技能的原理」 | 手册只讲怎么用，原理在技能正文里 |
| 「没有总表，我直接写一个」 | 先跑 `scripts/dv-help-gen.py` |

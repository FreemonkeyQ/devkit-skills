---
name: dv-author
description: 新建、修改、评估 devkit 技能本身，检查描述触发准确度并淘汰长期闲置技能。用于加新技能、改现有技能、技能没被触发、技能太多想精简。Triggers: 新建技能, 改技能, 技能没触发, 精简技能, author, meta.
disable-model-invocation: true
user-invocable: true
metadata:
  stage: meta
  reads: [skills/, DESIGN.md, 使用统计]
  writes: [skills/, DESIGN.md, ARTIFACTS.md]
  edits-code: true
  next: []
---

# 技能维护

只改 devkit 自己，不改业务代码。

## 适用 / 不适用

适用：加技能；改技能正文或描述；技能该触发时没触发；技能多到记不住想砍。

不适用：要用技能做事 → `/dv-route`；要看怎么用 → `/dv-help`。

## 流程

### A. 新建

1. **先问必要性**：这个能力能否由现有技能加一节解决？能，就不新建。**新技能必须通过「不能被现有技能覆盖」的检验。**
2. 选 `stage` 与 `edits-code`；确定 `next`（指向谁，或 `[]`）。
3. 按 `DESIGN.md` 第 4 节的骨架写正文，**≤120 行**。
4. 描述只写 WHAT + WHEN，不写 HOW（Description Trap）。中文主句 ≤60 字 + 英文 Triggers。
5. 若是 L2（仪式），三键齐发 + `agents/openai.yaml`。
6. 跑 `python3 scripts/lint.py`，再跑 `python3 scripts/dv-help-gen.py` 更新总表。

### B. 修改

1. 读现有正文与产物，确认改动不破坏 `next` 图。
2. 只改必要段落；增行要同时删行，保持 ≤120 行。
3. 重跑 lint 与生成脚本。

### C. 触发不准

1. 收集 3–5 条「该触发没触发」的真实原话。
2. 把原话里的特征词补进 Triggers；同时删掉会误触发的通用词（如「看」「这个」）。
3. 用这 3–5 条原话回归：命中率与误触发率各记一次。

### D. 30 天淘汰

1. 读使用统计（Claude Code `~/.claude.json` 的 `skillUsage`；其他端手工记录）。
2. 连续 30 天为 0 次的技能，列出来问用户：保留 / 移到 `in-progress/` / 删除。
3. 移到 `in-progress/` 时在 `DESIGN.md` 标注，不直接删除。

## 硬约束

- 不新增超过 120 行的正文
- 不为「以后可能用得上」加技能或字段
- 淘汰决策必须由用户确认

## 自检

- [ ] 新技能通过了「不能被现有技能覆盖」检验
- [ ] lint 通过
- [ ] `_generated.md` 已重新生成且 git diff 无漂移
- [ ] 淘汰清单已让用户确认

## 反合理化

| 我本来想说 | 现实 |
|---|---|
| 「再加一个技能更清晰」 | 每加一个，记忆负担和常驻 token 都涨 |
| 「描述写详细点更容易触发」 | 写了流程，模型只读描述不读正文 |
| 「反正没人用，先留着」 | 闲置技能会稀释触发准确度 |

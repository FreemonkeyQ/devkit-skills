---
name: dv-context
description: 把 devkit 接入一个仓库：生成配置、补 AGENTS.md 技能段、建状态文件，并核对既有目录约定。用于新仓首次接入、状态与配置不一致、SKILL 没按预期工作。Triggers: 接入, 初始化devkit, 配置devkit, setup, onboard, 状态不一致.
disable-model-invocation: true
user-invocable: true
metadata:
  stage: meta
  reads: [AGENTS.md, CLAUDE.md, .devkit/config.json, .devkit/state.json, git remote]
  writes: [.devkit/config.json, AGENTS.md, .devkit/STATUS.md, .devkit/state.json]
  edits-code: false
  next: []
---

# 接入与配置

一次性动作。之后只在配置或状态漂移时重跑。

## 适用 / 不适用

适用：新仓库首次用 devkit；要改产物路径；`STATUS.md` 与 `state.json` 不一致；技能没按预期触发。

不适用：要改技能本身 → `/dv-author`；不知道下一步 → `/dv-route`。

## 流程

### 1. 探查（先看再问）

读：`git remote -v` / `AGENTS.md` / `CLAUDE.md` / 是否存在 `.ai/` `docs/specs/` `specs/` / 包管理器与脚本 / 现有测试目录与运行方式 / 是否有工作树目录约定。

### 2. 逐节确认（一节一问，先给推荐）

**A. 产物路径**
> 仓库里已经有 `.ai/specs`、`.ai/issues`，建议直接指过去，不新建 `.devkit/specs`。确认吗？

选项：沿用已有目录（推荐） / 用 `.devkit/` / 其他路径。

**B. 命令**
从脚本里推断 `test` / `testUnit` / `lint` / `typecheck` / `dev`，逐条让用户确认。推断不出来就问。

**C. Git 习惯**
分支前缀、工作树目录、是否允许自动提交（默认否）。

**D. 语言**
技能正文与产物语言（默认中文）。仅影响新生成文档。

### 3. 写入

- `.devkit/config.json`（按 `.devkit/config.schema.json`）
- `AGENTS.md`：只在没有「## 技能」段时追加，已有则只更新该段，不动其他内容
- `.devkit/STATUS.md`（或配置指定路径）：骨架 + 当前状态
- `.devkit/state.json`：`stage: idle`

### 4. 验证

- `python3 scripts/lint.py`（若在 devkit 仓库内）
- 打印配置摘要与产物路径，让用户看一遍

## 硬约束

- 绝不覆盖已有的 `AGENTS.md` 正文，只增删自己的段
- 不创建与已有目录并存的第二套
- 不修改项目代码

## 自检

- [ ] 四节都问过，没有替用户决定
- [ ] 路径指向已存在目录时，确认过不是空目录冲突
- [ ] `AGENTS.md` 只增了自己的段
- [ ] 配置能通过 schema 校验

## 反合理化

| 我本来想说 | 现实 |
|---|---|
| 「默认用 .devkit 就行，不用问」 | 项目已有约定时会造成两套目录 |
| 「AGENTS.md 我重写一版更整齐」 | 那里面可能有用户的规则 |
| 「命令我猜一个，错了再改」 | 猜错会让后续验证全假 |

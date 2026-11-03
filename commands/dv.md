---
description: 按目标编排 devkit 链路
---

请根据 dv Skill(s) 链路执行。目标：

$ARGUMENTS

开工前：
1. 读取项目 `.devkit/project.json`；没有就调用 `dv-context` 生成，不要先写业务代码。
2. 读取 `${CLAUDE_PLUGIN_ROOT}/skills/dv-route/references/chain.md`。
3. 用 `dv-route` 判断风险与终点，默认到 `done`；用户明确写 commit/push 才加入对应步骤。

创建运行上下文：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/devkit_run.py --root . init --goal "$ARGUMENTS"
```

之后只处理 `next` 返回的技能，按 `plan.json` 的 scope、authorization、gates 执行；每个技能结束用 `record` 记录 pass/blocked 和证据。`dv-done` 前必须先跑：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/devkit_gates.py --root . --run <run> run
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/devkit_gates.py --root . --run <run> check
```

未通过的门禁、未闭合的验收项不能标记 done；不要自行 commit/push，除非 plan.authorization 明确允许。

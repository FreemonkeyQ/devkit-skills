---
name: dv-review
description: '分别从正确性、项目规范、原始需求三条轴独立评审改动，各轴分开报告不合并。用于审 diff、提交前检查、开合并请求前复查、看这次改动有没有实现原意。Triggers:
  评审, review, 审diff, 提交前检查, 看看这次改动, code review.'
user-invocable: true
metadata:
  stage: verify
  summary: 三轴评审含未提交改动
  effects:
  - docs
  explicit-actions: []
  next:
  - dv-build
  - dv-done
---

# 三轴改动评审

## 适用 / 不适用
提交前、分支/MR、指定提交与工作中改动。只审查不改业务源码，修复交build；全库健康用audit。

## 范围与流程
1. 固定范围与基线，记录HEAD和文件列表。默认本次任务变更，不把既有无关脏文件加入。
2. 工作区评审：`git status --porcelain=v1 -z`、`git diff`、`git diff --cached`、必要时`git diff HEAD`；读取任务相关未跟踪文件（排除敏感/生成/依赖）。未提交改动不能仅用`<base>...HEAD`。
3. 分支评审用`git diff <base>...HEAD`；指定提交范围使用用户语义，单提交可用git show。若无法确定基线先查项目/分支，仍有歧义才问。全新仓库无HEAD时按新文件评审。
4. 固定证据快照（报告不包含密钥），评审中代码变化则重新验证范围。需求可来自当前明确指令/规格/工单，不强制每项都有spec文件。
5. 三轴独立：Correctness找实际Bug（输入/状态→错误结果）；Standards依据项目文档，审美/代码味道为建议，不冒充Bug；Spec找缺失/超范围/错误实现。有缺失依据标unknown而非假通过。
6. 大任务有宿主子代理可并行，否则串行三轴降级，不依赖某个工具名。每项保留证据、反例与置信度，复核误报，允许零发现。
7. 输出每轴结果，去掉重复噪音但保留分类；关键风险摘要可跨轴概述，不掩盖各轴。报告命令、范围、遗漏与验证限制。

## 自检
未提交/暂存/新文件是否包含？是否尊重既有改动？正确性判断不能因仓库“规范”允许就忽略真实Bug；工具已检查不代表运行过。评审不commit/push。

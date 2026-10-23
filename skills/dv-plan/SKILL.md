---
name: dv-plan
description: '把已谈定的内容定稿为规格，再拆成可独立交付的垂直切片工单并声明依赖。用于已有结论要形成可执行计划、或要把 spec 拆任务。Triggers:
  写spec, 拆任务, 出工单, 拆ticket, plan, breakdown.'
user-invocable: true
metadata:
  stage: discover
  summary: 方案定稿与任务拆解
  effects:
  - docs
  explicit-actions: []
  next:
  - dv-build
  - dv-test
---

# 方案与可执行拆解

## 适用 / 不适用
综合已确认方案为规格、实施步骤或工单；不重新访谈。重大未决问题交 grill；小而明确的修改可直接 build，不必初始化tracker。

## 模式与流程
1. `spec` 只生成方案；`tickets` 从方案拆任务；默认按实际规模决定是否需要两者。
2. 确认目标、范围、非目标、规则来源、接口/数据影响、风险与验收。按需记录兼容、迁移、回滚；精确契约或关键原型片段可保留，易过时文件位置放实施任务中。
3. 已确认方案不重复审批；新提出的重要方案在开工前确认。用户只要分析时不写代码、不创建远程工单。
4. 分解为连贯、可验收的垂直切片，标依赖和每步验证；不要按前端/后端/测试机械拆开。宽迁移可expand/migrate/contract，每批说明兼容与回滚。
5. 用户已授权按方案实施且细分不改变范围时可以继续；存在新取舍才停。保存工单或远程发布仅在用户/项目规则授权后进行。
6. 沿用现有目录、编号与任务约定；无约定时用配置路径和 `references/spec.md`、`references/ticket.md`。改存量行为且已有现状规格时优先变更提案（模板见 dv-arch）。并行取号需锁/唯一编号，不宣称扫描最大值并发安全。
7. 落盘后提示运行 `scripts/check-docs.py --project <根>`；`profile=off` 时不宣称已校验。

## 自检
每条任务有可观察交付、依据与验证；无循环依赖；未定项不装作已定。不能用“下一步build”绕过“先不要实现”。

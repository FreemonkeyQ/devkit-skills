<!-- GENERATED: scripts/dv-help-gen.py -->

共 18 个技能。自然语言可选技能，副作用由当次授权控制。

| 技能 | 作用 | 能力范围 | 需明确意图的动作 | 可选关联 |
|---|---|---|---|---|
| dv-arch | 架构与兼容迁移方案 | docs | 依任务范围 | dv-plan, dv-build |
| dv-audit | 风险与测试有效性审计 | docs | 依任务范围 | dv-test, dv-build, dv-done |
| dv-author | 维护技能与评估质量 | docs, tests, business-code | 依任务范围 | — |
| dv-browser | 真实Web与桌面UI验收 | docs, tests | 依任务范围 | dv-build, dv-done |
| dv-build | 授权范围内实施 | docs, tests, business-code | 依任务范围 | dv-review, dv-done |
| dv-commit | 按功能规范本地提交 | docs | commit | dv-push |
| dv-context | 接入配置与路径核对 | docs | 依任务范围 | — |
| dv-debug | 基于证据诊断修复 | docs, tests, business-code | 依任务范围 | dv-review, dv-done |
| dv-design | 界面视觉交互设计 | docs, prototype | 依任务范围 | dv-build, dv-browser |
| dv-done | 验证汇报与可选发布验收 | docs | 依任务范围 | dv-commit, dv-push |
| dv-grill | 澄清需求与记录决定 | docs | 依任务范围 | dv-plan, dv-design |
| dv-help | 查询技能和推荐用法 | 只读说明 | 依任务范围 | — |
| dv-plan | 方案定稿与任务拆解 | docs | 依任务范围 | dv-build, dv-test |
| dv-push | 提交后推送与CI跟踪 | docs | commit, push | dv-commit, dv-done |
| dv-research | 一手证据调研 | docs | 依任务范围 | dv-plan, dv-arch |
| dv-review | 三轴评审含未提交改动 | docs | 依任务范围 | dv-build, dv-done |
| dv-route | 按目标选择最短研发路径 | 只读说明 | 依任务范围 | dv-help |
| dv-test | 业务用例与测试执行 | docs, tests | 依任务范围 | dv-build, dv-review, dv-audit |

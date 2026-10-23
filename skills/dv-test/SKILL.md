---
name: dv-test
description: 设计业务用例或编写运行测试，按用户目标选择模式；执行中允许补必要场景，不自动改业务实现。
user-invocable: true
metadata:
  stage: verify
  summary: 业务用例与测试执行
  effects:
  - docs
  - tests
  explicit-actions: []
  next:
  - dv-build
  - dv-review
  - dv-audit
---

# 用例设计与测试执行

## 适用 / 不适用
设计业务场景、补测试、执行与维护测试。真实Bug修复用debug/build；有效性审计用audit；真实UI验收用browser。

## 模式
- `design`：读取规则与现有设施，输出用例/覆盖缺口，不写测试代码或运行工具。
- `run`：写/跑测试与报告；可补必要场景和断言，不重新展开完整需求规划；不改业务实现，发现实现Bug交debug/build。
- 无参数时从用户动词选择；歧义才问。

## 流程
1. 规则来源优先于实现；明确权限、状态、输入、期望结果及必须/禁止副作用。关键规则编号方便追溯。
2. 确认项目实际框架、运行入口、fixture、依赖边界与版本；无设施时给手工/替代验证，不凭依赖文件假定工具能运行。
3. 按适用性推正常、错误、边界、并发、重复、取消、恢复用例；参考 references/scenarios.md。run阶段允许补最少必要输入以写出有意义断言。
4. 使用现有风格与 references/language-testing.md。避免只测mock；幂等/重试/副作用契约可验证关键调用次数。集成测试可使用隔离真实数据库，不混淆单元mock与集成依赖。
5. 执行记录命令、环境、退出码、关键输出；失败区分环境、flaky、断言或实现。隔离flaky须记录原因和修复计划，不“重跑到绿”掩盖失败。
6. 报告规则覆盖、执行结果、缺口与相关完整日志位置。覆盖率不代表正确性；性能/安全测试参考 references/performance-security.md。

## 自检
不安装新框架、不用生产数据或对生产压测；需要额外权限先确认。design文档和run测试代码权限明确，测试期望不能仅因为当前实现如此就定义为正确。

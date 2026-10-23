# 语言测试与执行参考

工具名称是示例。先检查实际配置、版本、代表性用例和有效命令，不假定已安装。

## Java
JUnit/Mockito/AssertJ用于单元；Spring slice/MockMvc/WebTestClient匹配实际栈。
Testcontainers仅在隔离Docker/许可可用时用；事务回滚测试不代表真实提交后行为和多连接并发。
Maven/Gradle verify可能含集成检查，按项目入口执行。PIT只在既有配置存在时审计。

## Python
pytest fixtures/factories、monkeypatch跟已有测试组织；async框架匹配event loop。
时间/随机/外部服务隔离；Hypothesis仅现有依赖且契约适合时使用。
集成DB使用固定可删除测试库，不使用生产DSN；coverage与mutmut报告范围不同。

## Go
原生testing/table-driven/subtests；httptest验证HTTP边界；race/fuzz按资源与项目命令适用。
并行测试隔离全局环境/文件/端口；cancel之后goroutine真的退出。
testify若已有才使用。突变工具成熟度和支持范围需实际确认，不保证等价JS/Java方案。

## JS/TS
Jest/Vitest组件/函数；Playwright等E2E沿用已有基础设施。
等待可观察状态而非固定sleep；网络mock和真实API分开标注。
Stryker只有既有配置才运行。DOM通过不代表布局、渲染或OS窗口正确。

## 边界与断言
单元隔离外部副作用；集成可以用真实隔离依赖；E2E验证跨层。
允许验证关键副作用次数（重试、幂等、事件发一次）；避免测私有细节/纯mock而无业务观察。
报告包含命令/版本/环境/退出码/通过失败跳过/日志位置、规则与代码覆盖差别。

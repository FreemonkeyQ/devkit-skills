# 新项目脚手架

先确认是不是新项目：没有 manifest、没有测试入口、没有既有模块结构，或用户明确说“新仓库 / 从零开始”。

## 顺序

1. **先确认栈**：用户没说语言时先问，不要替用户默认。用户说“你定”时，选维护活跃、团队已有经验的栈，并说明理由。
2. **用官方或社区 starter**：不要手写多文件骨架，不要自己发明目录结构。生成器负责版本、构建、测试入口和基础配置。
3. **锁版本**：生成后读 manifest/lockfile，保留生成器给的版本；不顺手升级，不引入生成器之外的框架。
4. **读生成结果**：确认构建、测试、lint、运行命令；把真实可用命令记录下来，未安装的不要写成已验证。
5. **最小结构起步**：只建当前需求需要的文件；不预建 controller/service/repository/domain 全套，不提前抽共享层。
6. **验证**：运行 starter 自带的测试/lint；没有测试就写一个最小行为测试。记录实际命令和结果。

## 语言 starter 选择

| 语言/场景 | 首选 | 备注 |
|---|---|---|
| Java / Spring Boot | Spring Initializr（Web、JPA、Flyway 等按需勾选） | 保留 Maven/Gradle wrapper 与生成版本 |
| Kotlin / JVM | Spring Initializr 或 `gradle init` | 不混用两套构建 |
| Python 应用/CLI | `uv init`（需要打包时加 `--package`） | 用 `pyproject.toml` + `uv.lock`；不手写 setuptools 骨架 |
| Python 数据/脚本 | `uv init` + 最小依赖 | 标准库够用就不加框架 |
| Go | `go mod init <module>` + 标准布局 | 需要 HTTP 时再引框架，不预建 `internal/` 全套 |
| TS/JS 前端 | `npm create vite@latest` / 框架官方 CLI | 保留 lockfile；不手写 bundler 配置 |
| Node 后端 | `nest new` / 框架官方 CLI | 不手写 tsconfig/构建链 |
| .NET | `dotnet new webapi` / `dotnet new console` | 保留 SDK 版本与项目文件 |
| Rust | `cargo new` | 需要异步/DB 时再逐项加 crate |
| PHP | `composer create-project` / Laravel installer | 保留 composer.lock |
| 移动端 | Expo / Flutter / 官方 CLI | 按目标平台选择，不跨栈拼装 |

工具名是示例，以当前环境和官方文档为准。不要在本仓库维护语言模板；模板会随版本腐烂，维护选择表即可。

## 不要做

- 不要为了“完整”预建分层、接口、抽象基类、DI 容器、CI、ORM。
- 不要手写构建配置来替代官方生成器。
- 不要在新项目里复制旧项目的架构，除非用户明确要求。
- 不要把“计划创建”说成“已经创建”；未执行就写明未执行。

## 记录

- 选型非显然（例如同语言有多个主流框架）时，记一条 ADR：选项、决定、后果。
- 普通项目只在回答里说明“用了哪个 starter、哪条命令、锁了什么版本”，不额外造文档。

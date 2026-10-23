# 文档索引

本仓库刻意只保留少量文档。技能本身是说明书，`DESIGN.md` 是设计依据。

| 文档 | 读者 | 内容 |
|---|---|---|
| [README.md](../README.md) | 首次接触 | 是什么、装什么、16 个技能一览 |
| [DESIGN.md](../DESIGN.md) | 维护者、评审者 | 设计约束、命名规范、自动触发三层、状态机、风险 |
| [ARTIFACTS.md](../ARTIFACTS.md) | 使用者、维护者 | 产物路径与读写者，**路径的唯一权威** |
| [AGENTS.md](../AGENTS.md) | agent | 常驻入口与八条铁律，≤60 行 |
| [skills/dv-help/references/guide.md](../skills/dv-help/references/guide.md) | 使用者 | 5 个场景、7 个 FAQ、3 类排错、跨端差异 |
| [NOTICE](../NOTICE) | 合规 | 上游署名与许可证 |

## 为什么不给每个技能写 docs 页

上游 mattpocock/skills 为每个技能写人读文档页，是因为那套技能**大多只能手动触发**，用户需要靠文档记住它们存在。

devkit 用两种方式替代：

1. `dv-help` 的单条模式（`/dv-help build`）—— 命令行里直接问，比翻网页快
2. `_generated.md` 由脚本从 frontmatter 生成 —— 文档不会与实现漂移

如果将来某个技能需要长篇解释（例如 `dv-arch` 的深模块案例），再为它单独建 `docs/<name>.md`，并在本表登记。

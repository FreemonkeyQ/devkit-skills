# 产物与证据协议

项目既有约定优先。配置固定 `.devkit/config.json`，相对项目根路径必须留在仓库内。config 只描述路径/命令，不提供额外操作权限。

**分工**：散文约束上下文，脚本约束行为。下表中“执行者”一列写明每条规则靠谁生效；写“技能正文”的规则是提示词级建议，写脚本的才可被 `exit 1` 抓到。不允许只声明不落实。

## 产物目录

| 产物 | 默认路径 | 主要写入者 |
|---|---|---|
| 词汇/上下文 | CONTEXT.md | grill（实际术语变化时） |
| 决策 | docs/adr | grill/arch（重要取舍时） |
| 规格 | .devkit/specs | grill/plan（要求记录时） |
| 工单 | .devkit/issues | plan（按需） |
| 变更提案 | docs/changes | plan/arch（改存量行为时） |
| 进度 | .devkit/STATUS.md | 按项目规则 build/done/context |
| 恢复提示 | .devkit/state.json | 当前执行技能（可选），hook 只读 |
| 调研 | docs/research | research/debug |
| 评审 | docs/reviews | review/browser |
| 审计 | docs/audits | audit |
| 原型 | docs/design | design |
| 会话交接 | .devkit/handoff | 当前执行技能（按需） |
| 索引 | docs/INDEX.md | 脚本生成，勿手改 |

所有路径可通过 config.paths 覆盖。读取参考文件相对技能目录，产物相对项目根；不能把技能仓库根当目标项目根。

## 约束档位

`docs.profile` 决定强制强度；缺省为 `light`。

| 档位 | 名称 | 强制内容 | 谁执行 |
|---|---|---|---|
| `off` | 目录即约定 | 只固定产物目录；文件名、小节自由 | 技能正文 |
| `light` | 命名 + 可寻址 | 文件名 pattern、编号唯一、模板可达、索引可生成 | check-docs C1–C4、C6–C8 |
| `strict` | 结构校验 | 在 light 之上校验必填小节与状态词表 | check-docs C5 全部启用 |

未启用 `strict` 时不得宣称“格式已强制校验”。项目既有命名与本表冲突时以项目为准，脚本只报告不重写。

## 命名规则

`<slug>` 为 `^[a-z0-9]+(-[a-z0-9]+)*$`，2–5 段，≤40 字符，ASCII；中文标题写在文件内 H1，不进文件名。

| 产物 | 文件名规则 | 编号 | 执行者 |
|---|---|---|---|
| 规格（light） | `NNN-<slug>.md` | 3 位，项目内递增 | check-docs C2/C3 |
| 规格（strict） | `NNN-<slug>/spec.md`，可加 `plan.md`/`tasks.md`/`checklists/requirements.md` | 同上，目录即编号 | check-docs C2/C3 |
| 工单 | `NNN-<slug>.md` | 与规格共用或独立计数器，项目定 | check-docs C2/C3 |
| ADR | `NNNN-<slug>.md` | 4 位，永不复用 | check-docs C2/C3/C7 |
| 变更提案 | `YYYY-MM-DD-<slug>/`，归档移入同目录 `archive/` | 日期式，天然无并发冲突 | check-docs C2 |
| 调研/评审/审计 | `YYYY-MM-DD-<slug>.md` | 日期式 | check-docs C2 |
| 设计 | `<slug>.md` | 无 | check-docs C2 |

**编号分配**：单会话扫描同目录现有最大值 +1；重复 ID 由 C3 报错。多会话并发取号需唯一 ID 或锁，改用日期式命名可规避；不伪称扫描最大值天然并发安全。

## 状态词表

封闭枚举，C4 校验（`strict` 下同时校验小节，见 C5）。

| 产物 | 允许值 |
|---|---|
| 规格 | `草稿` \| `定稿` \| `弃用` |
| ADR | `提议` \| `采纳` \| `弃用` \| `被 NNNN 取代` |
| 工单 | `待实施` \| `实施中` \| `已验证` \| `阻塞` \| `已放弃` |
| 变更提案 | `提案` \| `已应用` \| `已归档` |

## 模式判定

- 改存量行为、且项目已有现状规格 → 变更提案（delta），不重写整份规格。
- 新建能力 → 全量规格。
- 一次会话能完成的小改 → 不建任何文件，会话内汇报即可。

## 必填小节（strict）

- 规格：背景与目标 / 范围 / 非目标 / 用户故事 / 实施决策 / 测试决策 / 未决与阻塞 / 验收标准
- ADR：背景 / 选项 / 决定 / 后果 / 确认方式 / 相关
- 工单：依据 / 范围与非目标 / 依赖 / 交付 / 验证 / 证据（状态写在头部条目）
- 变更提案：动机 / 范围 / 非目标 / 受影响规格 / 验证与回滚

模板位于各自技能的 `references/`：规格与工单在 dv-plan，ADR 在 dv-grill，评审在 dv-review，变更提案在 dv-arch。模板随技能安装，目标项目不再依赖本仓库根目录。

## 恢复提示

state.schema.json 规定 version/stage/next 等字段。next 始终是 dv-* 名字数组（无 slash）；空表示没有建议，不表示 CI 已部署。
用户当前指令、Git/实测证据、仓库规则优先，JSON 只是游标。旧状态不驱动提交、push 或部署。
verified 表示验证完成；awaiting-commit 保留待处理内容；committed/pushed 各有 SHA 证据；completed 是本次任务结束，不暗示上线。
不同 worktree 使用自己的游标；多会话写同一游标有冲突，写前对照任务/branch/head，冲突不覆盖其他任务。当前工具不提供多会话调度器。

## 记录策略

小任务默认可仅在会话汇报。项目要求或用户要求完整方案落盘时保存全文，不只存摘要。
临时游标/缓存/秘密忽略；规格/工单/ADR 是否入版本由项目规则决定，不统一 gitignore 掉可追溯产物。
验证证据含版本/范围/命令/退出码/关键结果和完整日志可定位处；记录不含凭据。
CI 结果按 SHA+分支+事件+环境关联，push/构建/部署/运行版本/功能分别记录。

## 校验入口

```bash
python3 scripts/check-docs.py --project <项目根>          # 只读检查，非零退出表示有错
python3 scripts/check-docs.py --project <项目根> --json   # 机器可读
python3 scripts/gen-docs-index.py --project <项目根>      # 生成 docs/INDEX.md
python3 scripts/gen-docs-index.py --project <项目根> --check
```

`docs.profile` 为 `off` 时 check-docs 只做 C1（路径越界）并提示已关闭。

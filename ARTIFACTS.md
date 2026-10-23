# 产物与证据协议

项目既有约定优先。配置固定 `.devkit/config.json`，相对项目根路径必须留在仓库内。config只描述路径/命令，不提供额外操作权限。

| 产物 | 默认路径 | 主要写入者 |
|---|---|---|
| 词汇/上下文 | CONTEXT.md | grill（实际术语变化时） |
| 决策 | docs/adr | grill/arch（重要取舍时） |
| 规格 | .devkit/specs | grill/plan（要求记录时） |
| 工单 | .devkit/issues | plan（按需） |
| 进度 | .devkit/STATUS.md | 按项目规则build/done/context |
| 恢复提示 | .devkit/state.json | 当前执行技能（可选），hook只读 |
| 调研 | docs/research | research/debug |
| 评审 | docs/reviews | review/browser |
| 审计 | docs/audits | audit |
| 原型 | docs/design | design |
| 会话交接 | .devkit/handoff | 当前执行技能（按需） |

所有上述路径可通过config.paths覆盖。读取参考文件相对技能目录，产物相对项目根；不能把技能仓库根当目标项目根。

## 恢复提示
state.schema.json规定version/stage/next等字段。next始终是dv-*名字数组（无slash）；空表示没有建议，不表示CI已部署。
用户当前指令、Git/实测证据、仓库规则优先，JSON只是游标。旧状态不驱动提交、push或部署。
verified表示验证完成；awaiting-commit保留待处理内容；committed/pushed各有SHA证据；completed是本次任务结束，不暗示上线。
不同worktree使用自己的游标；多会话写同一游标有冲突，写前对照任务/branch/head，冲突不覆盖其他任务。当前工具不提供多会话调度器。

## 记录策略
小任务默认可仅在会话汇报。项目要求或用户要求完整方案落盘时保存全文，不只存摘要。
临时游标/缓存/秘密忽略；规格/工单/ADR是否入版本由项目规则决定，不统一gitignore掉可追溯产物。
编号沿用项目；无约定单会话取已有最大值+1，多会话需唯一ID或锁，不能伪称并发安全。
验证证据含版本/范围/命令/退出码/关键结果和完整日志可定位处；记录不含凭据。
CI结果按SHA+分支+事件+环境关联，push/构建/部署/运行版本/功能分别记录。

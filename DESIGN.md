# devkit-skills v0.3.3 设计

## 目标
统一dv-命名、个人开源、覆盖研发全程。技能选择交给模型，重要决定与副作用授权留给用户。不是强制流水线，不为满足阶段数量而制造文档。当前19个技能，不新增dv-deploy。

## 从v0.1修正
- 自然语言调用与行动授权分开；移除12个仅手动调用锁，避免route无法调用build/plan。
- commit和push独立：done只验证汇报；push按本次范围决定先commit，已有相关提交直接push。
- review包括工作区、暂存、新文件和分支提交；不再只用base...HEAD漏掉本次未commit实现。
- 状态降为恢复提示，next统一数组。verified≠committed≠pushed≠deployed，用户指令和真实证据优先。
- TDD/复现/极端数据/篇幅按风险适用，不强行禁止读源码辅助复现，不禁止幂等mock次数断言。
- 标准YAML共享读取，帮助表从metadata生成；next允许正常review→build反馈回路。
- 18入口保留简洁，语言/桌面/测试/设计/CI深度进按需reference。

## v0.3 增加
- 新增dv-upgrade：同时升级Claude Code与Qoder CN中的devkit插件或裸链接；官方命令后校验内容摘要。
- 同版本Claude拒绝更新时备份后原子同步；install只指本机安装，不授权commit/push或发布。
- 0.3.1修复apply模式未先刷新市场、导致看不到新发布版本的问题；check仍保持只读本地克隆。
- 0.3.2修复默认Claude根被强制写入CLAUDE_CONFIG_DIR、导致CLI去读错误配置路径的问题。
- 0.3.3强化dv-build：分级侦察、复用台账、新项目官方starter、约定冲突与SQL/性能门禁；不新增dv-init或dv-wiki，项目画像只在dv-context会话输出。

## 技能分工
| 类别 | 技能 | 主要职责 |
|---|---|---|
| 元 | route/help/context/author/upgrade | 选最短路径、说明用法、配置接入、维护技能、跨宿主升级本机安装 |
| 需求设计 | grill/plan/design/arch/research | 澄清/规格任务/界面/结构迁移/证据调查 |
| 实施 | build/debug | 授权范围修改、诊断修复 |
| 验证 | test/audit/browser/review | 用例执行/风险有效性/真实UI/三轴评审 |
| 交付 | done/commit/push | 验证汇报/规范分批提交/推送与CI跟踪 |

## 调用与授权
所有技能可自然语言选择，slash为快捷方式；宿主调用成功需工具日志，不能只输出名字就当执行。
metadata的effects描述docs/prototype/tests/business-code/install能力；explicit-actions记录commit/push/install意图门槛，不是宿主安全沙箱。install仅指本机宿主安装，不含远程发布。只分析不写业务代码，只草拟message不stage，明确push默认包括相关commit但“只推已有提交”优先。
重要新设计、范围变化、不可逆数据操作、生产写入/审批、Git提交推送按实际影响确认，不每个阶段机械STOP。已有明确授权不重复确认，环境权限限制绝不绕过。upgrade只动本机devkit安装，同版本内容同步先备份，不隐含commit/push或发布授权。

## 任务路径
- 小明确改动：build→review→done，不必grill/spec/issues。
- 模糊功能：grill→plan（按规模）→build→test/browser（按风险）→review→done。
- 大迁移：research/arch migrate→plan→build分批，兼容/验证/回滚；arch不直接执行。
- 报错只诊断：debug→证据与缺口；要求修复才修改。
- 提交：commit分批，保留无关文件和staged hunk；不默认push。
- 推送：相关未commit先commit，全部相关已commit直接push；检查upstream、历史、非fast-forward，禁止隐式force/rebase/merge。
- CI：本次SHA/分支/环境关联，不引用最近绿；默认状态链接，要求才等待；manual/timeout/失败明确报告，不批准/重试。
- 发布验收：done release区分pipeline、部署任务、实际版本和业务正常；不默认本地部署。
- 升级本机安装：upgrade先只读检查两个宿主，再走官方命令；命令成功仍校验内容，同版本Claude用备份后同步，最后要求重启确认。

## 工具与产物
见ARTIFACTS；配置固定项目.devkit/config.json，其他产物路径可覆盖，工具resolve防越界和外部symlink。
next为建议图而非执行状态机；cycles合法，目标必须存在。
help生成检查不写入；lint校验YAML类型、字段、引用、调用策略对齐。文字预算超限仅warning，静态检查不证明实际行为。
link仅Claude/Qoder本地目录，不覆盖外来链接；check无写入、卸载仅自有。
optional hook读取配置state，不写、不把游标变权限。稳定一行提示，无时长与循环计数；没有实现“3轮/10轮”稀疏策略，不承诺它。
文档契约分三档`docs.profile`：off只留目录，light校验命名/编号/状态词/引用/索引，strict再加必填小节。模板随技能安装进各自references，不再放仓库根。check-docs只报告不改写，索引由脚本生成，两者都不构成写入授权。

## 深度与边界
build/test/reference覆盖Java Python Go JS/TS和Electron，但不能保证替代所有语言专家能力。桌面分renderer/IPC/主进程/OS/安装升级签名，浏览器无法全覆盖。
安全、性能与发布验收按授权环境；缺框架/目标OS/CI权限要报告，不凭工具名字制造通过。
不依赖specific general-purpose代理名；review/audit/research的只读分析可并行，须固定同一快照、隔离写入、主流程复核汇总；宿主无并行入口时串行降级。build/debug/browser等共享写入或环境的场景默认串行。upgrade使用各宿主CLI与内容摘要校验；Claude同版本拒绝更新时备份后同步，Windows路径未实测。CodeGraph仅在项目已索引且项目约定适用时使用。

## 支持与验证口径
Claude/Codex/Qoder调用元数据分别验证。openai.yaml只说明Codex策略，user-invocable不是禁止隐式调用，Qoder未知能力不作结论。
当前版本不自动安装、不改全局、不提交本仓库、不实地push/deploy。
验证层：静态结构、离线脚本/临时Gitfixture、真实宿主调用、真实任务、实际发布。每层分别记录，未跑不写通过。
v0.1模型自报名字、回答no不足以证明16个加载或手动入口，原验证结论不继续沿用。字符÷3不是真实token或最坏上界。

## 发布前仍需
真实宿主自然语言选择与执行日志、一次小任务端到端、真实CI只读关联、Qoder/Codex加载、目标OS桌面验收与许可证追溯。评估规范见docs/evaluation.md。

# 评估与证据分层

## 层级
1. 静态结构：YAML/引用/metadata/目录/生成表/JSON schema。
2. 离线执行：脚本与临时Git fixture，覆盖失败与只读路径；不操作真实远程或用户配置。
3. 宿主：实际技能调用日志、模型/宿主/版本、输入、文件副作用与结果。模型输出名字或yes/no不足以证明调用。
4. 真实任务：小功能/报错/设计/测试/提交，版本与验收证据。
5. 发布：匹配SHA/环境的CI、运行版本与业务验收，各自授权并独立记录。

本版本提供前两层测试以及evals/scenarios.json人工/宿主评估用例。该JSON不是自动模型runner，不能把条目存在或静态契约通过算实际模型通过。全技能词法路由矩阵见 `evals/routing/README.md`：它只做触发预筛，不替代宿主调用日志。

核心技能方法的六项定向材料见 `evals/depth-scenarios.json`，对照步骤与独立评判维度见 `evals/README.md`。任务效果、边界遵守、证据真实性分别记录；零违规不等于完成任务。新增材料未执行真实模型对照，不能声明深度改进已被实验证明。历史版本验证记录保留其原始范围，不代替当前版本证据。

## 工作流基础设施验证（2026-11-03）

- 静态：`scripts/lint.py`、`dv-help-gen.py --check`、`check-docs.py` 均通过。
- 离线执行：`tests/test_workflow.py` 覆盖项目适配器检测、plan 风险/快路径、门禁 pass/fail、done fail-closed、driver 逐技能执行、入口安装；全量 `unittest` 通过。
- 真实仓库：`devkit_context.py --root . --write` 生成 `.devkit/project.json`；`devkit_gates.py run/check` 在 devkit 仓库执行 unit/lint/help/docs 门禁并保存证据。
- 消融：`run.py --skills` 支持 build-only、build+test、build+test+review 等臂；结果仍需真实宿主运行，不能把参数存在当模型通过。
- 2026-11-03 S6 小改动 smoke（Claude Code / fable，1 次）：no-skill 3/3、36.7s、876 token；`--skills dv-build` 3/3、47.9s、1,782 token；`--skills dv-build,dv-test` 3/3、83.8s、3,500 token。功能检查相同，成本随技能数上升。
- 项目适配器在 OTA clone 上识别为 mixed，门禁 `unit/lint/build/manual/docs/release`，`i18n` 因缺 `web/node_modules` 标为 optional；说明它按真实文件检测，不靠硬编码项目名。
- 结论边界：这些验证证明基础设施可执行、能 fail closed，不证明技能在真实任务上必然提高正确率。

## 跨仓库消融矩阵（2026-11-03）

矩阵文件：`evals/matrix.py`，报告：`evals/matrix-report.md`。

- 规模：2 模型（`fable`、`sonnet`）× 5 技能臂（no-skill / build / build+test / build+test+review / chain）× 4 任务（S9、S11、OTA2、LET1），每格 1 次，共 40 次。
- 任务通过：S9 10/10；S11 9/10；LET1 9/10；OTA2 0/10。S11/LET1 的缺口是 sonnet chain 在 900s 超时；OTA2 所有臂都没过中英手册 Filters 行，fable build+test+review 还因只调用 1 个技能而漏了后端隐藏测试。
- 技能调用：no-skill 0；build 1；build+test 2；build+test+review 3；chain 在同任务上为 1/5/6 不等，说明显式技能列表仍不保证按序执行。
- 成本：S11 fable no-skill 146.2s/17.6k token，chain 304.8s/53.5k；OTA2 sonnet no-skill 99.4s/9.1k，chain 535.3s/55.2k；LET1 sonnet build+test+review 746.9s/66.9k。技能越多通常越贵。
- 基础设施真实生效：fable chain S11 首次运行创建了 `.devkit/runs`，被算入改动导致范围失败；新增 `.git/info/exclude` 排除后重跑为 4/4、6 个文件。运行产物不应进入业务 diff。
- 结论：矩阵没有证明技能提升任务通过率；chain 还会因超时或未按序调用而退化。当前证据支持“显式、高风险、可接受成本时使用”，不支持默认全链。

## 记录模板
- 宿主/模型/版本/时间/配置（无秘密）；其他skills是否隔离。
- 输入与允许/禁止副作用。
- 实际调用（工具日志），变更文件与Git状态对照。
- 命令、退出码、关键输出、原始日志位置。
- 结果：通过/失败/未执行/无法验证。

## 判据
只分析不写业务；只消息不stage；commit不push；push相关未提交先commit，only-existing不commit；未提交diff审得到；manual CI不批准；生产自动部署后果在push前识别；无框架不编测试通过；state旧提示不覆盖新任务。

## 未验证范围
Qoder/Codex隐式调用、真实CI权限/API匹配、跨OS桌面、真实生产发布、许可证完整审计。字符预算不是精确token或上界。旧v0.1自报技能名结果不作为本版本有效证据。

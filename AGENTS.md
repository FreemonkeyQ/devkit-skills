# devkit 开发与使用约定

自然语言选择技能，调用不等于行动授权。18个入口见help生成表；不必为简单任务建立工单。

- 项目/目录级指令和当次用户范围优先；只分析不改代码。
- 证据必须匹配当前版本/范围，未验证明确说；日志摘要＋可定位原始输出，不强迫终端贴巨量文本。
- 提交用dv-commit，推送用dv-push。done只验证汇报；不自行commit/push/merge/deploy。
- 评审包含本次未提交/暂存/相关新文件，保留无关既有修改；零发现合法。
- 诊断可读源码辅助复现；事实/假设/限制分开，不伪称已复现。
- TDD按业务风险适用；幂等/重试关键交互断言可用，不测纯mock代替业务。
- 设计/测试/审计/方案职责独立，允许写文档/隔离原型不等于改生产代码。
- 桌面验收分渲染/IPC/OS/安装升级，Web通过不代表全部通过。
- CI跟踪优先已有发布链，SHA/分支关联；不隐式批准/重试/生产部署。
- state是恢复提示，不覆盖当前指令/Git/证据；不安装用户配置或链接，除非另行要求。
- 实施验证使用 `python3 -m unittest discover -s tests -v`、lint和help --check；开发依赖见requirements-dev.txt。
- 阅读技能不依赖Python；脚本元数据不能代替宿主权限沙箱。跨宿主未验证明确标注。

产物约定见ARTIFACTS.md；方案见DESIGN.md；评估口径见docs/evaluation.md。

文档契约分档：`docs.profile` = `off`/`light`/`strict`（缺省 light）。`scripts/check-docs.py` 只读校验命名、编号、状态词、引用与索引，非零退出表示有错；`scripts/gen-docs-index.py` 生成 `docs/INDEX.md`。未启用 strict 不校验必填小节，也不得宣称格式已强制。

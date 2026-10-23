# v0.2.0 离线验证记录

本轮实际执行：
- `python3 scripts/lint.py`：0 errors，0 warnings，18份技能契约。
- `python3 scripts/dv-help-gen.py --check`：生成表与源metadata一致。
- `python3 -m unittest discover -s tests -v`：16 tests通过。
- `claude plugin validate .claude-plugin/plugin.json`：通过。
- `claude plugin validate .claude-plugin/marketplace.json`：通过。
- `git diff --check`：通过。

测试覆盖：规范YAML多行/错误、嵌套目录、目录metadata、帮助只读check、默认/自定义state路径、类型错误、外部symlink与路径越界、hook无效状态不阻断、外来链接保护/自有卸载；临时Git仓含暂存/未暂存/新文件/无upstream与无关改动；提交推送done职责静态契约与9个评估fixture。

限制：临时Git测试验证Git差异语义，不等于真实模型分批提交或push成功。此轮未调用技能执行真实项目任务、未提交或推送本仓库、未挂全局hook、未安装替换旧技能、未运行真实CI/生产发布、未做Qoder/Codex宿主调用测试。

原型脚本验证通过，不宣称完整研发能力/所有平台/模型行为已验证。

## 安装路径实测（2.1.267，macOS，隔离配置目录）

在临时 `CLAUDE_CONFIG_DIR` 中执行，未影响本机既有安装：

- `claude plugin validate .`：通过。
- `claude plugin marketplace add ./` → `claude plugin install devkit-skills@devkit-skills`：安装成功，`plugin list` 显示 0.2.0 / enabled。
- `claude plugin details devkit-skills`：Skills (18)，常驻约 507 tok（估算）。
- `claude plugin marketplace add FreemonkeyQ/devkit-skills`（GitHub 克隆）→ 安装：成功。
- `claude plugin update …`：已是最新；`claude plugin marketplace update …`：成功。
- `claude plugin uninstall …` → `claude plugin marketplace remove …`：清理成功。
- `--plugin-dir` 启动后 `/devkit-skills:dv-help` 与自然语言「有哪些 dv 技能」均命中。
- 裸链接 `link.py --apply/--check/--uninstall` 在临时目标目录闭环通过，`/dv-help` 可调用。

限制：以上为安装与加载链路验证，不等同真实任务交付；Windows、其他宿主、`/plugin` 面板交互与自动更新未实测。`--marketplace <source>` 单命令安装需要更新版本，本机未验证。

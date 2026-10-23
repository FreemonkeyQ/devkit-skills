# devkit-skills

GitHub：[FreemonkeyQ/devkit-skills](https://github.com/FreemonkeyQ/devkit-skills)

```bash
git clone git@github.com:FreemonkeyQ/devkit-skills.git
```

面向个人与开源协作的研发技能库，统一 `dv-` 命名，与公司无关。**18 个技能，直接说任务即可；调用技能不等于授权提交、推送或部署。**

状态：**v0.2.0 原型**。流程契约与离线测试可验证；宿主实际调用、真实项目交付与跨平台部署不宣称已全面验证。

## 推荐用法

| 你说 | 推荐路径 | 边界 |
|---|---|---|
| 想加导出，但字段没想清 | grill → plan（必要时） | 只澄清不自动开工 |
| 按已确认方案实现 | build → review → done | 不自动commit/push |
| 报错，先分析别改 | debug诊断 | 不修源码 |
| 设计这页的交互 | design → build（批准后） | 先设计与原型 |
| 帮我审这次改动 | review | 包含未提交/暂存/相关新文件 |
| 按功能规范提交，不push | commit | 合理分批，仅本地提交 |
| 推送一下 / commit push | commit（若相关改动未提交）→ push | 保护无关改动，CI后果先识别 |
| 只推已有提交，不commit | push | 工作区保持原状 |
| 推完等部署结果 | push＋CI跟踪 | 不自动审批/重试/部署 |
| 验证发布后的功能 | done release | 实际版本＋健康＋关键业务，默认只读 |
| 这套怎么用 | help | 查询总表、场景和技能说明 |

没有必要为了一个小改动制造spec、issue、ADR。现有仓库规范优先；自然语言可以明确只分析、记录、执行或限制范围。

## 全部技能

元：dv-route、dv-help、dv-context、dv-author。
需求/设计：dv-grill、dv-research、dv-plan、dv-design、dv-arch。
实施：dv-build、dv-debug。
测试/验收：dv-test、dv-audit、dv-browser、dv-review。
交付：dv-done、**dv-commit、dv-push**。

完整生成表见 [dv-help](skills/dv-help/references/_generated.md)。next仅表示可选关联，不是强制执行序列。

## 使用与安装（尚未替换你的现有技能）

Claude Code本地试用可使用 `claude --plugin-dir /path/to/devkit-skills`，插件命名空间通常为 `/devkit-skills:dv-help`；裸skills链接时通常 `/dv-help`。以宿主实际列表为准。

可选本地链接工具（只处理Claude/Qoder skills目录）：
```
python3 scripts/link.py --check
python3 scripts/link.py --apply
python3 scripts/link.py --uninstall
```
apply会创建目标目录，但不覆盖任何外来文件/符号链接；有冲突返回非零。不要同时插件安装和裸链接，以免重复。
Codex附带agents/openai.yaml是Codex元数据；Qoder与Cursor支持需要分别实测，不把该字段当Qoder权限保险。此版本未提供Cursor规则生成或Codex自动安装。

所有技能按自然语言可发现。显式动作（commit/push）必须有当次明确意图；宿主权限机制仍优先，metadata只描述职责不是沙箱。

## 配置与恢复

`.devkit/config.json`可从示例复制，推荐dv-context读取现有仓库约定后接入。路径相对项目根，禁止越界。命令只填真实入口，无对应工具则保留未验证项。
状态可选；`state.json`只提示会话恢复，不覆盖当前指令、Git和实测证据。
可选hook `scripts/dv-hook.sh`不会自动注册，需宿主单独授权；它不执行技能、不写状态或自动部署。

## 开发验证

```
python3 -m pip install -r requirements-dev.txt
python3 scripts/lint.py
python3 scripts/dv-help-gen.py
python3 scripts/dv-help-gen.py --check
python3 -m unittest discover -s tests -v
python3 scripts/cost.py
```
开发工具需要PyYAML/jsonschema；阅读技能本身不需安装依赖。成本只报字符预算，非精确token或上界。

## 文档
[设计](DESIGN.md) · [产物](ARTIFACTS.md) · [使用指南](skills/dv-help/references/guide.md) · [评估](docs/evaluation.md) · [来源](NOTICE)

原创建议与重写技能，MIT；吸收Matt Pocock、Anthropic、Emil、Superpowers和AgentForge的工程思想，不声称逐字移植或已全量替代语言专项库。见NOTICE。

# devkit-skills

[![validate](https://github.com/FreemonkeyQ/devkit-skills/actions/workflows/lint.yml/badge.svg)](https://github.com/FreemonkeyQ/devkit-skills/actions/workflows/lint.yml)
[MIT](LICENSE)

面向个人与开源协作的研发技能库，统一 `dv-` 命名，与公司无关。**19 个技能，直接说任务即可；调用技能不等于授权提交、推送或部署。**

状态：**v0.3.3 原型**。流程契约与离线测试可验证；宿主实际调用、真实项目交付与跨平台部署不宣称已全面验证。

## 环境要求

| 依赖 | 用途 | 说明 |
|---|---|---|
| Claude Code | 宿主 | 本地在 2.1.267 实测；`claude plugin` 子命令不可用时请升级，或改用方式二 / 三 |
| git | 从 GitHub 拉取市场 | 私有 fork 需预先配置 SSH 或 HTTPS 凭据 |
| Python 3 | 仅方式三与开发验证 | 阅读技能正文不需要 Python |

macOS 上已实测插件市场、`--plugin-dir` 与裸链接三种方式；Linux/Windows 与其他宿主未验证，见「常见问题」。

## 安装（选一种）

三种方式只需选一种，**不要同时启用插件安装与裸 skills 链接**，否则同名能力会重复出现。

### 方式一：插件市场（推荐）

在 Claude Code 会话中执行：

```text
/plugin marketplace add FreemonkeyQ/devkit-skills
/plugin install devkit-skills@devkit-skills
```

`/plugin install` 会打开插件详情面板，选择安装范围后生效：

- **user**：本机所有项目可用（默认）
- **project**：写入仓库 `.claude/settings.json`，协作者仍需各自安装
- **local**：仅本仓库、仅自己

也可以不进入会话，直接在 shell 中安装：

```bash
claude plugin marketplace add FreemonkeyQ/devkit-skills
claude plugin install devkit-skills@devkit-skills --scope user
```

克隆私有仓库或镜像时，`marketplace add` 换成完整 URL（如 `git@github.com:you/devkit-skills.git` 或 `https://...`），并使用该机器已有的 git 凭据。

安装后技能名带插件命名空间：`/devkit-skills:dv-help`、`/devkit-skills:dv-build`；裸名 `/dv-help` 通常也可用，以宿主实际列表为准。

### 方式二：本地目录试用（不写入安装记录）

适合先评估、或修改技能后立即验证：

```bash
git clone git@github.com:FreemonkeyQ/devkit-skills.git
claude --plugin-dir /path/to/devkit-skills
```

`--plugin-dir` 只对当前会话生效，可重复传入多个目录或 zip；同样使用 `/devkit-skills:dv-help` 调用。

### 方式三：裸 skills 链接（Claude / Qoder 本地目录）

把 `skills/dv-*` 以符号链接方式挂到宿主 skills 目录：

```bash
python3 scripts/link.py --check     # 只读检查，列出缺失项，不写入
python3 scripts/link.py --apply     # 创建缺失链接
python3 scripts/link.py --uninstall # 仅删除由本仓库创建的链接
```

- 默认目标是 `~/.claude/skills` 与 `~/.qoder-cn/skills`；可用 `--target` 指定单个目录。
- `apply` 会创建目标目录，但**不覆盖**任何外来文件或符号链接；有冲突时返回非零并打印 `Conflict preserved`。
- 链接后以裸名调用：`/dv-help`；全部技能按自然语言可发现。

## 验证安装

```bash
claude plugin list                       # 方式一：应看到 devkit-skills，Status: ✔ enabled
claude plugin details devkit-skills      # 方式一：Skills (19) 且列出 dv-* 全部技能
```

会话内可打开 `/plugin` 的 **Installed** 标签确认，或输入 `/` 查看 `/devkit-skills:dv-*`。

再发一句自然语言验证自动选择，例如「看看未提交代码有没有问题」应命中 `dv-review`；「只分析这个报错别改」应命中 `dv-debug` 诊断。

方式三验证：输入 `/skills` 或 `/dv-help`。若 skills 目录是在会话启动后才新建的，先执行 `/reload-skills`。

> `claude plugin details` 显示的常驻 token 是估算值，不是精确计数或最坏上界。

## 怎么用

| 你说 | 推荐路径 | 边界 |
|---|---|---|
| 想加导出，但字段没想清 | grill → plan（必要时） | 只澄清不自动开工 |
| 按已确认方案实现 | build → review → done | 不自动 commit/push |
| 旧项目加接口/导出/改实现 | build（先侦察与复用）→ review → done | 不自动全量扫描，不新建同类轮子 |
| 新项目从零开始 | build（官方 starter）→ test → review | 不自建模板、不预建分层 |
| 报错，先分析别改 | debug 诊断 | 不修源码 |
| 设计这页的交互 | design → build（批准后） | 先设计与原型 |
| 帮我审这次改动 | review | 包含未提交/暂存/相关新文件 |
| 按功能规范提交，不 push | commit | 合理分批，仅本地提交 |
| 推送一下 / commit push | commit（若相关改动未提交）→ push | 保护无关改动，CI 后果先识别 |
| 只推已有提交，不 commit | push | 工作区保持原状 |
| 推完等部署结果 | push＋CI 跟踪 | 不自动审批/重试/部署 |
| 验证发布后的功能 | done release | 实际版本＋健康＋关键业务，默认只读 |
| 升级本机 Claude/Qoder 的 devkit | upgrade | 只动本机安装，不 commit/push |
| 这套怎么用 | help | 查询总表、场景和技能说明 |

全部技能：

- 元：dv-route、dv-help、dv-context、dv-author、dv-upgrade
- 需求/设计：dv-grill、dv-research、dv-plan、dv-design、dv-arch
- 实施：dv-build、dv-debug
- 测试/验收：dv-test、dv-audit、dv-browser、dv-review
- 交付：dv-done、dv-commit、dv-push

完整生成表见 [dv-help](skills/dv-help/references/_generated.md)。`next` 仅表示可选关联，不是强制执行序列。

没有必要为了一个小改动制造 spec、issue、ADR。现有仓库规范优先；自然语言可以明确只分析、记录、执行或限制范围。

## 更新与卸载

更新（插件市场安装）：

```bash
claude plugin marketplace update devkit-skills   # 先刷新市场目录
claude plugin update devkit-skills@devkit-skills # 再更新已安装插件
```

会话内也可在 `/plugin` 的 **Installed** 中选 **Update now**，或在 **Marketplaces** 中开启自动更新（第三方市场默认关闭）。更新后按提示执行 `/reload-plugins` 或重启会话。

跨宿主自动升级（Claude Code + Qoder CN）：

```bash
python3 <安装根>/scripts/upgrade.py --check   # 只读：版本、摘要、重复安装
python3 <安装根>/scripts/upgrade.py --apply   # 官方更新 + 校验 + 同版本备份同步
```

默认同时处理两个宿主，`--host claude|qoder` 可限定。Claude 在版本号不变时会拒绝 `plugin update`，此时技能会先备份安装目录再同步内容；升级后需重启宿主或 `/reload-plugins`。

版本以 `plugin.json` 的 `version` 为准；不提升版本号时，已安装用户可能收不到新提交。`--plugin-dir` 方式每次启动直接读取当前文件，与版本号无关。

卸载：

```bash
claude plugin uninstall devkit-skills@devkit-skills
claude plugin marketplace remove devkit-skills    # 同时卸载来自该市场的插件
python3 scripts/link.py --uninstall               # 方式三
```

## 常见问题

- **技能没出现在 `/` 菜单**：确认宿主版本支持插件；插件改动后执行 `/reload-plugins`，新建 skills 目录后执行 `/reload-skills`；检查是否用错了命名空间。
- **同一技能出现两份**：插件安装与裸链接同时启用了，只保留一种。
- **命令与你的宿主不一致**：`/plugin` 面板与 `claude plugin` CLI 功能等价，以宿主实际列表和版本为准。
- **Qoder / Codex**：仓库内的 `.qoder-plugin/`、`agents/openai.yaml` 只是元数据，未做宿主调用实测；其字段不构成权限保险。
- **Windows**：链接脚本依赖符号链接语义，未验证；建议使用方式一。
- **成本**：`scripts/cost.py` 只报字符预算，不是精确 token。

## 配置与恢复

`.devkit/config.json` 可从示例复制，推荐 dv-context 读取现有仓库约定后接入。路径相对项目根，禁止越界。命令只填真实入口，无对应工具则保留未验证项。

产物命名与目录契约见 [ARTIFACTS.md](ARTIFACTS.md)：`docs.profile` 三档（`off`/`light`/`strict`），缺省 `light`。模板随技能安装（在各自 `references/`），不依赖本仓库根目录。

```bash
python3 scripts/check-docs.py --project <项目根>        # 只读校验，非零退出=有错
python3 scripts/gen-docs-index.py --project <项目根>    # 生成 docs/INDEX.md
```

未启用 `strict` 时只校验文件名、编号、状态词、引用、证据路径与索引，不校验必填小节；不得宣称“格式已强制”。枚举与小节定义见 `scripts/docs.schema.json`。

状态可选；`state.json` 只提示会话恢复，不覆盖当前指令、Git 和实测证据。

可选 hook `scripts/dv-hook.sh` 不会自动注册，需宿主单独授权；它不执行技能、不写状态或自动部署。

## 开发验证

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/lint.py
python3 scripts/dv-help-gen.py
python3 scripts/dv-help-gen.py --check
python3 -m unittest discover -s tests -v
python3 scripts/check-docs.py --project . --json
python3 scripts/cost.py
claude plugin validate .          # 校验 plugin.json 与 marketplace.json
claude --plugin-dir .             # 从仓库根直接试用当前改动
```

开发工具需要 PyYAML/jsonschema；阅读技能本身不需安装依赖。CI 在每次 push/PR 执行 lint、生成表 check、单元测试与成本报告。

## 文档

[设计](DESIGN.md) · [产物](ARTIFACTS.md) · [使用指南](skills/dv-help/references/guide.md) · [评估](docs/evaluation.md) · [验证记录](docs/validation-v02.md) · [来源](NOTICE)

原创建议与重写技能，MIT；吸收 Matt Pocock、Anthropic、Emil、Superpowers 和 AgentForge 的工程思想，不声称逐字移植或已全量替代语言专项库。见 NOTICE。

# 宿主安装与升级细节

以下路径以 macOS 实测为准；Linux 同构，Windows 未验证。所有路径都可由环境变量覆盖，脚本以实际发现结果为准。

## 安装位置

| 宿主 | 配置根 | 插件注册表 | 市场克隆 | 插件缓存 | CLI |
|---|---|---|---|---|---|
| Claude Code | `~/.claude`（`CLAUDE_CONFIG_DIR`） | `plugins/installed_plugins.json` | `plugins/marketplaces/devkit-skills` | `plugins/cache/devkit-skills/devkit-skills/<版本>` | `claude` |
| Qoder CN | `~/.qoder-cn`（`QODER_CONFIG_DIR`） | `plugins/installed_plugins_v2.json` | `plugins/marketplaces/devkit-skills` | `plugins/cache/devkit-skills/devkit-skills/<版本>` | `~/.qoder-cn/bin/qoderclicn/qoderclicn-<版本>` 或 `qoderclicn` |

注册表里 `devkit-skills@devkit-skills` 的记录给出 `installPath`、`version`；Claude 还记录 `gitCommitSha`。以注册表指向的安装目录为准，不扫描全部版本目录猜测。

## 官方命令

Claude：

```bash
claude plugin marketplace update devkit-skills
claude plugin update devkit-skills@devkit-skills --scope user -y
```

Qoder CN：

```bash
qoderclicn --config-dir ~/.qoder-cn plugins marketplace update devkit-skills
qoderclicn --config-dir ~/.qoder-cn plugins update devkit-skills@devkit-skills --scope user
```

缺失 CLI 时报告手工命令，不自动安装。市场未配置时先报告，不擅自新增市场。`--check`只读本地市场克隆，不联网刷新；`--apply`总是先刷新市场，再决定是否需要`plugin update`。

## 同版本行为（2026-10-23 实测）

- Claude 2.1.267：`plugin update` 在 `plugin.json` 版本不变时直接返回 “already at the latest version”，即使市场克隆已有新提交，缓存内容也不会变。
- Qoder CN 1.1.62：同版本 `plugins update` 会重建缓存，能拿到市场里的新内容。
- 结论：命令成功必须再用内容摘要验证；Claude 同版本需要兜底。

## 同版本兜底

仅在源版本等于已安装版本、摘要不同、且用户允许同步时执行：

1. 校验 `installPath` 位于本宿主 `plugins/cache` 下且不是符号链接。
2. 备份到同级的 `<版本>.bak-<时间戳>`。
3. 同步源安装根到 `installPath`，跳过 `.git`、`__pycache__`、`.DS_Store`。
4. 删除 `skills/` 下源中已不存在的旧文件；不碰缓存里的宿主私有文件。
5. 重新计算摘要；版本元数据保持原值，报告中明确“内容已同步、版本号未变”。

源版本高于已安装时不使用原地同步，避免注册表版本与内容不一致。

## 裸链接

`~/.claude/skills` 与 `~/.qoder-cn/skills` 中指向本仓库 `skills/dv-*` 的符号链接：

- 链接跟随源仓库，源更新后无需重装。
- 源仓库干净且落后时用 `git pull --ff-only`；不干净、无 upstream 或分叉时只报告。
- 新增技能后只补缺失链接，不覆盖已有文件或外来链接。
- 插件和裸链接同时存在会造成重复加载；报告但不自动删除。

## 验证与限制

- 升级后需要重启宿主或 `/reload-plugins`，再确认技能列表。
- 摘要只覆盖 `skills/` 与 `scripts/`，不能证明宿主已重新加载。
- 不同宿主的版本号策略可能变化；未实测的宿主版本只报告，不承诺行为。
- 不读取或输出凭据；不修改其他插件、项目代码、Git 历史或远程仓库。

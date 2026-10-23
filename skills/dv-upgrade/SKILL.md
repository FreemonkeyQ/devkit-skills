---
name: dv-upgrade
description: '检查并升级 Claude Code 与 Qoder CN 中已安装的 devkit 技能或插件；用于版本落后、两个宿主不一致或新版本发布后更新，不修改项目代码。'
user-invocable: true
metadata:
  stage: meta
  summary: 跨宿主升级本机 devkit
  effects: [install]
  explicit-actions: [install]
  next:
  - dv-help
---

# 升级本机 devkit 安装

## 适用 / 不适用
用户要求升级或同步本机 devkit，或怀疑 Claude Code 与 Qoder CN 安装版本不一致时使用。只查版本用`--check`；项目接入配置用context，技能用法用help，维护技能仓库用author。升级不改项目代码，不授权commit/push/发布。

## 授权与边界
- 调用本技能即授权修改**本机 devkit 安装**：市场克隆、宿主插件缓存、由本仓库创建的裸链接。
- 只处理`devkit-skills`自身；不卸载或更新其他插件，不动无关配置，不删除用户创建的链接或文件。
- 同版本内容刷新前必须备份安装目录；目标无法确认在 devkit 缓存内时停止。
- 不自动commit/push源码；源码仓库不干净或已分叉时只报告，不强拉。
- 升级后需要重启宿主或执行`/reload-plugins`；命令成功不等于新会话已经加载。

## 流程
1. 定位脚本：先解析本 SKILL.md 的真实路径（裸链接安装用`pwd -P`或`realpath`，不能停在`~/.claude/skills`外层），向上两级是安装根，脚本为`<安装根>/scripts/upgrade.py`。插件安装和裸链接安装都适用。
2. 先只读检查：
   `python3 <安装根>/scripts/upgrade.py --check`
   报告两个宿主的安装方式、版本、源SHA、内容摘要和重复安装。
3. 说明将执行的宿主命令、是否触发同版本同步、备份位置。用户已明确“升级”则继续；只问“看看版本”则停在检查结果。
4. 执行升级：
   `python3 <安装根>/scripts/upgrade.py --apply`
   默认`--host both`；可指定`--host claude|qoder`。禁止同版本同步时加`--no-sync`。
5. 复核输出：每个宿主的 before→after、执行过的命令、备份路径、未处理项（CLI缺失、市场未配置、权限或网络失败、重复安装）。
6. 提示重启或重载；随后用`dv-help`确认技能表，用实际任务确认加载。未重载前不宣称已生效。

## 判断规则
- 源版本高于已安装：官方`marketplace update`后执行`plugin update`。
- 源版本等于已安装但内容摘要不同：Claude会拒绝更新，备份后原地同步；Qoder先走官方更新，未刷新再同步。
- 源版本低于已安装：拒绝降级并报告。
- 插件与裸链接同时存在：报告重复加载，不擅自删除；保留哪种由用户决定。
- CLI或市场缺失：报告可用手工命令，不猜测路径、不安装新工具。

## 输出
每个宿主给：安装方式、旧版本/新版本、内容摘要是否变化、执行动作、结果、备份路径、是否需要重载。失败保留现场并给可重试命令；`--check`只读，不产生备份或命令副作用。

## 自检
只动devkit安装；有备份；未改其他插件、项目代码或Git历史；失败未静默跳过；未重载的安装未标记为已生效；未把“命令成功”当成“技能已加载”。

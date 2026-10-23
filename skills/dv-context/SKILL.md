---
name: dv-context
description: '把 devkit 接入一个仓库：生成配置、补 AGENTS.md 技能段、建状态文件，并核对既有目录约定。用于新仓首次接入、状态与配置不一致、SKILL
  没按预期工作。Triggers: 接入, 初始化devkit, 配置devkit, setup, onboard, 状态不一致.'
user-invocable: true
metadata:
  stage: meta
  summary: 接入配置与路径核对
  effects:
  - docs
  explicit-actions: []
  next: []
---

# 仓库接入与配置核对

## 适用 / 不适用
首次接入、路径/命令/状态漂移；不为普通开发强制初始化。不明下一步用route，修改技能自身用author。

## 流程
1. 读取AGENTS/CLAUDE及目录级规则、现有spec/issues/词汇/ADR、脚本和真实测试入口、remote与分支习惯。事实自己查，只问无法判断且影响选择的决定。
2. 沿用既有产物目录与编号；没有则默认.devkit。配置始终在项目.devkit/config.json，路径值相对项目根；commands是明确命令，不凭安装依赖推定能运行。
3. 普通写文档按用户接入授权执行；新增重要流程规则展示摘要。AGENTS只维护标记包围的devkit段，不覆盖其他正文/目录级指令；该段写产物目录、命名规则与校验入口（≤15行），细节指向ARTIFACTS.md。
4. 参考共享scripts/config.py与config.schema.json输出配置，记录可用/不可用检查。新增`docs.profile`（off/light/strict）与`paths.changes`/`paths.index`；缺失时按light处理。没有自动提交开关：commit/push由当次意图授权，不由静态配置提升权限。
5. 状态可选；新建时idle，已有状态不能重置丢任务。用户指令/Git/实测优先于游标，冲突报告修正建议而非盲信JSON。
6. 可行时运行`scripts/check-docs.py`与`scripts/gen-docs-index.py`生成索引，报告实际输出；工具不可用或profile=off时明确说未校验。
7. 输出实际变动、路径与命令依据，不安装全局技能、不挂hook或修改用户设置，除非另行明确要求。

## 自检
路径未越出仓库或复写外部symlink；无秘密写入配置；schema校验不执行命令。缺框架不静默新增框架；已有记录保留。

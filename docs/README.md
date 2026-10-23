# Docs

README：安装与使用入口（插件市场 / `--plugin-dir` / 裸链接）、验证、更新卸载；DESIGN：技能分工、调用与授权、最短路径；实际技能数见 help 生成表；ARTIFACTS：产物目录、命名/编号/状态词契约与校验入口；help/guide：实际推荐用法。
评估方法见evaluation.md。技能reference补语言/桌面/测试/设计/CI细节，不自动全量加载。
产物模板放各自技能的 `references/`（spec/ticket 在 dv-plan，adr 在 dv-grill，review 在 dv-review，change-proposal 在 dv-arch），随技能安装。本仓库根不再有 `templates/`。
文档契约由 `scripts/check-docs.py` 校验、`scripts/gen-docs-index.py` 生成索引；两者只报告和写索引，不提供提交或推送授权。
当前不为每个技能建立重复的网页手册，避免与技能正文和help生成表漂移。历史版本验证记录保留原版本范围，不作为当前版本全量验证证据。

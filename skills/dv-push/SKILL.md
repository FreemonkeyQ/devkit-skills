---
name: dv-push
description: 推送明确分支；相关改动未提交时先规范提交，已全部提交则直接推送。用于push或commit push；只推已有提交指令优先。
user-invocable: true
metadata:
  stage: ship
  summary: 提交后推送与CI跟踪
  effects:
  - docs
  explicit-actions:
  - commit
  - push
  next:
  - dv-commit
  - dv-done
---

# 提交后推送与CI跟踪

## 适用 / 不适用与授权
“推送一下”“commit push”默认授权提交本次相关未提交内容后推送明确当前分支。
“只推已有提交，不commit”优先，保持工作区；“检查如何推送”只分析。推送不是merge、生产审批或部署命令授权，项目发布规则优先。

## 流程
1. 检查当前分支、HEAD、工作区、remote/upstream、待推送历史和CI触发配置。detached HEAD、冲突或目标歧义先停；不把有远程就猜成origin/main。无upstream时只有目标唯一且授权明确才建立。
2. 默认有本次相关未提交改动→实际调用dv-commit→成功再继续；无相关未提交内容→直接检查待推送提交。已有历史commit不代表工作区无需commit。commit失败/范围阻塞则停止，不push半成品。
3. 无关脏内容可保留并推已有提交；但待推送历史夹带不明提交必须说明范围。已有upstream用fetch读取最新目标（网络操作受权限），判断领先/落后/分叉；无upstream检查目标分支存在性与祖先关系。
4. 已同步→no-op；分叉、远端领先导致拒绝→报告，不自动rebase/merge/force。先说明推送目的地、提交范围和已知CI后果；直接触发生产部署时遵循仓库额外发布授权，不因普通push绕过。
5. 明确refspec推当前分支，不mirror/推全部分支tag；不使用force或`--force-with-lease`。失败区分权限、网络、保护规则、非fast-forward；不宣称远程已同步。成功通过命令/远程ref确认匹配目标SHA。
6. 读取 references/ci-tracking.md：关联本次SHA、分支、环境的流水线。默认给链接/当前状态；明确“等部署结果”才等待，有时间边界/中断/手动审批退出。缺流水线报告未找到，不引用最近一次绿冒充本次。
7. 不自动触发/重试CI任务、不点击审批、不改CI、不本地部署；额外请求仍按环境授权判断。输出commit清单、push状态、CI各阶段、保留工作区、未验证功能。发布验收可交dv-done release。

## 自检
只push已有提交指令优先；先commit的范围确实明确；推的是历史不是仅最新一个commit；pipeline成功不等于目标版本和业务正常。不执行部署回滚或删除worktree。

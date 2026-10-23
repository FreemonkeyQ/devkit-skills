---
name: dv-done
description: 验证任务完成程度、汇报证据与缺口；可做只读发布验收，不自动commit、push或清理工作树。
user-invocable: true
metadata:
  stage: ship
  summary: 验证汇报与可选发布验收
  effects:
  - docs
  explicit-actions: []
  next:
  - dv-commit
  - dv-push
---

# 验证与完成汇报

## 适用 / 不适用
判断任务完成程度、汇报验证、发布验收。提交交commit、推送交push；“做完了吗”只授权检查汇报，不授权Git或部署操作。

## 模式与流程
1. 默认任务收口：逐条对照用户验收要求与实际改动，复用仍对应当前版本/环境/测试范围的证据，证据失效才重跑。
2. 运行项目现有且适用的检查，记录命令、退出码、关键结果，完整日志按需留位置。不存在typecheck不算失败，也不伪造通过；基线失败和本次失败区分。
3. UI按browser记录；桌面、迁移、安全/性能按风险选择，不将自动化绿等同所有业务验收。
4. `release` 发布验收：读取 references/release-verification.md，区分push、CI构建、部署执行、目标环境实际版本、健康与关键业务路径。只查用户授权环境，不自行部署/审批。
5. 汇报完成/部分完成/阻塞及未验证项；按项目规则更新状态。verified表示代码验证完成，不表示已提交/推送/上线；待Git操作保留ticket与pending信息，用户明确结束任务才completed。
6. commit/push仅作为可选下一步，不自动调用；worktree保留，不默认合并、删除或关闭服务。

## 自检
不宣称完整输出等于执行成功；未测就明确未测。新鲜证据指匹配当前版本，不是无意义重复全套测试。缺口不能被“CI绿了”覆盖。

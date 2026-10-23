---
name: dv-done
description: 交付前的收口：用新鲜证据确认完成，更新状态，提交、开合并请求、清理工作树。用于改完了要交、要提交、要开MR、要结束当前工单。Triggers: 提交, 收尾, 交付, 开MR, commit, PR, finish.
disable-model-invocation: true
user-invocable: true
metadata:
  stage: ship
  reads: [.devkit/state.json, .devkit/issues, .devkit/config.json]
  writes: [.devkit/STATUS.md, .devkit/state.json, 提交, MR]
  edits-code: true
  next: []
---

# 收口

门禁 + 状态 + 提交，三件事一起做。**没有证据不许说完成。**

## 适用 / 不适用

适用：工单做完要交；要提交；要开 MR；要结束工作树。

不适用：还没审过 → `/dv-review`；测试没过 → `/dv-test run`；要修 bug → `/dv-debug`。

## 流程

### 1. 门禁（不可跳过）

逐项给出**新鲜证据**——现跑的命令、完整输出、退出码：

| 检查 | 命令来源 |
|---|---|
| 全量测试 | `config.commands.test` |
| 静态检查 | `config.commands.lint` |
| 类型检查 | `config.commands.typecheck` |
| 审美/前端验收（若涉及界面） | `dv-browser` 已产出的探针结论 |

任一项失败 → 停止，输出失败命令与原因，**不允许**标记完成。

禁止用语（未验证前）：应该可以 / 大概率好了 / 我觉得没问题 / 完成了。

### 2. 状态

- `STATUS.md`：追加本次工单编号、改动摘要、验证结果
- `state.json`：`stage=idle`、`next=[]`、清 `ticket`

> **⏸ STOP**：输出提交计划（文件清单 + 提交信息），问「确认提交吗？」，等回答。

### 3. 提交

```bash
git add <本次工单可追溯的文件>
git commit -m "<type>(<scope>): <subject>"
```

- 只含当前工单的文件；混入无关改动要拆
- 不提交密钥、`.env`、构建产物、依赖目录
- 不自动 push，除非用户明确要求

### 4. 合并请求（可选）

用户要求时：用 `config.tracker.command` 或 `glab mr create` / `gh pr create`。标题与提交一致，正文含：改了什么 / 怎么验证 / 风险与回滚。

### 5. 工作树清理（仅当本次用了独立工作树）

- 先确认已合入或用户决定保留
- 确认工作树内无未处理改动
- 用 git worktree 机制移除，不 `rm -rf`
- 不删除开发分支（需用户另行要求）

## 自检

- [ ] 每条门禁都贴了命令 + 输出 + 退出码
- [ ] 提交清单里没有无关文件
- [ ] `STATUS.md` 与 `state.json` 已更新
- [ ] 没有自动 push
- [ ] 若用了工作树，已确认可清理再清理

## 反合理化

| 我本来想说 | 现实 |
|---|---|
| 「测试刚才跑过，还是绿的」 | 改完代码后没跑过就是没证据 |
| 「这几个文件一起提交方便」 | 无关改动混入，回滚时无法拆 |
| 「先 push 再说，反正能改」 | 推送是用户的决定 |
| 「工作树先删了，分支还在」 | 未合并就删工作树会丢内容 |

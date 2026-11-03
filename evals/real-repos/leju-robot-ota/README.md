# leju-robot-ota 真实仓库评测

对 `leju-robot-ota`（Go 控制面 + React SPA）做隔离评测：只读 clone 到临时目录，agent 在副本里改代码，隐藏测试在 agent 结束后才复制进去。**不修改源仓库，不 commit，不 push，不安装依赖。**

- 源仓库：`/Users/zhangxingshuai/Documents/Code/LejuSoftware/leju-robot-ota`（可用 `--source` 或 `LEJU_OTA_SOURCE` 覆盖）
- 基线提交：`0e102a847ece37585ca6e60af2ec4931724325f1`（`dev`）
- 结果目录：`results/<UTC>-<arm>/`

## 场景

### OTA1-audit-redaction

审计 `detail` 的凭证脱敏补齐：`Authorization` 任意 scheme、`Cookie`/`Set-Cookie`、URL userinfo、`token=`/`password=` 查询参数；覆盖嵌套 map/数组，普通文本和普通 URL 保留。只改 `internal/audit/`。

隐藏验收：

- `hidden/audit/zz_hidden_sanitize_test.go` 复制进 `internal/audit/` 后运行 `go test ./internal/audit -run TestHidden`
- 再跑 `go test ./internal/audit` 检查既有测试

基线在隐藏测试上失败 5 项；参考实现全部通过。

### OTA2-audit-client-ip-filter

审计页增加客户端 IP 精确筛选：后端 `client_ip` 查询参数进入 `where`；前端 `clientIp` 字段、`client_ip` 查询参数和本地化标签；中英手册筛选说明同步更新。只改 `internal/audit/`、`web/src/`、两份手册。

隐藏验收：

- `hidden/client-ip/zz_hidden_client_ip_test.go` 复制进 `internal/audit/` 后运行 Go 测试（覆盖空值、组合筛选、limit）
- `hidden/client-ip/check_client_ip.py` 静态检查 SPA 与两份手册
- `python3 tools/check-manual.py`

基线在 Go 与静态检查上失败；参考实现全部通过。

## 运行

```bash
# 只打印场景
python3 evals/real-repos/leju-robot-ota/run.py --dry-run

# 基线：不加载插件
python3 evals/real-repos/leju-robot-ota/run.py --runs 2 --no-plugin --arm ota-no-skill

# 自然触发：加载插件，原始 prompt
python3 evals/real-repos/leju-robot-ota/run.py --runs 2 --arm ota-natural

# 链路：dv-route → dv-build → dv-test → dv-review → dv-done
python3 evals/real-repos/leju-robot-ota/run.py --runs 2 --chain --arm ota-chain
```

汇总复用 `evals/build-scenarios/compare.py`。

## 2026-11-02 结果

Claude Code 2.1.267 / `fable`，每臂每场景 1 次（源仓库固定在上面的 base_rev）：

| 臂 | OTA1 检查 | OTA2 检查 | OTA1 文件/工具/耗时/token | OTA2 文件/工具/耗时/token | 技能调用 |
|---|---|---|---|---|---|
| no-skill | 5/5 | 6/7 | 2 / 23 / 339.7s / 8,276 | 6 / 32 / 141.0s / 3,360 | 0 |
| natural | 5/5 | 6/7 | 2 / 16 / 269.3s / 8,240 | 7 / 41 / 208.0s / 4,547 | 0 |
| chain | 5/5 | 6/7 | 2 / 27 / 288.8s / 7,730 | 6 / 31 / 284.0s / 5,699 | 5 / 5 |

- **OTA1 三臂全部通过**：凭证脱敏的隐藏 Go 测试与既有测试都通过。技能没有带来可测差异。
- **OTA2 三臂都只过 6/7**：后端隐藏测试、前端静态接入和 `check-manual` 都通过，但两份手册的
  **Filters/筛选行**都没有写客户端 IP。三臂都改了手册，只是写到了 Fields 或新增段落，没有写进
  “筛选”条目；这是本次唯一稳定复现的失败点。
- chain 两次都调用了完整 5 个技能（route/build/test/review/done），但没有避免上述手册遗漏；
  OTA2 耗时约为 no-skill 的 2 倍。
- natural 两次都是 0 次技能调用，结果与 no-skill 基本一致。
- 第一轮用默认 `deepseek[1m]` 时，OTA1 的 no-skill/chain 在 900s 超时，因此最终数据只代表
  `fable`；模型切换会显著影响耗时和能否完成。

## 边界

- 隐藏测试是行为断言，不覆盖真实数据库、OSS、DDI 设备和部署链路。
- 任务 prompt 明确点名了要改的文件和字段；它测的是“在真实约束下能否正确落地”，不是“能否自己发现所有规范”。
- 源仓库的 `web/node_modules` 不在 clone 中；本评测不运行 SPA 构建或 TypeScript AST 检查，只做静态文本检查和 Go 测试。
- 结果目录已被本目录 `.gitignore` 排除；源仓库不会被写入。

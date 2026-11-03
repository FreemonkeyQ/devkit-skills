# Leju-LET-Platform 真实仓库评测

对 `Leju-LET-Platform` 的 Java 后端做隔离评测：只读 sparse clone 到临时目录，agent 只看到 `projects/backend/kuavodatahubserver`，隐藏 JUnit 测试在 agent 结束后才复制进去。**不修改源仓库，不 commit，不 push。**

- 源仓库：`/Users/zhangxingshuai/Documents/Code/LejuSoftware/Leju-LET-Platform`
- 基线提交：`970afb6def5aa269c9a68fe319bcf23bcb82fb22`
- 需要 Java 17；设置 `JAVA17_HOME`，或让脚本通过 `/usr/libexec/java_home -v 17` 查找

## 场景

### LET1-dept-isolation-consistency

`DataIsolationUtil.setDeptIsolation(QueryWrapper)` 的组织隔离包含组织本身和子项目，但 `LambdaQueryWrapper` 重载只查组织本身。任务要求统一两个重载，补齐 `type=2, parent_id in (...)` 条件。

隐藏测试：`mvn -Dtest=LetHiddenDeptIsolationTest test`；并重跑 `DataIsolationUtilTest` 防回归。

### LET2-user-project-exact-match

`setUserIsolation(QueryWrapper)` 的项目隔离使用 `LIKE project_id`，会把 `proj-1` 误匹配到 `proj-10`。任务要求改为精确匹配，同时保留空项目回退 `id=-1`。

隐藏测试：`mvn -Dtest=LetHiddenUserProjectIsolationTest test`；并重跑 `DataIsolationUtilTest`。

## 运行

```bash
# 基线：不加载插件
python3 evals/real-repos/leju-let-platform/run.py --runs 1 --model fable \
  --no-plugin --arm let-no-skill

# 消融：只 build
python3 evals/real-repos/leju-let-platform/run.py --runs 1 --model fable \
  --skills dv-build --arm let-build

# 链路
python3 evals/real-repos/leju-let-platform/run.py --runs 1 --model fable \
  --chain --arm let-chain
```

结果写入本目录 `results/`（已 gitignore）。真实仓库测试依赖本机 Maven 缓存和 Java 17；未安装时明确失败，不伪造通过。

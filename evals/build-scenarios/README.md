# Build 场景行为评估

这是评审材料，不是已完成的模型评测。它回答一个问题：当前 dv-build 在真实旧项目/新项目任务里，是否会先看现有实现、复用现有能力、避免性能反模式。

## 目录

- `fixtures/legacy-java`：Spring Boot 旧项目，已有 `CsvExportWriter`、`CustomerExportService`、分页接口、N+1、深 offset 查询
- `fixtures/legacy-py`：FastAPI 旧项目，已有 `format_dt`、`orders_to_csv`，两种 session 用法并存
- `fixtures/greenfield`：空仓库
- `scenarios.json`：8 个行为场景，prompt 与期望分离
- `run.py`：复制 fixture 到临时目录，用无头 Claude Code 跑 prompt，记录 trace/diff/检查
- `route.py`：对 19 个 description 做词法 TF-IDF 的触发路由近似

## 运行

```bash
# 只打印场景
python3 evals/build-scenarios/run.py --dry-run

# 单个场景，带 LLM 评审
python3 evals/build-scenarios/run.py --scenario S1-reuse-csv-export --judge

# 全部场景，每个 1 次
python3 evals/build-scenarios/run.py --runs 1 --judge

# 触发路由（免费、确定性）
python3 evals/build-scenarios/route.py
```

结果写入 `evals/build-scenarios/results/<UTC>-<arm>/`，已被 `.gitignore` 排除。

## 判定

每个场景有确定性检查（diff/文件数/依赖是否变化/响应关键词）和可选 LLM 评审（按 `expectations` 逐条判）。确定性检查通过不等于任务成功；必须同时看 diff 和 trace。

## 本轮结果（v0.3.3，2026-10-26，每场景 1 次）

- 自然触发：8 个构建类 prompt 中 0 次调用 devkit 技能；S7 因明确提到 “devkit” 才触发 dv-context。无头 `deepseek[1m]` 不按 description 自动路由，自然臂只能作为宿主默认行为基线。
- 显式调用（`--explicit-skill`）：
  - S5 新项目：2/2，24.5s，推荐 `uv init` 并让用户选栈（改前手写多文件包）
  - S6 小改动：3/3，24.4s，11 次工具（改前 74.8s、22 次工具）
  - S8 约定冲突：3/3，194.2s，明确列出 `Depends` 与 `SessionLocal` 两处写法（改前漏判）
  - S4 性能诊断：显式 `dv-debug` 在 plan 模式下 600s 超时；自然臂 4/4、64s。S4 暂记为未验证，不宣称技能有效。
- 触发路由（词法近似）：top-1 从 0/8 提升到 6/8；S4/S6 仍靠行为触发，不作为唯一判据。

## 限制

- 宿主是 Claude Code，实际模型由用户环境决定（本轮为 `deepseek[1m]`），不是 Claude 原生模型。
- 用户级已安装 `devkit-skills@devkit-skills`，同时用 `--plugin-dir` 加载本仓库；同名技能可能重复出现。结果用于现状基线，不用于跨宿主结论。
- `route.py` 是词法近似，不能判断语义；中文按字符 bigram 处理。
- fixture 是合成项目，不自带可运行数据库；它测行为，不测真实编译/集成。
- 单次运行不足以证明稳定性；评审方案要求每个场景多次运行并报告方差。

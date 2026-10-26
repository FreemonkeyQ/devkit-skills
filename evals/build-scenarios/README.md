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

### A/B 对照臂

```bash
# 技能臂：加载插件并显式要求使用 dv-build
python3 evals/build-scenarios/run.py --scenario S1-reuse-csv-export \
  --scenario S6-small-change-overhead --runs 3 --explicit-skill --arm with-skill

# 基线臂：不加载插件，并禁用所有技能
python3 evals/build-scenarios/run.py --scenario S1-reuse-csv-export \
  --scenario S6-small-change-overhead --runs 3 --no-plugin --arm no-skill
```

两臂 prompt 不完全相同：技能臂多一句显式调用指令，基线臂是原始 prompt；结果用于比较技能体是否改善任务，不用于测自然触发率。`--no-plugin` 与 `--explicit-skill` 互斥。

指定宿主与模型（不传则用宿主默认）：

```bash
python3 evals/build-scenarios/run.py --scenario S6-small-change-overhead --runs 3 \
  --explicit-skill --host qoder --model claude-fable-5 --arm qoder-with
python3 evals/build-scenarios/run.py --scenario S6-small-change-overhead --runs 3 \
  --no-plugin --host qoder --model claude-fable-5 --arm qoder-no
```

`--host claude`（缺省）驱动 Claude Code；`--host qoder` 驱动 Qoder CLI CN，需串行执行，模型名以 `-m` 原样传入。实际模型记在结果目录的 `meta.json`。

## 判定

每个场景有确定性检查（diff/文件数/依赖是否变化/响应关键词）和可选 LLM 评审（按 `expectations` 逐条判）。确定性检查通过不等于任务成功；必须同时看 diff 和 trace。

## 结论（最新一轮，2026-10-26）

两宿主 × 两臂 × S1/S6 × 3 次 = 24 次调用，全部 checks 通过：

| 宿主 / 模型 | 场景 | 臂 | 文件均值 | 工具均值 | 耗时均值 | 输出 token |
|---|---|---|---:|---:|---:|---:|
| Claude Code / claude-opus-5-5 | S1 | with | 3.0 | 13.0 | 83.4s | 3,137 |
| Claude Code / claude-opus-5-5 | S1 | no | 3.3 | 14.0 | 79.4s | 3,080 |
| Claude Code / claude-opus-5-5 | S6 | with | 1.0 | 9.0 | 42.0s | 722 |
| Claude Code / claude-opus-5-5 | S6 | no | 1.0 | 5.0 | 28.8s | 365 |
| Qoder CLI CN / claude-fable-5 | S1 | with | 3.0 | 18.3 | 186.8s | 未回报 |
| Qoder CLI CN / claude-fable-5 | S1 | no | 2.7 | 16.3 | 108.6s | 未回报 |
| Qoder CLI CN / claude-fable-5 | S6 | with | 1.0 | 6.7 | 79.5s | 未回报 |
| Qoder CLI CN / claude-fable-5 | S6 | no | 1.0 | 5.0 | 37.8s | 未回报 |

- 两宿主、两臂质量无差异：S1 都复用 `CsvExportWriter` 且不改 `pom.xml`，S6 都只改 1 个文件。
- 技能体对强模型只剩开销：S6 with 臂比 no 臂慢 1.5–2.1 倍，没有质量收益。
- 自然触发仍然弱：构建类 prompt 在无显式指令时基本不调用 `dv-build`，这是路由问题，不是技能体问题。

## 历史结论（2026-10-26 早前，模型 deepseek-v4.1-flash-1017）

- 显式 `dv-build`：S5 新项目 2/2 推荐 `uv init`；S6 3/3 从 74.8s/22 工具降到 24.4s/11 工具；S8 3/3 正确列出 `Depends` 与 `SessionLocal` 两种写法。S4 显式 `dv-debug` 在 plan 模式 600s 超时，记未验证。
- A/B v1（12 次）：with 臂 17/18、no 臂 18/18，无质量增益；with 臂 S1 约 1.6 倍、S6 约 1.9 倍耗时。唯一失败是 S1 一次改了 5 个文件，超预算。
- A/B v2 快速路径（6 次）：S1 恢复到 9/9 且不再越界；S6 从 65.1s/6,022 token 降到 43.3s/2,730 token。这组数据是保留快速路径与文件预算的依据。
- 以上三轮的逐次明细已随结果目录丢弃，需要时从 git 历史或重跑恢复。

## 限制

- 宿主有两套：Claude Code（`claude` CLI，别名 `claude[1M]` 解析为 `claude-opus-5-5`）与 Qoder CLI CN（`--host qoder`，可钉 `claude-fable-5`）。跨宿主结果不可互推。
- Qoder CLI 通道带内容过滤，短中文指令可能被稳定拒绝（见 routing README）；A/B 的构建 prompt 未触发拒绝。
- 用户级已安装 `devkit-skills@devkit-skills`，同时用 `--plugin-dir` 加载本仓库；同名技能可能重复出现。
- `route.py` 是词法近似，不能判断语义；中文按字符 bigram 处理。
- fixture 是合成项目，不自带可运行数据库；它测行为，不测真实编译/集成。
- with 臂多一句显式调用指令，与 no 臂原始 prompt 不对称；只能测技能体效果，不能当自然触发率。
- n=3 不足以证明稳定性；结论按方向使用，不按百分点使用。


# Build 场景行为评估

这是评审材料，不是已完成的模型评测。它回答一个问题：当前 dv-build 在真实旧项目/新项目任务里，是否会先看现有实现、复用现有能力、避免性能反模式。

## 目录

- `fixtures/legacy-java`：Spring Boot 旧项目，已有 `CsvExportWriter`、`CustomerExportService`、分页接口、N+1、深 offset 查询
- `fixtures/legacy-py`：FastAPI 旧项目，已有 `format_dt`、`orders_to_csv`，两种 session 用法并存
- `fixtures/fullstack-orders`：无依赖全栈项目，后端标准库、前端 vanilla JS，已有筛选/分页/状态基线
- `fixtures/saas-billing`：带 SQLite 的多租户 SaaS 计费项目，含租户、套餐、订阅、用量、账单和仪表盘
- `fixtures/greenfield`：空仓库
- `scenarios.json`：12 个行为场景，prompt 与期望分离
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

# 链路臂：加载插件并按 dv-route 链路调用 build/test/review/done
python3 evals/build-scenarios/run.py --scenario S1-reuse-csv-export \
  --scenario S6-small-change-overhead --runs 3 --chain --arm chain

# 基线臂：不加载插件，并禁用所有技能
python3 evals/build-scenarios/run.py --scenario S1-reuse-csv-export \
  --scenario S6-small-change-overhead --runs 3 --no-plugin --arm no-skill
```

两臂 prompt 不完全相同：技能臂多一句显式调用指令，基线臂是原始 prompt；结果用于比较技能体是否改善任务，不用于测自然触发率。`--no-plugin`、`--explicit-skill`、`--chain`、`--skills` 四者互斥。`--chain` 测的是 route 编排后的多技能链路，不是单个技能体。

消融臂：

```bash
# 只测 build
python3 evals/build-scenarios/run.py --scenario S9-fullstack-backend-filter \
  --runs 2 --skills dv-build --arm ablation-build

# 测 build+test，判断 test 的增量
python3 evals/build-scenarios/run.py --scenario S9-fullstack-backend-filter \
  --runs 2 --skills dv-build,dv-test --arm ablation-build-test

# 测 build+test+review，判断 review 的增量
python3 evals/build-scenarios/run.py --scenario S9-fullstack-backend-filter \
  --runs 2 --skills dv-build,dv-test,dv-review --arm ablation-build-test-review
```

消融结果按 `compare.py` 汇总；只有 `build+test` 明显优于 `build-only`，才说明 test 有独立价值。

指定宿主与模型（不传则用宿主默认）：

```bash
python3 evals/build-scenarios/run.py --scenario S6-small-change-overhead --runs 3 \
  --explicit-skill --host qoder --model claude-fable-5 --arm qoder-with
python3 evals/build-scenarios/run.py --scenario S6-small-change-overhead --runs 3 \
  --no-plugin --host qoder --model claude-fable-5 --arm qoder-no
```

`--host claude`（缺省）驱动 Claude Code；`--host qoder` 驱动 Qoder CLI CN，需串行执行，模型名以 `-m` 原样传入。实际模型记在结果目录的 `meta.json`。

## 判定

每个场景有确定性检查（diff/文件数/依赖是否变化/响应关键词）、可选隐藏测试和可选 LLM 评审（按 `expectations` 逐条判）。确定性检查通过不等于任务成功；必须同时看 diff 和 trace。

`hidden_tests` 会把 `hidden/<suite>` 复制到临时仓库的 `copy_to` 目录，运行 `command` 后删除；隐藏测试不在发给模型的 prompt 或 fixture 中，避免答案泄漏。

## 前后端 A/B pilot

`fullstack-orders` 是新增的离线全栈 fixture：后端 Python 标准库、前端 vanilla JS + Node 内置 test，不需要安装依赖。S9/S10 分别覆盖：

- S9 后端：按客户名 + 状态筛选，修复循环内逐单查询，保持分页结构。
- S10 前端：客户名搜索 + 状态筛选，补齐 loading/error/empty/ready 四态，复用现有日期/转义工具。

三臂对照：

```bash
# 基线：不加载插件，禁用所有技能
python3 evals/build-scenarios/run.py --scenario S9-fullstack-backend-filter \
  --scenario S10-fullstack-frontend-states --runs 3 --no-plugin --arm fullstack-no-skill

# 自然触发：加载插件，使用原始 prompt
python3 evals/build-scenarios/run.py --scenario S9-fullstack-backend-filter \
  --scenario S10-fullstack-frontend-states --runs 3 --arm fullstack-natural

# 技能体：加载插件并显式要求使用 dv-build
python3 evals/build-scenarios/run.py --scenario S9-fullstack-backend-filter \
  --scenario S10-fullstack-frontend-states --runs 3 --explicit-skill --arm fullstack-explicit
```

### 2026-11-02 结果

Claude Code 2.1.267 / `deepseek[1m]`，每臂每任务 3 次：

| 臂 | S9 隐藏/全部 | S10 隐藏/全部 | S9 文件/耗时/token | S10 文件/耗时/token | 技能调用 |
|---|---|---|---|---|---|
| no-skill | 3/3, 3/3 | 3/3, 0/3 | 2.7 / 60.3s / 1,877 | 5.7 / 97.7s / 11,910 | 0 |
| natural | 3/3, 3/3 | 3/3, 0/3 | 2.3 / 62.0s / 1,660 | 6.0 / 89.8s / 11,116 | 0 |
| explicit | 3/3, 3/3 | 3/3, 0/3 | 2.0 / 82.1s / 3,866 | 5.0 / 150.2s / 19,120 | 3 |

- 隐藏验收三臂完全一致；S10 的“全部检查”失败来自 `changed_files_max` 和 `changed_files_prefix`，三臂都把 backend 一起改了。
- 显式 `dv-build` 只增加成本：S9 耗时 +36%/token +106%，S10 耗时 +54%/token +61%。
- natural 臂两轮共 12 次运行 0 次 Skill 调用。改 description 后词法 top1 已是 `dv-build`（S9 0.189、S10 0.252），宿主仍不调用；该宿主/模型下 description 不足以保证自然触发。
- S9 基线全过，存在天花板；本 pilot 不支持“简单前后端任务默认启用有必要”，只支持高风险/复杂任务的显式护栏假设。

判定口径：隐藏测试通过率是主指标；关键违规、改动文件数、工具调用、耗时和输出 token 是辅助指标。`explicit ≈ no-skill` 表示技能体没有质量收益；`natural < no-skill` 表示触发是主要成本；只有 `explicit > no-skill` 才说明技能体改善了任务。

pilot 默认每个场景跑 3 次，只能看方向；要证明小差异需要更多任务和重复次数。

结果汇总：

```bash
python3 evals/build-scenarios/compare.py \
  evals/build-scenarios/results/<no-skill-dir> \
  evals/build-scenarios/results/<natural-dir> \
  evals/build-scenarios/results/<explicit-dir>
```

## SaaS 计费 A/B

`saas-billing` 是带 SQLite 的多租户计费项目：后端标准库 + `sqlite3`，前端 vanilla JS + Node 内置 test，无需安装依赖。S11/S12 分别覆盖：

- S11 后端：按套餐月费/包含额度/超额微单价生成 2026-10 账单；金额按分四舍五入；重复执行幂等；列表租户隔离、状态/账期筛选、游标分页；用量聚合不逐租户查询。
- S12 前端：账期 + 状态组合筛选；总额与用量汇总；loading/error/empty/ready 四态；整数分金额与租户名转义。

fixture 基线保留了真实遗留缺陷：超额金额截断、税额浮点截断、重复执行撞唯一键、`get_invoice` 跨租户泄漏、列表无筛选/游标、前端无空态/账期筛选/转义。隐藏测试分别覆盖这些点，并会重跑 fixture 自带测试防止回归。

```bash
# 基线：不加载插件，禁用所有技能
python3 evals/build-scenarios/run.py --scenario S11-saas-billing-backend \
  --scenario S12-saas-billing-dashboard --runs 2 --timeout 900 \
  --no-plugin --arm saas-no-skill

# 自然触发：加载插件，使用原始 prompt
python3 evals/build-scenarios/run.py --scenario S11-saas-billing-backend \
  --scenario S12-saas-billing-dashboard --runs 2 --timeout 900 \
  --arm saas-natural

# 链路：加载插件，显式要求 dv-route 编排 build/test/review/done
python3 evals/build-scenarios/run.py --scenario S11-saas-billing-backend \
  --scenario S12-saas-billing-dashboard --runs 2 --timeout 900 \
  --chain --arm saas-chain
```

判定仍以隐藏测试通过率为主；`changed_files_prefix` 强制 S11 只改 `backend/`、S12 只改 `frontend/`，`manifest_unchanged` 防止新增依赖。

### 2026-11-02 结果

Claude Code 2.1.267 / `deepseek[1m]`，每臂每任务 2 次：

| 臂 | S11 任务/隐藏 | S12 任务/隐藏 | S11 文件/工具/耗时/token | S12 文件/工具/耗时/token | 技能调用 |
|---|---|---|---|---|---|
| no-skill | 2/2, 2/2 | 2/2, 2/2 | 4.5 / 35.5 / 266.6s / 31,634 | 3.5 / 28.5 / 95.7s / 10,613 | 0 |
| natural | 2/2, 2/2 | 1/2, 2/2 | 4.5 / 27.5 / 172.4s / 21,524 | 5.0 / 50.5 / 215.7s / 25,765 | 0 |
| chain | 2/2, 2/2 | 2/2, 2/2 | 4.0 / 60.0 / 596.0s / 45,717 | 3.0 / 43.5 / 195.4s / 20,808 | 13（逐次 5/3/5/0） |

- 隐藏验收三臂全部通过（每臂 4/4）；在这两个任务上，技能没有带来可测的功能正确性增益。
- 唯一任务级失败是 natural 的 S12 第 2 次：它顺手修了 `backend/app/billing.py` 等 4 个后端文件，触发 `changed_files_max` 与 `changed_files_prefix`。S12 prompt 只描述仪表盘、未显式写“只改前端”，这是范围口径的已知歧义。
- chain 后端平均耗时是 no-skill 的 2.2 倍、natural 的 3.5 倍，输出 token 是 no-skill 的 1.45 倍；前端 chain 约 2 倍于 no-skill。
- chain 的技能调用不稳定：4 次运行中 2 次走完 route→build→test→review→done，1 次停在 test，1 次 0 次 Skill 调用但仍通过全部检查。单轮 headless 下，显式 prompt 不能保证技能被调用或链路连续执行。
- chain 走完整链路时给出了更完整的验证证据和边界条件（如一租户多订阅的计费口径），但这些没有转化为隐藏测试差异；no-skill/natural 也自行补了测试与 CLI 验证。
- n=2 只能看方向；任务难度仍未击穿强模型基线，不能据此判断技能在更复杂遗留系统或跨模块改动中无价值。

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
- `legacy-java`/`legacy-py` 是合成项目，不自带可运行数据库；`saas-billing` 带可运行 SQLite，但数据仍是合成的，测行为不测真实编译/集成。
- 链路臂的 prompt 明确点名 route/build/test/review/done；它测编排路径，不代表宿主会自然触发整条链路。
- with 臂多一句显式调用指令，与 no 臂原始 prompt 不对称；只能测技能体效果，不能当自然触发率。
- n=3 不足以证明稳定性；结论按方向使用，不按百分点使用。


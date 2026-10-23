# devkit 使用手册

> 本文件手写，只放不随技能定义变化的内容：场景、常见问题、排错、跨端差异。
> 技能总表由 `scripts/dv-help-gen.py` 生成，不要在这里重复。

---

## 5 个场景：你只需要说人话

### 场景 A · 小 bug

**你说**

> 登录接口 500 了

**自动链**

```
dv-debug（模型自动接手）
  → 建能红的复现 → 修 → 回归测试
  → 提示「接着跑 /dv-done」
```

**你打了 0 个技能名。**

### 场景 B · 中等功能

**你说**

> 加个导出功能，但我不确定要导出哪些字段

**链**

```
/dv-grill      每轮 ≤5 问，问完落 spec 草稿
   ↓
/dv-plan       ⏸ 确认规格 → 拆工单 → ⏸ 确认拆分
   ↓
/dv-build      每个工单一次，内含红绿循环
   ↓
dv-review      自动，三轴分开报告
   ↓
/dv-done       ⏸ 确认后提交
```

**你按 3 次**（grill / plan / done），其中 3 个是确认点。

### 场景 C · 大改造

**你说**

> OTA 平台要整合 deb 和符号归档，我摸不太清

**链**

```
/dv-route          → 建议先 shape + research 并行
/dv-arch shape     → ADR + 接缝建议
/dv-research       → 后台取证
/dv-grill          → 收敛未定项
/dv-plan
/dv-arch migrate   → 若涉及宽重构：expand → migrate → contract
/dv-build × N
dv-review（自动） → /dv-done
```

### 场景 D · 只做前端

**你说**

> 这个列表页要重做

**链**

```
/dv-design     结构 + 状态矩阵 + 异常态 + 动效四问 → HTML 稿
/dv-build
/dv-browser    极端数据：超长名 / 空列表 / 1 万条 / 超大数字
/dv-done       结论里声明「DOM 探针验证，未肉眼核对」
```

### 场景 E · 不想一步步点

```
/dv-route --auto
```

只说目标，它按状态机推进，**只在 3 处停**：规格定稿前、工单拆分后、提交前。

---

## 常见问题

**Q：记不住 16 个怎么办？**
只记 3 个：`/dv-grill` `/dv-plan` `/dv-build`。其余 4 个自己会来（route / debug / research / review），9 个季节型想不起来就问 `/dv-route`。全忘了就 `/dv-help`。

**Q：`dv-route` 和 `dv-help` 有什么区别？**
`dv-route` 回答「我现在该干什么」，输出祈使句，只给一个推荐。
`dv-help` 回答「这套东西怎么用」，输出陈述句，给手册。
判定：需要**决定**用 route，需要**查询**用 help。

**Q：为什么有些技能模型不会自己触发？**
那是刻意的。12 个技能是「仪式」（写 spec、拆工单、提交），模型自己发起会让你被流程推着走——这正是 superpowers 被弃用的原因。只有 4 个症状客观的技能允许自动触发。

**Q：`dv-plan` 里有两个 STOP，必须停吗？**
必须。spec 没确认就拆工单，拆错会一路传到实现；工单没确认就开工，验收无法归因。`--auto` 也只在这两处加提交前三处停。

**Q：`dv-test design` 和 `dv-test run` 混了会怎样？**
design 会去写测试代码（越界），run 会跳过边界推导（漏用例）。技能正文里写死了互斥句，混用时它会拒绝并让你选模式。

**Q：产物路径能不能改？**
能。`.devkit/config.json` 的 `paths` 可把 specs / issues / status / state 指到项目已有目录（如 `.ai/specs`）。改完跑 `/dv-context` 验证。**不要两套并存。**

**Q：`state.json` 和 `STATUS.md` 不一致听谁的？**
下一步听 `state.json`（机器游标），人读进度看 `STATUS.md`。下次 `/dv-done` 时修正 STATUS。

---

## 排错

### 技能该触发却没触发

1. 看 `description` 里有没有你这次的说法（Triggers 是英文，中文主句才是主要匹配面）
2. L2 技能本来就只能手动，先确认它不是 L2
3. 跑 `python3 scripts/lint.py`，检查 description 长度与流程词
4. 还是不行 → `/dv-author` 的「触发不准」流程，拿 3–5 条真实原话回归

### stage 卡住了

```
cat .devkit/state.json
```

- `stage` 与你要做的事不符 → 手动改成目标 stage，或直接跑对应技能（技能会自己覆写）
- `next` 指向不存在的技能 → 跑 lint
- 文件损坏 → `/dv-context` 重建

### hook 没注入状态行

- Claude Code：`settings.json` 的 `hooks.UserPromptSubmit` 里是否有 `dv-hook.sh`
- Qoder CN：`~/.qoder-cn/settings.json` 的同名事件；**Qoder 是否把 hook stdout 注入上下文尚未实测**
- 都不行：降级为纯手动，交接段仍然有效（每个技能末尾都写了下一步）

### 视觉验收时读不到图

用 DOM / 几何 / PDF 探针代替，并在结论里明确写「未做像素级肉眼核对」。`dv-browser` 的输出模板最后一段就是为此设计的。

---

## 跨端差异

| 能力 | Claude Code | Qoder CN | Codex |
|---|---|---|---|
| `disable-model-invocation` | ✅ | ❌ | ✅ |
| `user-invocable` | 忽略 | ✅ | 忽略 |
| `agents/openai.yaml` | 忽略 | ✅ | ✅ |
| hook 注入 | ✅ | 待实测 | — |
| 技能目录 | `skills/*/SKILL.md` | 同 | 同 |

结论：L2 的三键必须**同时**写，缺哪个端就会被自动触发。`lint.py` 规则 6/7 强制。

---

## 我要新增一个技能吗？

先回答：**现有 16 个里，有没有哪个加一节就能解决？**
有 → 用 `/dv-author` 改那个技能。
没有 → 新技能必须通过三个检验：

1. 有独立的 `stage` 或 `edits-code` 语义（不能和现有技能同质）
2. 有明确的 `next`（不能是孤岛）
3. 描述能写出「不适用时指向谁」

三条缺一条，就不要加。

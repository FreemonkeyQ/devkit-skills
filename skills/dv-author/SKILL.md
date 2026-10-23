---
name: dv-author
description: 仅在明确要求维护技能仓库时创建、修改或评估技能；低频能力按价值评估，不机械淘汰。
user-invocable: true
metadata:
  stage: meta
  summary: 维护技能与评估质量
  effects:
  - docs
  - tests
  - business-code
  explicit-actions: []
  next: []
---

# 技能维护与评估

## 适用 / 不适用
仅用户明确要求新建/修改/评估技能仓库时使用；业务研发用route，使用查询用help。加载不等于授权改任意项目。

## 流程
1. 新技能先评估是否可在现有职责内增加模式/参考；职责确需独立才新增。低频安全/迁移/发布技能不按30天零使用机械淘汰，结合价值、周期、维护成本提出建议。
2. 使用既有frontmatter与metadata：stage、effects、explicit-actions、next、summary；effects表示能力，不是宿主强制权限。常规技能自然语言可调；高风险动作写明意图与环境授权。
3. 正文聚焦任务、输入、适用/不适用、步骤、证据与边界；约120行是预算而非必须砍知识，深入内容放references。短description写what/when与排除，别靠关键词堆砌。
4. 调整后更新元数据/帮助生成与引用；使用规范YAML解析而非自造不完整解析器。next允许反馈回路，只验证目标存在，不充当执行状态机。
5. 运行结构/单元/契约fixture；真实模型行为另用 evals/scenarios.json 与 docs/evaluation.md 记录模型/宿主/版本/输入/调用日志/副作用/结果。输出名字不算执行成功，测试通过不算所有宿主兼容。
6. 不自动发布安装提交；遵守仓库权限。使用统计只读相关聚合数据，不扫描原始会话或凭据。

## 自检
报告优点、证据与局限，不强行找茬或声称全量替代。第三方引入需核许可证与版本/文件，NOTICE泛称MIT不代替原版权保留。

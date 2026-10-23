# <范围> 评审

- 比较点：`<fixed>`
- 命令：`git diff <fixed>...HEAD`
- 提交：`git log <fixed>..HEAD --oneline`
- 日期：YYYY-MM-DD

## Correctness

（找 bug：边界、空值、并发、错误路径、资源泄漏；smell 基线一律标为判断项）

## Standards

（逐条对照仓库文档化规范，引用出处；硬违规与判断项分开）

## Spec

（缺失 / 超范围 / 实现错，每条引 spec 原句；无 spec 则写「Spec 轴跳过」）

---

合计：Correctness N 项 / Standards N 项 / Spec N 项
各轴最严重：<按轴各一句，不跨轴排名>

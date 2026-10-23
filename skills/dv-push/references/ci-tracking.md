# CI跟踪，不另开本地部署路径

## 推送前
读取实际CI配置和仓库发布约定：push/MR/merge/tag/manual何者触发、目标环境、是否自动生产部署。
提交不触发远程CI，push等事件才可能触发。普通push不能覆盖项目额外生产发布许可。

## 关联
记录推送后SHA、分支、remote；通过已有GitLab/GitHub CLI/API权限查询流水线。
候选必须匹配目标SHA+分支/事件，多个pipeline区分push/MR/child，别把最新绿当本次。
默认提供链接与当前状态；没有CI工具/权限就明确未查询。不能通过猜URL报告真实pipeline存在。

## 状态
等待启动/queued/running/passed/failed/canceled/skipped/manual/未找到分别汇报。
“等部署结果”有等待截止时间、适当查询间隔与用户中断；manual等待用户，不自行批准。
只推代码不自动retry、trigger、cancel job、改workflow、SSH/kubectl部署或回滚。
请求重试/部署仍须确认环境、影响、目标版本与权限，优先既有CI发布链路。

## 结果
push成功、构建通过、测试通过、部署执行、实际运行版本、业务验收分项报告。
Pipeline总体绿不一定包含部署（可能跳过/手工），功能绿仍需对应验收证据。

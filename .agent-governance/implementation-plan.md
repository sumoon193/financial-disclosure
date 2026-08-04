# 财务披露核验工作台 完整实施计划

> 本文是开发执行合同，不是学习材料或完成证明。每一模块必须由独立任务分支按依赖顺序实施，先观察失败测试，再做最小实现。

## 全局精确路径与边界

- 生产代码根：`app/financial_disclosure`。
- 任务只能修改本模块 `source_paths/test_paths` 与任务包白名单；Runtime Kernel、秘密和其他模块默认只读或禁止。
- 接口签名、数据表、API、状态和错误语义以 `.agent-governance/module-contracts.json` 为机器真源。
- 每次激活任务时，主集成模型把任务 `base_sha` 重绑定为当前集成提交，再由实现模型创建精确分支。

## 公共接口签名、数据表与 API

### 接口签名
- `FilingSourcePort.fetch(identity: FilingIdentity) -> SourceArtifact`
- `VerificationPort.verify(run: VerificationRun) -> VerificationResult`

### 数据表
- `filing`：必须有主键、版本/幂等键、创建更新时间与审计来源。
- `document_version`：必须有主键、版本/幂等键、创建更新时间与审计来源。
- `xbrl_fact`：必须有主键、版本/幂等键、创建更新时间与审计来源。
- `verification_run`：必须有主键、版本/幂等键、创建更新时间与审计来源。
- `discrepancy`：必须有主键、版本/幂等键、创建更新时间与审计来源。
- `review_decision`：必须有主键、版本/幂等键、创建更新时间与审计来源。

### API
- `POST /filings`：使用 typed request/response、稳定错误码、request/correlation ID 与权限校验。
- `GET /filings/{id}`：使用 typed request/response、稳定错误码、request/correlation ID 与权限校验。
- `POST /verification-runs`：使用 typed request/response、稳定错误码、request/correlation ID 与权限校验。
- `GET /verification-runs/{id}/timeline`：使用 typed request/response、稳定错误码、request/correlation ID 与权限校验。

## 模块逐项执行

### FD-01 来源、许可证与公开样例基线

- 依赖：`无`。
- 精确路径：`docs/audit/**`, `tests/financial_disclosure/audit/**`。
- 接口签名：`FilingIdentity.execute(input: FD01Input) -> FD01Result`。
- 数据表：`document_version`；迁移必须向前/向后兼容并保留审计事实。
- API：`/verification-runs`；禁止把领域决策写入控制器。
- 状态：`created -> evidence_ready -> computed -> reviewed -> completed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/financial_disclosure/fd_01`，失败原因只能是目标行为未实现。
- 可观察结果：每个 filing 样例具有来源、版本和许可证状态。
- 回归命令：`python -m pytest tests/financial_disclosure -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### FD-02 Typed API、状态与错误合同

- 依赖：`FD-01`。
- 精确路径：`app/financial_disclosure/contracts/**`, `tests/financial_disclosure/contracts/**`。
- 接口签名：`CitationAnchor.execute(input: FD02Input) -> FD02Result`。
- 数据表：`verification_run`；迁移必须向前/向后兼容并保留审计事实。
- API：`/verification-runs`；禁止把领域决策写入控制器。
- 状态：`created -> evidence_ready -> computed -> reviewed -> completed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/financial_disclosure/fd_02`，失败原因只能是目标行为未实现。
- 可观察结果：Filing/Verification API 使用固定 typed output。
- 回归命令：`python -m pytest tests/financial_disclosure -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### FD-03 SEC、XBRL 与 HTML 摄取

- 依赖：`FD-02`。
- 精确路径：`app/financial_disclosure/ingestion/**`, `tests/financial_disclosure/ingestion/**`。
- 接口签名：`VerificationResult.execute(input: FD03Input) -> FD03Result`。
- 数据表：`document_version`；迁移必须向前/向后兼容并保留审计事实。
- API：`/verification-runs`；禁止把领域决策写入控制器。
- 状态：`created -> evidence_ready -> computed -> reviewed -> completed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/financial_disclosure/fd_03`，失败原因只能是目标行为未实现。
- 可观察结果：重复摄取幂等且 filing identity 不混淆 amendment。
- 回归命令：`python -m pytest tests/financial_disclosure -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### FD-04 规范化与 Decimal 公式血缘

- 依赖：`FD-03`。
- 精确路径：`app/financial_disclosure/normalization/**`, `app/financial_disclosure/formulas/**`, `tests/financial_disclosure/formulas/**`。
- 接口签名：`FilingIdentity.execute(input: FD04Input) -> FD04Result`。
- 数据表：`verification_run`；迁移必须向前/向后兼容并保留审计事实。
- API：`/verification-runs`；禁止把领域决策写入控制器。
- 状态：`created -> evidence_ready -> computed -> reviewed -> completed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/financial_disclosure/fd_04`，失败原因只能是目标行为未实现。
- 可观察结果：数值计算保留单位、scale、rounding和输入血缘。
- 回归命令：`python -m pytest tests/financial_disclosure -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### FD-05 三路检索与模型 adapter

- 依赖：`FD-04`。
- 精确路径：`app/financial_disclosure/retrieval/**`, `app/financial_disclosure/model/**`, `tests/financial_disclosure/retrieval/**`。
- 接口签名：`CitationAnchor.execute(input: FD05Input) -> FD05Result`。
- 数据表：`document_version`；迁移必须向前/向后兼容并保留审计事实。
- API：`/verification-runs`；禁止把领域决策写入控制器。
- 状态：`created -> evidence_ready -> computed -> reviewed -> completed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/financial_disclosure/fd_05`，失败原因只能是目标行为未实现。
- 可观察结果：检索返回版本 citation且模型只解释已计算事实。
- 回归命令：`python -m pytest tests/financial_disclosure -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### FD-06 只读核验链路

- 依赖：`FD-05`。
- 精确路径：`app/financial_disclosure/verification/**`, `tests/financial_disclosure/verification/**`。
- 接口签名：`VerificationResult.execute(input: FD06Input) -> FD06Result`。
- 数据表：`verification_run`；迁移必须向前/向后兼容并保留审计事实。
- API：`/verification-runs`；禁止把领域决策写入控制器。
- 状态：`created -> evidence_ready -> computed -> reviewed -> completed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/financial_disclosure/fd_06`，失败原因只能是目标行为未实现。
- 可观察结果：规则核验输出 discrepancy、tolerance、provenance和citations。
- 回归命令：`python -m pytest tests/financial_disclosure -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### FD-07 PDF/OCR 准入

- 依赖：`FD-06`。
- 精确路径：`app/financial_disclosure/ocr/**`, `tests/financial_disclosure/ocr/**`。
- 接口签名：`FilingIdentity.execute(input: FD07Input) -> FD07Result`。
- 数据表：`document_version`；迁移必须向前/向后兼容并保留审计事实。
- API：`/verification-runs`；禁止把领域决策写入控制器。
- 状态：`created -> evidence_ready -> computed -> reviewed -> completed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/financial_disclosure/fd_07`，失败原因只能是目标行为未实现。
- 可观察结果：只有通过冻结准入指标的PDF/OCR路径可启用。
- 回归命令：`python -m pytest tests/financial_disclosure -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### FD-08 持久化、幂等、租约与缓存

- 依赖：`FD-07`。
- 精确路径：`app/financial_disclosure/persistence/**`, `migrations/financial_disclosure/**`, `tests/financial_disclosure/persistence/**`。
- 接口签名：`CitationAnchor.execute(input: FD08Input) -> FD08Result`。
- 数据表：`verification_run`；迁移必须向前/向后兼容并保留审计事实。
- API：`/verification-runs`；禁止把领域决策写入控制器。
- 状态：`created -> evidence_ready -> computed -> reviewed -> completed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/financial_disclosure/fd_08`，失败原因只能是目标行为未实现。
- 可观察结果：版本化事实、查询缓存和worker租约可恢复。
- 回归命令：`python -m pytest tests/financial_disclosure -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### FD-09 迁移、回滚与对象生命周期

- 依赖：`FD-08`。
- 精确路径：`app/financial_disclosure/lifecycle/**`, `tests/financial_disclosure/lifecycle/**`。
- 接口签名：`VerificationResult.execute(input: FD09Input) -> FD09Result`。
- 数据表：`document_version`；迁移必须向前/向后兼容并保留审计事实。
- API：`/verification-runs`；禁止把领域决策写入控制器。
- 状态：`created -> evidence_ready -> computed -> reviewed -> completed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/financial_disclosure/fd_09`，失败原因只能是目标行为未实现。
- 可观察结果：active版本切换可回滚且旧审计事实保留。
- 回归命令：`python -m pytest tests/financial_disclosure -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### FD-10 OTel、安全与权限

- 依赖：`FD-09`。
- 精确路径：`app/financial_disclosure/security/**`, `app/financial_disclosure/observability/**`, `tests/financial_disclosure/security/**`。
- 接口签名：`FilingIdentity.execute(input: FD10Input) -> FD10Result`。
- 数据表：`verification_run`；迁移必须向前/向后兼容并保留审计事实。
- API：`/verification-runs`；禁止把领域决策写入控制器。
- 状态：`created -> evidence_ready -> computed -> reviewed -> completed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/financial_disclosure/fd_10`，失败原因只能是目标行为未实现。
- 可观察结果：来源、检索、核验和review具有脱敏Trace和权限隔离。
- 回归命令：`python -m pytest tests/financial_disclosure -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### FD-11 冻结评测、检索消融与真实模型试验

- 依赖：`FD-10`。
- 精确路径：`app/financial_disclosure/eval/**`, `tests/financial_disclosure/eval/**`。
- 接口签名：`CitationAnchor.execute(input: FD11Input) -> FD11Result`。
- 数据表：`document_version`；迁移必须向前/向后兼容并保留审计事实。
- API：`/verification-runs`；禁止把领域决策写入控制器。
- 状态：`created -> evidence_ready -> computed -> reviewed -> completed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/financial_disclosure/fd_11`，失败原因只能是目标行为未实现。
- 可观察结果：数值、citation和检索收益由冻结集验证。
- 回归命令：`python -m pytest tests/financial_disclosure -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

### FD-12 完整演练、发布与真实性审计

- 依赖：`FD-11`。
- 精确路径：`scripts/financial_disclosure/**`, `docs/financial_disclosure/release/**`, `tests/financial_disclosure/release/**`。
- 接口签名：`VerificationResult.execute(input: FD12Input) -> FD12Result`。
- 数据表：`verification_run`；迁移必须向前/向后兼容并保留审计事实。
- API：`/verification-runs`；禁止把领域决策写入控制器。
- 状态：`created -> evidence_ready -> computed -> reviewed -> completed`，非法转换必须稳定拒绝。
- 失败测试：先创建/运行 `tests/financial_disclosure/fd_12`，失败原因只能是目标行为未实现。
- 可观察结果：来源中断、解析失败和回滚有真实演练记录。
- 回归命令：`python -m pytest tests/financial_disclosure -q`。
- 交接：记录 RED/GREEN、实际改动、未运行项、风险、commit SHA；禁止 merge 和 force-push。

## 跨模块集成与真实性门禁

- 按依赖拓扑合并；每次合并后运行合同测试、全回归、构建、安全、故障恢复与回滚演练。
- 对数据库、消息、缓存、外部副作用执行崩溃点测试，核对幂等键、租约、Outbox/Inbox、SideEffect Ledger 和 UNKNOWN 对账。
- 远端分支保护、真实外部服务、真实模型或真实数据未执行时必须列为 unverified，不能以本地 Fake 结果替代。
- 所有模块构建、主集成优化、Bug 修复和最终验证前，禁止生成任何学习解释、项目总结、面试或简历文档。

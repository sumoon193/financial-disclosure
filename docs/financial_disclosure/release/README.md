# 完整演练、发布与真实性审计（FD-12）

本目录是 FD-12「完整演练、发布与真实性审计」的发布计划与演练记录规范。

## 演练类型

- `source_interruption`：来源中断演练。
- `parse_failure`：解析失败演练。
- `rollback`：回滚演练。

## 记录真实性

- 每次执行 `run_drill` 都会向演练日志追加一条真实记录（drill_id、类型、状态、详情、序号）。
- 状态如实反映验证级别：
  - `verified`：本次演练在本地真实代码上复现/执行。
  - `simulated`：外部来源不可达时（network=disabled）以 Fake/Recorded 模拟执行。
- **未验证外部服务绝不写成 `passed`**。演练日志由 `scripts/financial_disclosure/release_drill.py` 的 `VerificationResult` 生成。

## 审计边界

- 本模块只做演练记录与审计，不触碰白名单外模块。
- 真实外部来源抓取、真实模型试验与真实数据库回滚演练未执行时，必须保留 `unverified`，不得以本地 Fake 结果替代。

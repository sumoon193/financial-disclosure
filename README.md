# 财务披露核验工作台

契约驱动的财务披露核验与审计系统：对 SEC / XBRL / HTML 披露文档实施幂等摄取、Decimal 公式血缘计算、只读规则核验、版本化持久化与脱敏审计，用确定性 Fake/Recorded adapter 替代真实外部依赖（模型未接入真实 LLM）。

## 12 模块架构

每个模块以 typed 合同入口（`execute(input) -> result`）暴露，输出不可变 `frozen` dataclass，错误以稳定错误码的 `ErrorContract` 返回，永不抛裸异常到 API 边界。

| 模块 | 标题 | 依赖 | 可观察结果 |
|---|---|---|---|
| FD-01 | 来源、许可证与公开样例基线 | — | 每个 filing 样例具有来源、版本和许可证状态 |
| FD-02 | Typed API、状态与错误合同 | FD-01 | Filing/Verification API 使用固定 typed output |
| FD-03 | SEC、XBRL 与 HTML 摄取 | FD-02 | 重复摄取幂等且 filing identity 不混淆 amendment |
| FD-04 | 规范化与 Decimal 公式血缘 | FD-03 | 数值计算保留单位、scale、rounding 和输入血缘 |
| FD-05 | 三路检索与模型 adapter | FD-04 | 检索返回版本 citation 且模型只解释已计算事实 |
| FD-06 | 只读核验链路 | FD-05 | 规则核验输出 discrepancy、tolerance、provenance、citations |
| FD-07 | PDF/OCR 准入 | FD-06 | 只有通过冻结准入指标的 PDF/OCR 路径可启用 |
| FD-08 | 持久化、幂等、租约与缓存 | FD-07 | 版本化事实、查询缓存和 worker 租约可恢复 |
| FD-09 | 迁移、回滚与对象生命周期 | FD-08 | active 版本切换可回滚且旧审计事实保留 |
| FD-10 | OTel、安全与权限 | FD-09 | 来源、检索、核验和 review 具有脱敏 Trace 和权限隔离 |
| FD-11 | 冻结评测、检索消融与真实模型试验 | FD-10 | 数值、citation 和检索收益由冻结集验证 |
| FD-12 | 完整演练、发布与真实性审计 | FD-11 | 来源中断、解析失败和回滚有真实演练记录 |

依赖拓扑线性无环：`FD-01 → FD-02 → ... → FD-12`。机器真源为 `.agent-governance/module-contracts.json`。

## 快速运行

```bash
# 全回归
python -m pytest tests/financial_disclosure -q

# 构建（编译检查）
python -m compileall -q app tests scripts

# 静态检查（需 pip install ruff mypy）
python -m ruff check app tests scripts
python -m mypy app/financial_disclosure
```

生产代码根：`app/financial_disclosure`；冻结演练脚本：`scripts/financial_disclosure/release_drill.py`；持久化 schema：`migrations/financial_disclosure/001_persistence.sql`。

## 治理

本项目只接受任务包驱动开发，默认离线、Fake/Recorded、测试先行。开发必须遵守 [`AGENTS.md`](AGENTS.md) 与 [`.agent-governance/`](.agent-governance/)（manifest、module-contracts、tasks）。禁止秘密、force-push、自动合并与未授权副作用；真实外部服务、真实模型、真实数据流未执行时必须列为 `unverified`。

跨模块不变式见 `module-contracts.json`：服务端可信身份不可由模型覆盖、写副作用必须审批幂等并处理 UNKNOWN 对账、状态推进必须经 typed command 与合法状态机、单元测试禁止网络、用户可见结论必须关联 provenance/citation。
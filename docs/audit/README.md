# 来源、许可证与公开样例基线（FD-01）

本目录是 FD-01「来源、许可证与公开样例基线」的可观察合同交付物：公开样例基线数据与来源/许可证策略。接口签名以 `.agent-governance/module-contracts.json` 为机器真源：

- 接口：`FilingIdentity.execute(input: FD01Input) -> FD01Result`
- 可观察结果：**每个 filing 样例具有来源、版本和许可证状态**

## 公开样例基线

`sample-baseline.json` 是只读基线，包含每个样例的 `sample_id`、`source`、`version`、`license_status`。合同测试要求每个样例三个字段全部非空，并由 `FilingIdentity.execute` 以 typed 结果返回同一合同。

## 来源策略

- 主来源：SEC EDGAR 公开数据集（`sec-edgar`）。
- 检索方式：Fake/Recorded adapter。单元测试禁止网络（跨模块不变式：外部依赖必须有 Fake 或 Recorded adapter，单元测试禁止网络）。
- 样例中的 `sample_id` 引用 SEC EDGAR 公开 CIK（如 0000320193 / 0000789019 / 0001652044）。这些是合同基线记录，作为公开来源标识使用；accession 级端到端抓取证据的核验不在 FD-01 范围内，计划由 FD-12「完整演练、发布与真实性审计」完成。

## 许可证策略

- SEC EDGAR 公开数据属于美国政府作品，许可证状态为 `public-domain`。
- 任何派生记录必须携带来源与版本（provenance/citation），证据不足时保持 `blocked/review`，不得写成已验证。

## 边界

- FD-01 只实现「每个 filing 样例具有来源、版本和许可证状态」的最小合同，不扩展相邻模块。
- 未验证的外部服务不得写成通过；本目录内容不是已核验的抓取证据。

"""FD-01 最小合同实现：来源、许可证与公开样例基线。

只实现使“每个 filing 样例具有来源、版本和许可证状态”成立的
单一可观察合同，不扩展相邻模块（见 FD-01 实施边界）。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FD01Input:
    """filing 样例标识输入。"""

    sample_id: str


@dataclass(frozen=True)
class FD01Result:
    """filing 样例的单一可观察合同输出。

    每个 filing 样例必须具有来源、版本和许可证状态。
    """

    sample_id: str
    source: str
    version: str
    license_status: str


class FilingIdentity:
    """对公开样例基线实施来源、版本与许可证状态合同。

    基线仅接受已登记 sample_id；未知样例必须稳定失败，不得静默通过。
    """

    def __init__(self, baseline: dict[str, dict[str, str]]) -> None:
        self._baseline = dict(baseline)

    def execute(self, input: FD01Input) -> FD01Result:
        entry = self._baseline.get(input.sample_id)
        if entry is None:
            raise KeyError(f"unknown filing sample: {input.sample_id}")
        return FD01Result(
            sample_id=input.sample_id,
            source=entry["source"],
            version=entry["version"],
            license_status=entry["license_status"],
        )

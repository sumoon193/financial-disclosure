"""FD-11 合同入口：CitationAnchor.execute 的冻结集评测。"""

from __future__ import annotations

from ..contracts.errors import ErrorContract
from .errors import EvalError
from .types import FD11Input, FD11Result, FrozenEvalSet


class CitationAnchor:
    """数值、citation 与检索收益由冻结集验证的合同入口。"""

    def __init__(self, frozen: FrozenEvalSet) -> None:
        self._frozen = frozen

    def execute(self, input: FD11Input) -> FD11Result:
        if input.operation != "evaluate":
            return FD11Result(
                operation=input.operation,
                total=0,
                correct_numerical=0,
                correct_citation=0,
                correct_retrieval=0,
                numerical_accuracy=0.0,
                citation_accuracy=0.0,
                retrieval_gain=0.0,
                error=ErrorContract(
                    EvalError.INVALID_OPERATION, f"unknown operation: {input.operation}"
                ),
            )
        if not input.results or len(input.results) != len(self._frozen.cases):
            return FD11Result(
                operation=input.operation,
                total=len(self._frozen.cases),
                correct_numerical=0,
                correct_citation=0,
                correct_retrieval=0,
                numerical_accuracy=0.0,
                citation_accuracy=0.0,
                retrieval_gain=0.0,
                error=ErrorContract(
                    EvalError.INCOMPLETE, "results must cover every frozen case"
                ),
            )
        expected = {case.case_id: case for case in self._frozen.cases}
        for result in input.results:
            if result.case_id not in expected:
                return FD11Result(
                    operation=input.operation,
                    total=len(input.results),
                    correct_numerical=0,
                    correct_citation=0,
                    correct_retrieval=0,
                    numerical_accuracy=0.0,
                    citation_accuracy=0.0,
                    retrieval_gain=0.0,
                    error=ErrorContract(
                        EvalError.UNKNOWN_CASE, f"unknown case: {result.case_id}"
                    ),
                )
        total = len(input.results)
        correct_numerical = sum(
            1
            for r in input.results
            if r.value == expected[r.case_id].expected_value
        )
        correct_citation = sum(
            1
            for r in input.results
            if r.citation == expected[r.case_id].expected_citation
        )
        correct_retrieval = sum(
            1
            for r in input.results
            if r.retrieved and r.citation == expected[r.case_id].expected_citation
        )
        return FD11Result(
            operation=input.operation,
            total=total,
            correct_numerical=correct_numerical,
            correct_citation=correct_citation,
            correct_retrieval=correct_retrieval,
            numerical_accuracy=correct_numerical / total,
            citation_accuracy=correct_citation / total,
            retrieval_gain=correct_retrieval / total,
        )

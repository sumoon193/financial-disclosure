"""FD-07 OCR 准入错误码（错误载体复用 contracts.ErrorContract）。"""


class OCRAdmissionError:
    """固定错误码，API 层必须原样透出。"""

    INVALID_INPUT = "ocr.admission.input.invalid"
    INVALID_METRICS = "ocr.admission.metrics.invalid"

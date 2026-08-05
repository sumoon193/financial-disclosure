"""FD-05 模型 adapter 包。"""

from .adapter import (
    ModelAdapter,
    ModelProvider,
    ModelUnavailableError,
    RealModelAdapter,
)

__all__ = ["ModelAdapter", "ModelProvider", "ModelUnavailableError", "RealModelAdapter"]

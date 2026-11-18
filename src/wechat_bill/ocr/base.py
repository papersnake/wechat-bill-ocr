from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Union

from PIL import Image

from wechat_bill.models import TextBlock


class BaseOCR(ABC):
    """OCR 引擎抽象接口。"""

    @abstractmethod
    def recognize(self, image: Union[bytes, str, Image.Image]) -> list[TextBlock]:
        """识别图片，返回统一的 TextBlock 列表。"""
        ...

from __future__ import annotations

import io
from typing import Union

from loguru import logger
from PIL import Image

from wechat_bill.models import TextBlock
from wechat_bill.ocr.base import BaseOCR


class RapidOCREngine(BaseOCR):
    """基于 RapidOCR (ONNX) 的实现，中文效果好且轻量。"""

    def __init__(self):
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as e:
            raise ImportError(
                "请先安装 rapidocr-onnxruntime: pip install rapidocr-onnxruntime"
            ) from e

        self.engine = RapidOCR()
        logger.info("RapidOCR 引擎已加载")

    def recognize(self, image: Union[bytes, str, Image.Image]) -> list[TextBlock]:
        if isinstance(image, Image.Image):
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            image = buf.getvalue()

        result, _ = self.engine(image)
        if not result:
            return []

        blocks: list[TextBlock] = []
        for item in result:
            # RapidOCR 返回: [box, text, score]
            box, text, score = item[0], item[1], item[2]
            # box 是 4 个点
            blocks.append(
                TextBlock(
                    text=str(text).strip(),
                    box=[[float(p[0]), float(p[1])] for p in box],
                    score=float(score),
                )
            )
        return blocks

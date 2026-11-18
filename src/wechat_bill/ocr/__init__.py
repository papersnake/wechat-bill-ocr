from __future__ import annotations

from wechat_bill.config import OCRConfig
from wechat_bill.ocr.base import BaseOCR


def create_ocr_engine(cfg: OCRConfig) -> BaseOCR:
    engine = cfg.engine.lower()
    if engine == "rapid":
        from wechat_bill.ocr.rapid import RapidOCREngine

        return RapidOCREngine()
    if engine == "paddle":
        raise NotImplementedError("PaddleOCR 引擎暂未实现，请使用 rapid")
    if engine == "umi":
        raise NotImplementedError("Umi-OCR HTTP 接口暂未实现，请使用 rapid")
    raise ValueError(f"未知 OCR 引擎: {cfg.engine}")


__all__ = ["BaseOCR", "create_ocr_engine"]

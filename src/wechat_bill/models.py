from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TextBlock(BaseModel):
    """OCR 返回的单个文本块。"""

    text: str
    box: list[list[float]] = Field(default_factory=list)  # 四点坐标 [[x1,y1], ...]
    score: float = 0.0

    @property
    def center_x(self) -> float:
        if not self.box or len(self.box) < 4:
            return 0.0
        return sum(p[0] for p in self.box[:4]) / 4

    @property
    def center_y(self) -> float:
        if not self.box or len(self.box) < 4:
            return 0.0
        return sum(p[1] for p in self.box[:4]) / 4

    @property
    def height(self) -> float:
        if not self.box or len(self.box) < 4:
            return 0.0
        ys = [p[1] for p in self.box[:4]]
        return max(ys) - min(ys)

    @property
    def top(self) -> float:
        if not self.box:
            return 0.0
        return min(p[1] for p in self.box[:4])

    @property
    def bottom(self) -> float:
        if not self.box:
            return 0.0
        return max(p[1] for p in self.box[:4])


class BillRecord(BaseModel):
    """一条账单记录。"""

    desc: str = ""
    amount: float = 0.0  # 正数=收入，负数=支出
    time_str: str = ""  # 原始 OCR 时间文本
    dt: Optional[datetime] = None
    year_month: Optional[tuple[int, int]] = None
    source_screen: int = 0
    raw_desc: str = ""  # 未归一化的描述，方便调试

    def normalized_desc(self) -> str:
        import re

        return re.sub(r'[\s"\'“”‘’「」『』《》·。]', "", self.desc)


class ScreenResult(BaseModel):
    screen_idx: int
    records: list[BillRecord] = Field(default_factory=list)
    year_month: Optional[tuple[int, int]] = None


class Summary(BaseModel):
    total: int = 0
    income_count: int = 0
    total_income: float = 0.0
    expense_count: int = 0
    total_expense: float = 0.0
    net: float = 0.0
    top_expenses: list[dict] = Field(default_factory=list)

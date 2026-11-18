from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, Tuple

AMOUNT_RE = re.compile(r"^[+-]?\d{1,7}(?:,\d{3})*\.\d{2}$")
TIME_RE = re.compile(r"(\d{1,2}月\d{1,2}日)\s*(\d{1,2}:\d{2})")
MONTH_TITLE_RE = re.compile(r"(\d{4})年(\d{1,2})月")


def is_amount(text: str) -> bool:
    return bool(AMOUNT_RE.match(text.replace(",", "").strip()))


def is_time(text: str) -> bool:
    return bool(TIME_RE.search(text))


def parse_month_title(text: str) -> Tuple[Optional[int], Optional[int]]:
    m = MONTH_TITLE_RE.search(text)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def normalize_desc(text: str) -> str:
    return re.sub(r'[\s"\'“”‘’「」『』《》·。]', "", text)


def parse_time(text: str, year: Optional[int], month: Optional[int]) -> Optional[datetime]:
    m = TIME_RE.search(text)
    if not m or not year or not month:
        return None
    date_part = m.group(1)
    time_part = m.group(2)
    try:
        return datetime.strptime(f"{year}年{date_part}{time_part}", "%Y年%m月%d日%H:%M")
    except ValueError:
        return None


def resolve_year(ref_year: Optional[int], ref_month: Optional[int], time_text: str) -> Optional[int]:
    """根据参考年月和条目自身月份，推断最可能的年份（处理跨年）。"""
    if not ref_year or not ref_month:
        return ref_year
    m = TIME_RE.search(time_text)
    if not m:
        return ref_year
    item_month = int(m.group(1).split("月")[0])
    candidates = (ref_year - 1, ref_year, ref_year + 1)
    return min(candidates, key=lambda y: abs((y * 12 + item_month) - (ref_year * 12 + ref_month)))

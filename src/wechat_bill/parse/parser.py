from __future__ import annotations

import re
from typing import List, Optional, Tuple

from loguru import logger

from wechat_bill.config import ParseConfig
from wechat_bill.models import BillRecord, TextBlock
from wechat_bill.parse.rules import (
    MONTH_TITLE_RE,
    is_amount,
    is_time,
    normalize_desc,
    parse_month_title,
    parse_time,
    resolve_year,
)


def _is_search_box(text: str) -> bool:
    """顶部搜索框文案（"Q 查找交易"）。不能用 startswith("Q")，否则 QQ音乐、Q币 等商户会被误丢。"""
    return bool(re.match(r"^Q\s*查找", text)) or "查找交易" in text


def _is_month_title(text: str) -> bool:
    """月份标题（"2026年11月"，后面可能跟一个下拉箭头）。它不能被当成某一行的描述。"""
    t = text.strip()
    return bool(MONTH_TITLE_RE.match(t)) and len(t) <= 12


def parse_records(
    blocks: List[TextBlock],
    current_year_month: Optional[Tuple[int, int]] = None,
    view: Optional[Tuple[float, float]] = None,
    cfg: Optional[ParseConfig] = None,
    screen_idx: int = 0,
) -> Tuple[List[BillRecord], Optional[Tuple[int, int]]]:
    """从 OCR 文本块解析账单记录。

    view=(top, bottom) 时，整行未完整落在可视区内的记录会被丢弃。
    返回 (records, detected_year_month)
    """
    cfg = cfg or ParseConfig()
    records: List[BillRecord] = []
    detected = current_year_month

    # 过滤低置信度与固定 UI 文案
    filtered: List[TextBlock] = []
    skip_texts = {"X", "全部账单", "账单", "查找交易", "收支统计>", "收"}
    for b in blocks:
        if b.score < 0.3:
            continue
        t = b.text.strip()
        if t in skip_texts:
            continue
        if "支出¥" in t or "收入¥" in t:
            continue
        if _is_search_box(t):
            continue
        filtered.append(b)

    carry_over = current_year_month

    # 收集月份标题
    titles: List[Tuple[float, Tuple[int, int]]] = []
    for b in filtered:
        y, m = parse_month_title(b.text)
        if y and m:
            titles.append((b.center_y, (y, m)))
            logger.debug("[月份标题] {}年{}月", y, m)
    titles.sort(key=lambda x: x[0])
    if titles:
        detected = titles[-1][1]  # 本屏最靠下（最旧）的标题

    def month_for(y_pos: float) -> Tuple[Optional[int], Optional[int]]:
        above = [t for t in titles if t[0] < y_pos]
        if above:
            return above[-1][1]
        if titles:
            return titles[0][1]
        return carry_over or (None, None)

    amount_items = [b for b in filtered if is_amount(b.text)]
    other_items = [b for b in filtered if not is_amount(b.text) and not _is_month_title(b.text)]

    for amt in amount_items:
        amt_y = amt.center_y
        amt_x = amt.center_x
        raw_amt = amt.text.strip().replace(",", "")
        try:
            amount = float(raw_amt)
        except ValueError:
            continue

        desc_cands: List[TextBlock] = []
        time_cands: List[TextBlock] = []
        h = max(amt.height, 20)

        for o in other_items:
            if abs(o.center_y - amt_y) < max(h * 2.5, cfg.amount_y_tolerance):
                if o.center_x < amt_x - 50:
                    if is_time(o.text):
                        time_cands.append(o)
                    else:
                        desc_cands.append(o)

        desc = ""
        if desc_cands:
            desc_cands.sort(key=lambda x: abs(x.center_y - amt_y))
            desc = desc_cands[0].text

        time_str = ""
        dt = None
        e_year, e_month = month_for(amt_y)
        if time_cands:
            time_cands.sort(key=lambda x: abs(x.center_y - amt_y))
            time_str = time_cands[0].text
            resolved_year = resolve_year(e_year, e_month, time_str)
            dt = parse_time(time_str, resolved_year, e_month)

        # 贴边过滤
        if view:
            boxes = [amt.box]
            if desc_cands:
                boxes.append(desc_cands[0].box)
            if time_cands:
                boxes.append(time_cands[0].box)
            row_top = min(p[1] for b in boxes for p in b[:4])
            row_bottom = max(p[1] for b in boxes for p in b[:4])
            if row_top < view[0] or row_bottom > view[1]:
                logger.debug("[贴边丢弃] {} | {} | {}", desc, raw_amt, time_str)
                continue

        # 正负号规则
        if raw_amt.startswith("-"):
            amount = -abs(amount)
        elif raw_amt.startswith("+"):
            amount = abs(amount)
        elif desc and any(k in desc for k in cfg.income_keywords):
            amount = abs(amount)
        else:
            amount = -abs(amount)

        flags: List[str] = []
        if not desc:
            flags.append("missing_desc")
        if not time_str:
            flags.append("missing_time")

        records.append(
            BillRecord(
                desc=desc,
                amount=amount,
                time_str=time_str,
                dt=dt,
                year_month=(e_year, e_month) if e_year and e_month else None,
                source_screen=screen_idx,
                raw_desc=desc,
                flags=flags,
            )
        )

    return records, detected

from __future__ import annotations

from typing import List, Optional

from wechat_bill.models import BillRecord
from wechat_bill.parse.rules import TIME_RE, normalize_desc


def _when(r: BillRecord) -> tuple:
    """时间键：月日 + 时分，最稳定。"""
    m = TIME_RE.search(r.time_str)
    if m:
        return (m.group(1), m.group(2))
    return (normalize_desc(r.time_str),)


def same_record(a: BillRecord, b: BillRecord) -> bool:
    """同一条账单：时间精确到分钟 + 金额绝对值相同。"""
    return _when(a) == _when(b) and abs(abs(a.amount) - abs(b.amount)) < 0.005


def match_overlap(
    current: List[BillRecord], pool: List[BillRecord]
) -> List[Optional[BillRecord]]:
    """把本屏记录与已记录的 pool 配对。

    返回与 current 等长的列表：
    - 配上的元素是 pool 里的原记录
    - 没配上的是 None（新记录）
    每条 pool 记录最多被使用一次。
    先尝试描述也相同的，再放宽到仅时间+金额。
    """
    pairs: List[Optional[BillRecord]] = [None] * len(current)
    used: set[int] = set()

    for need_same_desc in (True, False):
        for i, r in enumerate(current):
            if pairs[i] is not None:
                continue
            for j, p in enumerate(pool):
                if j in used or not same_record(r, p):
                    continue
                if need_same_desc and r.normalized_desc() != p.normalized_desc():
                    continue
                pairs[i] = p
                used.add(j)
                break
    return pairs

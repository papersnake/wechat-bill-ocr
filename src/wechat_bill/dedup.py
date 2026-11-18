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
    """同一条账单：时间精确到分钟 + 金额绝对值相同。

    描述不参与判定：被屏幕边缘裁切的行，描述最容易被读少一个字或读成别的文字。
    任一方没读到时间时，退而要求两边都读到描述且相同。
    两边都既没有时间也没有描述的行（只剩一个金额），只能互相按金额配对：
    列表到底、页面不再滚动时同一屏会被反复截到，如果这类行永远配不上，
    每一屏都会被当成新记录，既无法判定"到底"，也会重复记录。
    它们本来就带警告标志要人工核对，宁可偶尔合并也不能无限重复。
    """
    if abs(abs(a.amount) - abs(b.amount)) >= 0.005:
        return False
    if a.time_str and b.time_str:
        return _when(a) == _when(b)
    if not (a.time_str or a.desc) and not (b.time_str or b.desc):
        return True
    return bool(a.desc and b.desc) and a.normalized_desc() == b.normalized_desc()


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

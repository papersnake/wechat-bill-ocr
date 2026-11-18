# -*- coding: utf-8 -*-
"""跨屏去重测试。"""
from wechat_bill.dedup import match_overlap, same_record
from wechat_bill.models import BillRecord


def make(desc: str, time_str: str, amount: float) -> BillRecord:
    return BillRecord(desc=desc, time_str=time_str, amount=amount)


def test_same_record_by_time_and_amount():
    a = make("兰州拉面", "11月3日20:57", -18.0)
    b = make("兰州拉", "11月3日20:57", -18.0)  # 描述被读残
    assert same_record(a, b)
    assert not same_record(a, make("美团", "11月3日20:57", -18.0))  # 时间相同但实际不同？金额同时间同会判同
    # 金额不同应判不同
    assert not same_record(a, make("兰州拉面", "11月3日20:57", -19.0))


def test_match_overlap_keeps_identical_same_minute():
    """同一分钟两笔相同金额的真实交易都应保留。"""
    r1 = make("智慧停车场", "11月1日07:36", -2.0)
    r2 = make("智慧停车场", "11月1日07:36", -2.0)
    cur = [r1, r2]
    pool = [r1]  # 上一屏只有一笔
    pairs = match_overlap(cur, pool)
    # 第一笔配上，第二笔是新的
    assert pairs[0] is not None
    assert pairs[1] is None


def test_degraded_desc_matched():
    prev = make("兰州拉面", "11月3日20:57", -18.0)
    cur = make("兰州拉", "11月3日20:57", -18.0)
    pairs = match_overlap([cur], [prev])
    assert pairs[0] is prev

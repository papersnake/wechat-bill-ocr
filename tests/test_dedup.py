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
    # 描述不参与判定（边缘行描述常被读坏）：时间和金额都相同就是同一条，哪怕描述完全不同
    assert same_record(a, make("美团", "11月3日20:57", -18.0))
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


def test_pool_with_same_object_twice_must_not_swallow_a_twin():
    """回归：一条记录连续出现在两屏时 recent 里是同一对象；池要按对象去重，
    否则紧接着出现的"同分钟同金额"的另一笔真实交易会被一并配掉。"""
    t = make("智慧停车场", "11月1日07:36", -2.0)
    pool = list({id(p): p for p in [t, t]}.values())
    cur = [make("智慧停车场", "11月1日07:36", -2.0), make("智慧停车场", "11月1日07:36", -2.0)]
    pairs = match_overlap(cur, pool)
    assert pairs[0] is t and pairs[1] is None


def test_rows_without_time_are_not_merged_with_complete_rows_by_amount_alone():
    """没读到时间的行，不能仅凭金额与一条完整记录配对（两笔金额相同的不同交易会被悄悄合并）"""
    full = make("美团外卖", "11月2日12:00", -9.99)
    assert not same_record(full, make("", "", -9.99))
    assert not same_record(make("", "", -9.99), full)


def test_rows_with_only_an_amount_pair_with_each_other():
    """只剩金额的行只能互相按金额配对：页面到底后同一屏被反复截到，必须能判定为"没有新记录"，否则永不停止"""
    a, b = make("", "", -9.99), make("", "", -9.99)
    assert same_record(a, b)
    assert match_overlap([b], [a]) == [a]
    assert not same_record(a, make("", "", -8.88))


def test_rows_without_time_match_only_when_descriptions_agree():
    a = make("美团外卖", "11月2日12:00", -25.5)
    assert same_record(a, make("美团外卖", "", -25.5))
    assert not same_record(a, make("兰州拉面", "", -25.5))
    assert not same_record(a, make("", "", -25.5))

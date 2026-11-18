# -*- coding: utf-8 -*-
"""解析基础规则测试。"""
from wechat_bill.config import ParseConfig
from wechat_bill.models import TextBlock
from wechat_bill.parse import parse_records
from wechat_bill.parse.rules import is_amount, is_time, parse_month_title, resolve_year


def test_is_amount():
    assert is_amount("-18.00")
    assert is_amount("+25.50")
    assert is_amount("3.00")
    assert not is_amount("18")
    assert not is_amount("美团外卖")


def test_is_time():
    assert is_time("11月3日20:57")
    assert is_time("1月1日 09:00")
    assert not is_time("11月3日")


def test_parse_month_title():
    assert parse_month_title("2026年11月") == (2026, 11)
    assert parse_month_title("随便") == (None, None)


def test_resolve_year_cross_year():
    # 参考是 2026年12月，条目是 1月 → 应为 2027
    assert resolve_year(2026, 12, "1月3日20:51") == 2027
    # 参考是 2027年1月，条目是 12月 → 应为 2026
    assert resolve_year(2027, 1, "12月30日12:00") == 2026


# ---- 回归：解析鲁棒性 -------------------------------------------------------
VIEW = (492, 2712)


def _b(text, x0, y0, x1, y1, score=0.98):
    return TextBlock(text=text, box=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]], score=score)


def _row(y, desc, time, amount):
    """一行：描述与金额同高，时间在其下方。desc/time 传 None 表示这一块没读到。"""
    out = [_b(amount, 1050, y + 4, 1220, y + 67)]
    if desc is not None:
        out.append(_b(desc, 245, y, 740, y + 66))
    if time is not None:
        out.append(_b(time, 251, y + 80, 552, y + 131))
    return out


def test_merchant_starting_with_q_is_kept():
    blocks = [_b("2026年11月", 43, 560, 392, 620)] + _row(700, "QQ音乐会员", "11月3日20:57", "-15.00")
    (r,), _ = parse_records(blocks, view=VIEW, cfg=ParseConfig())
    assert r.desc == "QQ音乐会员" and r.amount == -15.0 and not r.flags


def test_search_box_text_is_still_filtered():
    blocks = [_b("Q 查找交易", 100, 300, 500, 360), _b("2026年11月", 43, 560, 392, 620)] \
        + _row(700, "美团外卖", "11月3日20:57", "-25.50")
    (r,), _ = parse_records(blocks, view=VIEW, cfg=ParseConfig())
    assert r.desc == "美团外卖"


def test_month_title_is_never_used_as_description():
    """描述没读到时，离得最近的块是月份标题；以前会把 "2026年11月" 当成描述"""
    blocks = [_b("2026年11月", 43, 560, 392, 620)] + _row(700, None, "11月3日20:57", "-15.00")
    (r,), _ = parse_records(blocks, view=VIEW, cfg=ParseConfig())
    assert r.desc == "" and "missing_desc" in r.flags


def test_row_missing_description_or_time_is_kept_and_flagged():
    blocks = ([_b("2026年11月", 43, 560, 392, 620)]
              + _row(700, "美团外卖", None, "-25.50")
              + _row(953, None, None, "-9.99"))
    records, _ = parse_records(blocks, view=VIEW, cfg=ParseConfig())
    assert [(r.amount, r.flags) for r in records] == [
        (-25.5, ["missing_time"]),
        (-9.99, ["missing_desc", "missing_time"]),
    ]

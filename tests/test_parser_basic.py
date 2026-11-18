# -*- coding: utf-8 -*-
"""解析基础规则测试。"""
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

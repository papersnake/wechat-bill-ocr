# -*- coding: utf-8 -*-
"""日期范围计算测试。"""
from datetime import date

import pytest
from typer.testing import CliRunner

from wechat_bill.cli import resolve_date_range

TODAY = date(2026, 11, 16)


def test_today_is_single_day():
    assert resolve_date_range(today=True, base=TODAY) == (TODAY, TODAY)


def test_days_includes_today():
    assert resolve_date_range(days=1, base=TODAY) == (TODAY, TODAY)
    assert resolve_date_range(days=7, base=TODAY) == (date(2026, 11, 10), TODAY)


def test_days_crosses_month_and_year():
    assert resolve_date_range(days=20, base=TODAY) == (date(2026, 10, 28), TODAY)
    assert resolve_date_range(days=3, base=date(2027, 1, 1)) == (
        date(2026, 12, 30),
        date(2027, 1, 1),
    )


def test_months():
    assert resolve_date_range(months=2, base=TODAY) == (date(2026, 10, 1), TODAY)
    assert resolve_date_range(months=12, base=TODAY) == (date(2025, 12, 1), TODAY)


def test_explicit_dates():
    assert resolve_date_range(start_date="2024-01-01", end_date="2024-12-31", base=TODAY) == (
        date(2024, 1, 1),
        date(2024, 12, 31),
    )
    assert resolve_date_range(base=TODAY) == (None, None)


def test_conflicting_options_rejected():
    with pytest.raises(Exception):
        resolve_date_range(today=True, months=2, base=TODAY)
    with pytest.raises(Exception):
        resolve_date_range(days=0, base=TODAY)

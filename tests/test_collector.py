# -*- coding: utf-8 -*-
"""收集循环回归测试：用假设备 + 假 OCR，不需要真机和 OCR 引擎。"""
import pytest
from PIL import Image

from wechat_bill import collector
from wechat_bill.collector import MAX_EMPTY_STREAK, collect_bills
from wechat_bill.config import Settings
from wechat_bill.models import TextBlock


def blk(text, x0, y0, x1, y1, score=0.98):
    return TextBlock(text=text, box=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]], score=score)


def title(ym="2026年11月"):
    return [blk(ym, 43, 560, 392, 620)]


def row(y, desc, time, amount):
    """一行：描述与金额同高，时间在其下方。desc/time 传 None 表示这一块没读到。"""
    out = [blk(amount, 1050, y + 4, 1220, y + 67)]
    if desc is not None:
        out.append(blk(desc, 245, y, 740, y + 66))
    if time is not None:
        out.append(blk(time, 251, y + 80, 552, y + 131))
    return out


class FakeDevice:
    """swipe_up 一次，"页面位置"前进一屏；超出脚本后停在最后一屏（相当于列表到底、页面不再滚动）。"""

    def __init__(self):
        self.pos = 0
        self.swipes = 0

    def screenshot(self):
        return Image.new("RGB", (1264, 2736), "white")

    def swipe_up(self, screen_height=None, duration_ms=350):
        self.pos += 1
        self.swipes += 1


class FakeOCR:
    def __init__(self, device, screens):
        self.device, self.screens = device, screens

    def recognize(self, image):
        return self.screens[min(self.device.pos, len(self.screens) - 1)]


@pytest.fixture
def run(monkeypatch):
    monkeypatch.setattr(collector.time, "sleep", lambda s: None)

    def _run(screens, max_scrolls=30):
        settings = Settings()
        settings.collect.wait_after_scroll = 0
        dev = FakeDevice()
        records = collect_bills(settings, device=dev, ocr=FakeOCR(dev, screens), max_scrolls=max_scrolls)
        return records, dev

    return _run


def test_identical_twin_transactions_survive_three_screen_overlap(run):
    """回归：同一笔交易出现在连续三屏时，紧接着的"同分钟同金额"的另一笔真实交易不能被吞掉"""
    T = ("智慧停车场", "11月1日07:36", "-2.00")
    screens = [
        title() + row(1700, *T),                      # 第 1 屏：T
        row(700, *T),                                  # 第 2 屏：T 还在
        row(700, *T) + row(953, *T),                   # 第 3 屏：T 和真实的第二笔 T'
    ]
    records, _ = run(screens)
    assert [(r.desc, r.amount) for r in records] == [("智慧停车场", -2.0)] * 2


def test_empty_ocr_screen_does_not_stall_scrolling(run):
    """回归：OCR 返回空时必须继续滚动；以前 continue 跳过了滑动，对同一屏反复截图直到用完 max_scrolls"""
    screens = [[], title() + row(700, "美团外卖", "11月3日20:57", "-25.50")]
    records, dev = run(screens)
    assert [(r.desc, r.amount) for r in records] == [("美团外卖", -25.5)]
    assert dev.swipes < 10                             # 正常结束，没有空转到 max_scrolls


def test_persistently_empty_ocr_stops_early(run):
    records, dev = run([[]], max_scrolls=50)
    assert records == []
    assert dev.swipes == MAX_EMPTY_STREAK - 1          # 连续 MAX_EMPTY_STREAK 屏为空即停止，最后一次不再滑动


def test_rows_missing_description_or_time_are_kept_and_flagged(run):
    screens = [title() + row(700, "美团外卖", "11月3日20:57", "-25.50") + row(953, None, None, "-9.99")]
    records, _ = run(screens)
    assert [(r.amount, r.flags) for r in records] == [
        (-25.5, []),
        (-9.99, ["missing_desc", "missing_time"]),
    ]


def test_flagged_rows_do_not_repeat_forever_at_end_of_list(run):
    """列表到底后同一屏被反复截到：只剩金额的行也必须能配上，让"无新记录"判定生效，而不是重复到 max_scrolls"""
    screens = [title() + row(700, None, None, "-9.99")]
    records, dev = run(screens, max_scrolls=30)
    assert len(records) == 1
    assert dev.swipes < 10

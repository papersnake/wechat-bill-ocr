from __future__ import annotations

import time
from collections import deque
from datetime import date, datetime
from pathlib import Path
from typing import Deque, List, Optional, Tuple

from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from wechat_bill.config import Settings
from wechat_bill.dedup import match_overlap
from wechat_bill.device import DeviceController
from wechat_bill.models import BillRecord
from wechat_bill.ocr import create_ocr_engine
from wechat_bill.ocr.base import BaseOCR
from wechat_bill.parse import parse_records

console = Console()

# OCR 连续这么多屏都没有识别到任何内容就停止（避免对着一个空白/错误页面一直滚动）
MAX_EMPTY_STREAK = 3


def collect_bills(
    settings: Settings,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    device: Optional[DeviceController] = None,
    max_scrolls: Optional[int] = None,
    ocr: Optional[BaseOCR] = None,
) -> List[BillRecord]:
    """主收集循环。支持 Ctrl+C 中断并保留已抓数据。"""
    cfg = settings.collect
    parse_cfg = settings.parse
    max_scrolls = max_scrolls or cfg.max_scrolls

    if device is None:
        device = DeviceController(
            serial=settings.device.serial or None,
            host=settings.device.adb_host,
            port=settings.device.adb_port,
        )

    ocr = ocr or create_ocr_engine(settings.ocr)
    all_records: List[BillRecord] = []
    recent: Deque[List[BillRecord]] = deque(maxlen=2)
    no_new_count = 0
    empty_streak = 0
    current_ym: Optional[Tuple[int, int]] = None

    output_dir = Path(settings.output.dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print("[bold green]开始抓取微信账单...[/]")
    console.print("请确保账单页面已滚动到最顶部，手机保持亮屏。")
    if start_date:
        console.print(f"开始日期: {start_date}")
    if end_date:
        console.print(f"结束日期: {end_date}")
    time.sleep(1.5)

    try:
        for i in range(max_scrolls):
            console.print(f"\n[cyan]--- 第 {i + 1} 屏 ---[/]")

            img = device.screenshot()
            w, h = img.size

            if settings.output.save_screenshots:
                img.save(output_dir / f"screen_{i+1:03d}.png")

            blocks = ocr.recognize(img)
            if not blocks:
                # 空结果也必须继续滚动：不滚动会对同一屏反复截图/OCR，直到用完 max_scrolls
                empty_streak += 1
                logger.warning("OCR 未识别到内容（连续 {} 屏）", empty_streak)
                if empty_streak >= MAX_EMPTY_STREAK:
                    console.print(
                        "[red]OCR 连续多屏没有识别到内容，停止。"
                        "请检查是否停在账单页、OCR 是否正常[/]"
                    )
                    break
                device.swipe_up(screen_height=h, duration_ms=cfg.scroll_duration_ms)
                time.sleep(cfg.wait_after_scroll)
                continue
            empty_streak = 0

            view = (h * parse_cfg.list_top_ratio, h - parse_cfg.edge_bottom_px)
            records, current_ym = parse_records(
                blocks,
                current_year_month=current_ym,
                view=view,
                cfg=parse_cfg,
                screen_idx=i + 1,
            )

            screen_records: List[BillRecord] = []
            early_stop = False

            for r in records:
                if r.dt:
                    r_date = r.dt.date()
                    if start_date and r_date < start_date:
                        console.print(
                            f"  [yellow][超出开始日期] {r.desc} {r.time_str}，停止[/]"
                        )
                        early_stop = True
                        continue
                    if end_date and r_date > end_date:
                        continue

                # 描述或时间没读到的行也保留（parser 已打 flags），交给人工核对；
                # 直接丢弃会让这笔金额在对账时凭空消失。
                screen_records.append(r)

            # 去重
            # 一条记录连续出现在两屏时，recent 里是同一个对象；按对象去重，
            # 否则池里有两份，会把紧接着出现的"同分钟同金额"的另一笔真实交易也配掉。
            pool = list({id(p): p for prev in recent for p in prev}.values())
            pairs = match_overlap(screen_records, pool)

            if pool and screen_records and all(p is None for p in pairs):
                console.print(
                    "  [yellow][警告] 本屏与前两屏没有任何重叠，滚动距离可能过大[/]"
                )

            new_count = 0
            kept: List[BillRecord] = []
            for r, matched in zip(screen_records, pairs):
                if matched is None:
                    all_records.append(r)
                    kept.append(r)
                    new_count += 1
                    sign = "+" if r.amount > 0 else ""
                    console.print(
                        f"  [green]+[/] {r.desc} | {sign}{r.amount:.2f} | {r.time_str}"
                    )
                else:
                    kept.append(matched)

            if kept:
                recent.append(kept)

            console.print(f"本屏新增 {new_count} 条，累计 {len(all_records)} 条")

            if early_stop:
                console.print("[yellow]已超出指定日期范围，停止[/]")
                break

            # 月份提前停止
            if start_date and current_ym:
                cy, cm = current_ym
                if date(cy, cm, 1) < date(start_date.year, start_date.month, 1):
                    console.print("[yellow]当前月份已早于开始日期范围，停止[/]")
                    break

            if new_count == 0:
                no_new_count += 1
                if no_new_count >= cfg.no_new_threshold:
                    console.print("[green]连续多屏无新记录，已到达底部[/]")
                    break
            else:
                no_new_count = 0

            device.swipe_up(screen_height=h, duration_ms=cfg.scroll_duration_ms)
            time.sleep(cfg.wait_after_scroll)

    except KeyboardInterrupt:
        console.print("\n[yellow]用户中断，保留已抓取的数据...[/]")

    flagged = [r for r in all_records if r.flags]
    if flagged:
        console.print(
            f"[yellow]注意：{len(flagged)} 条记录的描述或时间没有识别成功，已保留并标记"
            "（见输出的「警告」列），请人工核对。这类记录无法可靠去重，"
            "可能在相邻两屏里重复出现。[/]"
        )

    return all_records

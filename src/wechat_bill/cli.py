from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from wechat_bill import __version__
from wechat_bill.collector import collect_bills
from wechat_bill.config import Settings
from wechat_bill.export import save_results, summarize

app = typer.Typer(
    name="wechat-bill",
    help="自动抓取微信账单并导出统计结果",
    add_completion=False,
)
console = Console()


def resolve_date_range(
    today: bool = False,
    days: Optional[int] = None,
    months: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    base: Optional[date] = None,
) -> tuple[Optional[date], Optional[date]]:
    base = base or date.today()
    kinds = [
        bool(today or days is not None),
        bool(months),
        bool(start_date or end_date),
    ]
    if sum(kinds) > 1:
        raise typer.BadParameter(
            "--today/--days、--months、--start-date/--end-date 只能选一种"
        )

    if today or days is not None:
        n = 1 if today else days  # type: ignore
        if n < 1:
            raise typer.BadParameter("--days 必须是 1 以上的整数")
        return base - timedelta(days=n - 1), base

    if months:
        month = base.month - (months - 1)
        year = base.year
        while month <= 0:
            month += 12
            year -= 1
        return date(year, month, 1), base

    def parse(s: Optional[str]) -> Optional[date]:
        if not s:
            return None
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        raise typer.BadParameter(f"无法解析日期: {s}")

    return parse(start_date), parse(end_date)


@app.command()
def run(
    months: Optional[int] = typer.Option(None, "--months", "-m", help="统计最近 N 个月"),
    days: Optional[int] = typer.Option(None, "--days", "-d", help="统计最近 N 天（含今天）"),
    today: bool = typer.Option(False, "--today", help="只统计今天"),
    start_date: Optional[str] = typer.Option(None, "--start-date", help="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = typer.Option(None, "--end-date", help="结束日期 YYYY-MM-DD"),
    device: Optional[str] = typer.Option(None, "--device", help="指定 adb 设备序列号"),
    max_scrolls: Optional[int] = typer.Option(None, "--max-scrolls", help="最大滚动次数"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
    save_screenshots: bool = typer.Option(False, "--save-screenshots", help="保存每屏截图"),
):
    """抓取微信账单并导出 CSV/JSON。"""
    settings = Settings.load(config)
    if device:
        settings.device.serial = device
    if save_screenshots:
        settings.output.save_screenshots = True

    try:
        start, end = resolve_date_range(
            today=today, days=days, months=months, start_date=start_date, end_date=end_date
        )
    except typer.BadParameter as e:
        console.print(f"[red]参数错误：{e}[/]")
        raise typer.Exit(1)

    if today or days is not None:
        console.print(f"统计 {start} 至 {end}")
    elif months:
        console.print(f"统计最近 {months} 个月：{start} 至 {end}")

    records = collect_bills(
        settings,
        start_date=start,
        end_date=end,
        max_scrolls=max_scrolls,
    )

    if not records:
        console.print("[yellow]未抓取到任何记录，请检查页面是否已打开到账单顶部[/]")
        raise typer.Exit(1)

    summary = summarize(records)
    save_results(records, summary, settings.output.dir)


@app.command("version")
def version_cmd():
    """显示版本。"""
    console.print(f"wechat-bill-ocr {__version__}")


@app.callback()
def main():
    """wechat-bill-ocr — 自动抓取微信账单工具"""
    pass


if __name__ == "__main__":
    app()

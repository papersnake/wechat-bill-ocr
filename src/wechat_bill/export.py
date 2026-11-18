from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List

from loguru import logger
from rich.console import Console
from rich.table import Table

from wechat_bill.models import BillRecord, Summary

console = Console()

FLAG_TEXT = {"missing_desc": "缺描述", "missing_time": "缺时间"}


def summarize(records: List[BillRecord]) -> Summary:
    income = [r for r in records if r.amount > 0]
    expense = [r for r in records if r.amount < 0]

    total_income = sum(r.amount for r in income)
    total_expense = sum(r.amount for r in expense)

    desc_summary: dict[str, dict] = defaultdict(lambda: {"count": 0, "amount": 0.0})
    for r in expense:
        key = r.desc or "(未知)"
        desc_summary[key]["count"] += 1
        desc_summary[key]["amount"] += r.amount

    top = sorted(desc_summary.items(), key=lambda x: x[1]["amount"])[:20]
    top_expenses = [
        {"desc": k, "count": v["count"], "amount": round(v["amount"], 2)} for k, v in top
    ]

    summary = Summary(
        total=len(records),
        income_count=len(income),
        total_income=round(total_income, 2),
        expense_count=len(expense),
        total_expense=round(total_expense, 2),
        net=round(total_income + total_expense, 2),
        top_expenses=top_expenses,
    )

    # 漂亮打印
    console.print("\n[bold]========== 账单统计结果 ==========[/]")
    console.print(f"总记录数：{summary.total}")
    console.print(f"收入：{summary.income_count} 笔，共 {summary.total_income:+.2f}")
    console.print(f"支出：{summary.expense_count} 笔，共 {summary.total_expense:+.2f}")
    console.print(f"净额：{summary.net:+.2f}")

    if top_expenses:
        table = Table(title="支出 TOP")
        table.add_column("描述", style="cyan")
        table.add_column("笔数", justify="right")
        table.add_column("金额", justify="right", style="red")
        for item in top_expenses:
            table.add_row(item["desc"], str(item["count"]), f"{item['amount']:.2f}")
        console.print(table)

    return summary


def save_results(
    records: List[BillRecord],
    summary: Summary,
    output_dir: str | Path = "output",
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = output_dir / f"wechat_bills_{ts}.json"
    csv_path = output_dir / f"wechat_bills_{ts}.csv"

    # JSON
    data = {
        "records": [
            {
                "desc": r.desc,
                "amount": r.amount,
                "time": r.time_str,
                "datetime": r.dt.isoformat() if r.dt else None,
                "year_month": r.year_month,
                "source_screen": r.source_screen,
                "flags": r.flags,
            }
            for r in records
        ],
        "summary": summary.model_dump(),
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # CSV（带 BOM，Excel 友好）
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["描述", "金额", "时间", "完整时间", "警告"])
        for r in records:
            writer.writerow(
                [
                    r.desc,
                    f"{r.amount:.2f}",
                    r.time_str,
                    r.dt.isoformat(sep=" ") if r.dt else "",
                    "；".join(FLAG_TEXT.get(f, f) for f in r.flags),
                ]
            )

    console.print(f"\n[green]结果已保存：[/]\n  {json_path}\n  {csv_path}")
    return json_path, csv_path

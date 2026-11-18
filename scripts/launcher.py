# -*- coding: utf-8 -*-
"""交互式启动菜单，避免 bat 中文编码问题。"""
from __future__ import annotations

import subprocess
import sys


def run_cmd(args: list[str]) -> int:
    print()
    return subprocess.call([sys.executable, "-m", "wechat_bill", *args])


def main() -> None:
    while True:
        print()
        print("----------------------------------------")
        print("  请选择操作:")
        print()
        print("  1. 一键统计（最近 N 个月）")
        print("  2. 只统计今天")
        print("  3. 统计最近 7 天")
        print("  4. 自定义日期范围")
        print("  5. 仅检查设备连接")
        print("  0. 退出")
        print("----------------------------------------")
        choice = input("请输入选项 (0-5): ").strip()

        if choice == "1":
            months = input("请输入要统计的月数（直接回车默认 2）: ").strip() or "2"
            print()
            print("请确认：")
            print("  1. 手机已通过 adb 连接")
            print("  2. 微信已打开到「我 → 服务 → 钱包 → 账单」并滚动到最顶部")
            print("  3. 手机保持亮屏")
            input("准备好后按回车开始...")
            run_cmd(["--months", months])

        elif choice == "2":
            print()
            print("请确认手机已打开账单页并滚动到顶部，保持亮屏。")
            input("准备好后按回车开始...")
            run_cmd(["--today"])

        elif choice == "3":
            run_cmd(["--days", "7"])

        elif choice == "4":
            start = input("开始日期 (YYYY-MM-DD): ").strip()
            end = input("结束日期 (YYYY-MM-DD): ").strip()
            print()
            print("请确认手机已打开账单页并滚动到顶部，保持亮屏。")
            input("准备好后按回车开始...")
            run_cmd(["--start-date", start, "--end-date", end])

        elif choice == "5":
            print()
            print("当前 adb 设备列表:")
            subprocess.call(["adb", "devices", "-l"])
            input("\n按回车返回菜单...")
            continue

        elif choice == "0":
            print("\n再见！")
            break

        else:
            print("无效选项，请重新选择。")
            continue

        print()
        print("----------------------------------------")
        print("运行结束。结果保存在 output 文件夹中。")
        print("----------------------------------------")
        again = input("是否返回主菜单继续？(Y/N，默认 N): ").strip().lower()
        if again != "y":
            print("\n再见！")
            break


if __name__ == "__main__":
    main()

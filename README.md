# wechat-bill-ocr

自动从 Android 手机微信账单页抓取交易记录（ADB 截图 + 本地 OCR），解析、跨屏去重、按日期过滤，并导出 CSV / JSON 统计结果。

> 模块化重写版本，解决了原项目硬编码路径、单文件、布局阈值写死等问题。

## 功能特点

- 📱 **ADB 无线 / USB 控制**（基于 [adbutils](https://github.com/openatx/adbutils)）
- 🖼️ **本地 OCR**（默认 RapidOCR，中文效果好、体积小）
- 🔄 **自动滚动 + 跨屏去重**（时间+金额优先，描述辅助）
- ⏱️ **灵活日期范围**（`--months` / `--days` / `--today` / 指定起止）
- 🛑 **Ctrl+C 安全中断**，已抓数据会保存
- 📊 **CSV（Excel 友好）+ JSON 详细结果**
- ⚙️ **配置驱动**（`config.toml`），无硬编码路径

## 环境要求

- Python 3.11+
- Android 手机（开启开发者选项 + USB/无线调试）
- 电脑与手机同一网络（无线调试时）

## 快速安装

```bash
# 推荐使用 uv
uv venv
uv pip install -e .

# 或传统方式
pip install -e .
```

首次运行 RapidOCR 会自动下载模型。

## 使用方法

1. 连接手机：

```bash
# 无线调试示例
adb pair <IP>:<配对端口> <配对码>
adb connect <IP>:<调试端口>
adb devices
```

2. 打开微信 → 我 → 服务 → 钱包 → 账单，**滚动到最顶部**，保持亮屏。

3. 运行：

```bash
# 最近 2 个月
wechat-bill --months 2

# 今天
wechat-bill --today

# 最近 7 天
wechat-bill --days 7

# 指定日期范围
wechat-bill --start-date 2026-01-01 --end-date 2026-06-30

# 指定设备
wechat-bill --device 192.168.1.5:5555 --months 2

# 保存每屏截图（调试用）
wechat-bill --months 1 --save-screenshots
```

也可以直接：

```bash
python -m wechat_bill.cli --months 2
```

## 配置

复制 `config.example.toml` 为 `config.toml`，按需修改：

```toml
[device]
serial = ""                # 留空自动选择

[ocr]
engine = "rapid"

[parse]
list_top_ratio = 0.18
income_keywords = ["退款", "收款", "入账", "红包", "工资", "来自"]

[collect]
max_scrolls = 100
wait_after_scroll = 1.2

[output]
dir = "output"
save_screenshots = false
```

## 输出

运行结束后在 `output/` 目录生成：

- `wechat_bills_YYYYMMDD_HHMMSS.csv` — Excel 可直接打开
- `wechat_bills_YYYYMMDD_HHMMSS.json` — 完整记录 + 汇总

## 项目结构

```
src/wechat_bill/
├── cli.py           # Typer 命令行入口
├── config.py        # 配置加载
├── models.py        # 数据模型
├── collector.py     # 主收集循环
├── dedup.py         # 跨屏去重
├── export.py        # 汇总与导出
├── device/          # ADB 控制
├── ocr/             # OCR 引擎抽象与实现
└── parse/           # 账单解析规则
```

## 测试

```bash
pip install -e ".[dev]"
pytest
```

## 注意事项

- 微信账单页做了 Accessibility 保护，因此采用截图 + OCR 方案。
- OCR 准确率受屏幕清晰度、滚动位置影响，建议人工抽查结果。
- 不同手机分辨率 / 微信版本可能需要微调 `config.toml` 中的 `list_top_ratio` 等参数。

## License

MIT

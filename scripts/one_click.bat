@echo off
chcp 65001 >nul
setlocal

echo ========================================
echo   wechat-bill-ocr 一键启动
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.11+
    pause
    exit /b 1
)

echo [1] 检查依赖...
pip show wechat-bill-ocr >nul 2>&1
if errorlevel 1 (
    echo 正在安装项目...
    pip install -e .
)

echo.
echo [2] 请确认：
echo   - 手机已通过 adb 连接（adb devices 能看到设备）
echo   - 微信账单页面已打开并滚动到最顶部
echo   - 手机保持亮屏
echo.

set /p months="请输入要统计的月数（直接回车默认 2）: "
if "%months%"=="" set months=2

echo.
echo 开始抓取最近 %months% 个月的账单...
echo.

wechat-bill --months %months%

echo.
pause

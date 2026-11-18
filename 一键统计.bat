@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

title wechat-bill-ocr 一键统计

echo.
echo  ========================================
echo    微信账单自动统计  wechat-bill-ocr
echo  ========================================
echo.

:: ---------- 检查 Python ----------
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python。
    echo 请先安装 Python 3.11 或更高版本，并勾选 "Add to PATH"。
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [OK] %PYVER%

:: ---------- 检查 / 安装本项目 ----------
echo.
echo 正在检查项目是否已安装...
pip show wechat-bill-ocr >nul 2>&1
if errorlevel 1 (
    echo 首次运行，正在安装依赖（可能需要几分钟）...
    pip install -e . -q
    if errorlevel 1 (
        echo [错误] 安装失败，请手动执行: pip install -e .
        pause
        exit /b 1
    )
    echo [OK] 安装完成
) else (
    echo [OK] 项目已安装
)

:: ---------- 检查 adb ----------
echo.
echo 正在检查 adb 设备...
adb devices >nul 2>&1
if errorlevel 1 (
    echo [提示] 系统 PATH 中未找到 adb。
    echo 请确保已安装 Android Platform-Tools，或把 adb.exe 所在目录加入 PATH。
    echo 也可以把 platform-tools 解压到本项目目录下。
    echo.
) else (
    echo 当前已连接设备:
    adb devices -l
)

:: ---------- 主菜单 ----------
:menu
echo.
echo  ----------------------------------------
echo   请选择操作:
echo.
echo   1. 一键统计（最近 N 个月）
echo   2. 只统计今天
echo   3. 统计最近 7 天
echo   4. 自定义日期范围
echo   5. 仅检查设备连接
echo   0. 退出
echo  ----------------------------------------
echo.
set /p choice=请输入选项 (0-5): 

if "%choice%"=="1" goto do_months
if "%choice%"=="2" goto do_today
if "%choice%"=="3" goto do_days
if "%choice%"=="4" goto do_range
if "%choice%"=="5" goto do_check
if "%choice%"=="0" goto end
echo 无效选项，请重新选择。
goto menu

:do_months
echo.
set /p months=请输入要统计的月数（直接回车默认 2）: 
if "%months%"=="" set months=2
echo.
echo 请确认：
echo   1. 手机已通过 adb 连接
echo   2. 微信已打开到「我 → 服务 → 钱包 → 账单」并滚动到最顶部
echo   3. 手机保持亮屏
echo.
pause
echo.
echo 开始抓取最近 %months% 个月的账单...
echo.
wechat-bill --months %months%
goto after_run

:do_today
echo.
echo 请确认手机已打开账单页并滚动到顶部，保持亮屏。
pause
echo.
wechat-bill --today
goto after_run

:do_days
echo.
wechat-bill --days 7
goto after_run

:do_range
echo.
set /p start=开始日期 (YYYY-MM-DD): 
set /p end=结束日期 (YYYY-MM-DD): 
echo.
echo 请确认手机已打开账单页并滚动到顶部，保持亮屏。
pause
echo.
wechat-bill --start-date %start% --end-date %end%
goto after_run

:do_check
echo.
echo 当前 adb 设备列表:
adb devices -l
echo.
pause
goto menu

:after_run
echo.
echo ----------------------------------------
echo 运行结束。结果保存在 output 文件夹中。
echo ----------------------------------------
echo.
set /p again=是否返回主菜单继续？(Y/N，默认 N): 
if /i "%again%"=="Y" goto menu

:end
echo.
echo 再见！
timeout /t 2 >nul
endlocal

@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

title wechat-bill-ocr 一键统计

:: 切换到脚本所在目录（项目根目录）
cd /d "%~dp0"

echo.
echo  ========================================
echo    微信账单自动统计  wechat-bill-ocr
echo  ========================================
echo.

:: ---------- 优先使用项目 .venv ----------
set "VENV_PY=.venv\Scripts\python.exe"
set "VENV_PIP=.venv\Scripts\pip.exe"
set "PYTHON_CMD="
set "PIP_CMD="

if exist "%VENV_PY%" (
    set "PYTHON_CMD=%VENV_PY%"
    set "PIP_CMD=%VENV_PIP%"
    echo [OK] 使用项目虚拟环境: .venv
) else (
    :: 没有 .venv，尝试系统 Python
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [错误] 未找到 .venv，也未检测到系统 Python。
        echo.
        echo 请先在本目录执行:
        echo   uv venv
        echo   uv pip install -e .
        echo.
        echo 或安装系统 Python 3.11+ 并勾选 Add to PATH。
        echo.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=python"
    set "PIP_CMD=pip"
    echo [提示] 未找到 .venv，使用系统 Python
    echo 建议先执行: uv venv ^&^& uv pip install -e .
)

for /f "tokens=*" %%i in ('"%PYTHON_CMD%" --version 2^>^&1') do set PYVER=%%i
echo [OK] %PYVER%

:: ---------- 检查项目是否已安装到当前 Python ----------
echo.
echo 正在检查项目是否已安装...
"%PYTHON_CMD%" -c "import wechat_bill" >nul 2>&1
if errorlevel 1 (
    echo 首次运行或环境不完整，正在安装依赖...
    if exist "%VENV_PY%" (
        :: 有 venv 时优先用 uv 安装（更快）
        where uv >nul 2>&1
        if not errorlevel 1 (
            uv pip install -e .
        ) else (
            "%PIP_CMD%" install -e .
        )
    ) else (
        "%PIP_CMD%" install -e .
    )
    if errorlevel 1 (
        echo [错误] 安装失败。
        echo 请手动执行: uv venv ^&^& uv pip install -e .
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
"%PYTHON_CMD%" -m wechat_bill --months %months%
goto after_run

:do_today
echo.
echo 请确认手机已打开账单页并滚动到顶部，保持亮屏。
pause
echo.
"%PYTHON_CMD%" -m wechat_bill --today
goto after_run

:do_days
echo.
"%PYTHON_CMD%" -m wechat_bill --days 7
goto after_run

:do_range
echo.
set /p start=开始日期 (YYYY-MM-DD): 
set /p end=结束日期 (YYYY-MM-DD): 
echo.
echo 请确认手机已打开账单页并滚动到顶部，保持亮屏。
pause
echo.
"%PYTHON_CMD%" -m wechat_bill --start-date %start% --end-date %end%
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

@echo off
chcp 65001 >nul
setlocal

title wechat-bill-ocr
cd /d "%~dp0"

echo.
echo  ========================================
echo    wechat-bill-ocr
echo  ========================================
echo.

set "VENV_PY=.venv\Scripts\python.exe"

if exist "%VENV_PY%" (
    echo [OK] using .venv
    set "PYTHON_CMD=%VENV_PY%"
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] .venv not found, and no system Python.
        echo.
        echo Please run first:
        echo   uv venv
        echo   uv pip install -e .
        echo.
        pause
        exit /b 1
    )
    echo [WARN] .venv not found, using system Python
    echo Suggest: uv venv ^&^& uv pip install -e .
    set "PYTHON_CMD=python"
)

for /f "tokens=*" %%i in ('"%PYTHON_CMD%" --version 2^>^&1') do echo [OK] %%i

echo.
echo Checking install...
"%PYTHON_CMD%" -c "import wechat_bill" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    where uv >nul 2>&1
    if not errorlevel 1 (
        uv pip install -e .
    ) else (
        "%PYTHON_CMD%" -m pip install -e .
    )
    if errorlevel 1 (
        echo [ERROR] install failed
        pause
        exit /b 1
    )
    echo [OK] installed
) else (
    echo [OK] package ready
)

echo.
echo Checking adb devices...
adb devices >nul 2>&1
if errorlevel 1 (
    echo [WARN] adb not found in PATH
) else (
    adb devices -l
)

echo.
"%PYTHON_CMD%" scripts\launcher.py

endlocal

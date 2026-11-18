@echo off
:: 兼容旧路径，直接调用根目录的一键脚本
cd /d "%~dp0.."
call "一键统计.bat"

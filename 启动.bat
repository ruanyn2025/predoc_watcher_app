@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem 按需改成你自己的解释器路径；找不到就退回 PATH 里的 python
set PY=D:\miniforge3\envs\dc1\pythonw.exe
if not exist "%PY%" set PY=pythonw

start "" "%PY%" desktop.py %*

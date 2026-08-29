@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem 找 Python：优先环境变量，其次 python_path.txt（自己建，已被 gitignore），
rem 最后退回 PATH 里的。用 pythonw 是为了不弹黑框。
set PY=
if defined PREDOC_PYTHON set "PY=%PREDOC_PYTHON%"
if "%PY%"=="" if exist "python_path.txt" set /p PY=<python_path.txt
if "%PY%"=="" set PY=pythonw

where "%PY%" >nul 2>&1 || if not exist "%PY%" (
  echo 找不到 Python。请先安装 Python 3.9+，或把解释器完整路径写进 python_path.txt
  echo Python not found. Install Python 3.9+, or put the interpreter path in python_path.txt
  pause
  exit /b 1
)

start "" "%PY%" desktop.py %*

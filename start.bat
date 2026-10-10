@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo ============================================
echo            优选商城 - 一键启动
echo ============================================
echo.

rem ---- 1. 检查 Python ----
set "PY="
where python >nul 2>&1 && set "PY=python"
if not defined PY (
    where py >nul 2>&1 && set "PY=py"
)
if not defined PY (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+ 并加入 PATH。
    echo        下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('%PY% --version 2^>^&1') do echo [1/4] 已检测到 %%v

rem ---- 2. 准备虚拟环境 ----
if not exist ".venv\Scripts\python.exe" (
    echo [2/4] 首次运行，正在创建虚拟环境 .venv ...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败。
        pause
        exit /b 1
    )
) else (
    echo [2/4] 虚拟环境已存在，跳过创建。
)
set "VPY=.venv\Scripts\python.exe"

rem ---- 3. 安装依赖 ----
echo [3/4] 检查并安装依赖 ...
"%VPY%" -m pip install --upgrade pip -q
"%VPY%" -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查网络后重试。
    pause
    exit /b 1
)

rem ---- 4. 初始化数据库 ----
if not exist "instance\shopping.db" (
    echo [4/4] 未发现数据库，正在初始化演示数据 ...
    "%VPY%" seed.py
) else (
    echo [4/4] 数据库已存在，跳过初始化。
)

echo.
echo ============================================
echo   启动成功！请在浏览器访问：
echo     http://127.0.0.1:5000
echo.
echo   管理员: admin / admin123
echo   普通用户: demo / 123456
echo.
echo   按 Ctrl+C 可停止服务
echo ============================================
echo.

"%VPY%" app.py
pause

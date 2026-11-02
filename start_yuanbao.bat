@echo off
setlocal EnableExtensions
chcp 65001 >nul
title 元宝 - 桌面宠物
cd /d "%~dp0"
rem 固定 UTF-8 输出，避免中文/emoji 在 GBK 控制台里报 UnicodeEncodeError
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

echo.
echo ============================================
echo   元宝桌宠 YuanBaoPet
echo ============================================
echo.

if not exist "main.py" (
    echo [错误] 当前目录里找不到 main.py。
    echo        请把本文件和 main.py 放在同一个文件夹里再运行。
    goto :fail
)

rem ---------- 1. 找一个能用的 Python ----------
rem 优先选已经装好 PyQt5 的解释器，避免重复安装
set "PY="
for %%C in ("py -3" "python" "python3") do (
    if not defined PY (
        %%~C -c "import PyQt5" >nul 2>nul
        if not errorlevel 1 set "PY=%%~C"
    )
)
for %%C in ("py -3" "python" "python3") do (
    if not defined PY (
        %%~C -c "import sys" >nul 2>nul
        if not errorlevel 1 set "PY=%%~C"
    )
)
if not defined PY (
    echo [错误] 没有找到 Python。
    echo        请先安装 Python 3.8+ ：https://www.python.org/downloads/
    echo        安装时记得勾选 "Add python.exe to PATH"。
    goto :fail
)
echo [1/2] 使用 Python：%PY%
%PY% -c "import sys; print('      版本 ' + sys.version.split()[0] + '   ' + sys.executable)"

rem ---------- 2. 检查 PyQt5，缺了就自动装 ----------
%PY% -c "import PyQt5" >nul 2>nul
if errorlevel 1 (
    echo [2/2] 缺少 PyQt5，正在自动安装（需要联网，请稍候）...
    %PY% -m pip install --disable-pip-version-check PyQt5
    %PY% -c "import PyQt5" >nul 2>nul
    if errorlevel 1 (
        echo.
        echo [错误] PyQt5 安装失败，请手动执行下面这条命令后重试：
        echo        %PY% -m pip install PyQt5
        goto :fail
    )
    echo       PyQt5 安装完成。
) else (
    echo [2/2] PyQt5 已就绪。
)

echo.
echo 正在启动元宝...
echo.
%PY% main.py
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo.
    echo [错误] 元宝异常退出，返回码 %RC%，请把上面的报错信息发给开发者。
    call :quit %RC%
    exit /b %RC%
)

echo.
echo 元宝已关闭，再见~
call :quit 0
exit /b 0

:fail
call :quit 1
exit /b 1

:quit
rem 双击运行时暂停，方便看报错；设置 NO_PAUSE=1 可跳过（自动化用）
if not defined NO_PAUSE pause
exit /b %1

@echo off
setlocal EnableExtensions
chcp 65001 >nul
title 元宝 - EXE 打包工具
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

echo.
echo ============================================
echo   元宝桌宠 YuanBaoPet - EXE 打包工具
echo ============================================
echo.

if not exist "main.py" (
    echo [错误] 当前目录里找不到 main.py。
    echo        请把本文件和全部 .py 文件放在同一个文件夹里再运行。
    goto :fail
)
if not exist "sprites\yuanbao_idle_0.png" (
    echo [错误] 找不到 sprites 图片素材（sprites\yuanbao_idle_0.png）。
    echo        打包前请确认 sprites 文件夹完整。
    goto :fail
)

rem ---------- 1. 找一个能用的 Python ----------
set "PY="
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
echo [1/5] 使用 Python：%PY%
%PY% -c "import sys; print('      版本 ' + sys.version.split()[0] + '   ' + sys.executable)"

rem ---------- 2. 依赖：PyQt5 + PyInstaller ----------
%PY% -c "import PyQt5" >nul 2>nul
if errorlevel 1 (
    echo [2/5] 正在安装 PyQt5...
    %PY% -m pip install --disable-pip-version-check PyQt5
    %PY% -c "import PyQt5" >nul 2>nul
    if errorlevel 1 goto :depfail
)
%PY% -c "import PyInstaller" >nul 2>nul
if errorlevel 1 (
    echo [2/5] 正在安装 PyInstaller...
    %PY% -m pip install --disable-pip-version-check pyinstaller
    %PY% -c "import PyInstaller" >nul 2>nul
    if errorlevel 1 goto :depfail
)
echo [2/5] 依赖已就绪（PyQt5 + PyInstaller）。

rem ---------- 3. 清理旧构建 ----------
echo [3/5] 清理旧构建...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist YuanBaoPet.spec del /q YuanBaoPet.spec

rem ---------- 4. 打包 ----------
echo [4/5] 正在打包为单个 EXE，约需 1-5 分钟，请耐心等待...
echo.
rem 图标：有 yuanbao.ico 就嵌进 EXE，并打包进去供托盘使用
rem （想换成自己的图标：把 yuanbao.ico 换成任意 .ico 即可，或改 make_icon.py）
set "ICON_OPT="
if exist "yuanbao.ico" set ICON_OPT=--icon yuanbao.ico --add-data "yuanbao.ico;."
rem 注意：这里用 "python -m PyInstaller"，不依赖 PATH 里的 pyinstaller.exe
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name "YuanBaoPet" ^
    %ICON_OPT% ^
    --add-data "sprites;sprites" ^
    main.py
if errorlevel 1 goto :buildfail
if not exist "dist\YuanBaoPet.exe" goto :buildfail

rem ---------- 5. 复制到桌面 ----------
echo.
echo [5/5] 复制 EXE 到桌面...
set "DESKTOP="
for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESKTOP=%%D"
if not defined DESKTOP set "DESKTOP=%USERPROFILE%\Desktop"

if not exist "%DESKTOP%" (
    echo [提示] 桌面上没有复制成功，EXE 在：dist\YuanBaoPet.exe
) else (
    copy /y "dist\YuanBaoPet.exe" "%DESKTOP%\YuanBaoPet.exe" >nul
    if errorlevel 1 (
        echo [提示] 复制到桌面失败，EXE 在：dist\YuanBaoPet.exe
    ) else (
        echo [完成] 已复制到：%DESKTOP%\YuanBaoPet.exe
    )
)

echo.
echo ============================================
echo   打包完成！
echo   EXE 位置：%CD%\dist\YuanBaoPet.exe
echo   发送给客户即可，对方无需安装 Python。
echo ============================================
echo.
call :quit 0
exit /b 0

:depfail
echo.
echo [错误] 依赖安装失败，请手动执行下面两条命令后重试：
echo        %PY% -m pip install PyQt5
echo        %PY% -m pip install pyinstaller
goto :fail

:buildfail
echo.
echo [错误] 打包失败，请查看上面 PyInstaller 的报错信息。
goto :fail

:fail
echo.
call :quit 1
exit /b 1

:quit
rem 双击运行时暂停，方便看报错；设置 NO_PAUSE=1 可跳过（自动化用）
if not defined NO_PAUSE pause
exit /b %1

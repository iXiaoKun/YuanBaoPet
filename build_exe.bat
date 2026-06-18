@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ============================================
echo   元宝桌宠 YuanBaoPet - EXE 打包工具
echo ============================================
echo.

echo [1/3] 清理旧构建...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo [2/3] 正在打包为单个 EXE...

pyinstaller --noconfirm --onefile --windowed ^
    --name "YuanBaoPet" ^
    --add-data "sprites;sprites" ^
    --collect-all PyQt5 ^
    --hidden-import PyQt5.QtCore ^
    --hidden-import PyQt5.QtGui ^
    --hidden-import PyQt5.QtWidgets ^
    --clean ^
    --noconsole ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 打包失败！
    pause
    exit /b 1
)

echo.
echo [3/3] 复制到桌面...
copy /y "dist\YuanBaoPet.exe" "%USERPROFILE%\Desktop\YuanBaoPet.exe"

echo.
echo ============================================
echo   打包完成！
echo   EXE 已复制到桌面: YuanBaoPet.exe
echo   发送给客户即可，无需安装 Python！
echo ============================================
echo.
pause

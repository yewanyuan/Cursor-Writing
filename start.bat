@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM Cursor-Writing 一键启动脚本 (Windows)

echo ========================================
echo    Cursor-Writing AI 小说创作助手
echo ========================================
echo.

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM 检查 Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 检查 Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)

REM 检查 npm
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 npm
    pause
    exit /b 1
)

REM 检查后端虚拟环境
if not exist "%SCRIPT_DIR%backend\venv" (
    echo [提示] 首次运行，正在创建 Python 虚拟环境...
    cd "%SCRIPT_DIR%backend"
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    echo [完成] Python 环境创建完成
) else (
    cd "%SCRIPT_DIR%backend"
    call venv\Scripts\activate.bat
)

REM 检查前端依赖
if not exist "%SCRIPT_DIR%frontend\node_modules" (
    echo [提示] 首次运行，正在安装前端依赖...
    cd "%SCRIPT_DIR%frontend"
    call npm install
    echo [完成] 前端依赖安装完成
)

REM 创建 PID 文件目录
if not exist "%SCRIPT_DIR%.pids" mkdir "%SCRIPT_DIR%.pids"

REM 启动后端（新窗口）
echo [启动] 正在启动后端服务...
cd "%SCRIPT_DIR%backend"
start "Cursor-Writing Backend" cmd /c "call venv\Scripts\activate.bat && python -m app.main"
echo [完成] 后端已启动

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 启动前端（新窗口）
echo [启动] 正在启动前端服务...
cd "%SCRIPT_DIR%frontend"
start "Cursor-Writing Frontend" cmd /c "npm run dev"
echo [完成] 前端已启动

echo.
echo ========================================
echo    启动完成！
echo ========================================
echo.
echo 后端地址: http://localhost:8000
echo 前端地址: http://localhost:5173
echo API 文档: http://localhost:8000/docs
echo.
echo [提示] 关闭此窗口不会停止服务
echo [提示] 使用 stop.bat 停止所有服务
echo [提示] 或直接关闭后端和前端的命令行窗口
echo.
pause

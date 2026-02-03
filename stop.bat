@echo off
chcp 65001 >nul

REM Cursor-Writing 停止脚本 (Windows)

echo 正在停止 Cursor-Writing 服务...

REM 通过窗口标题关闭
taskkill /FI "WINDOWTITLE eq Cursor-Writing Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Cursor-Writing Frontend*" /F >nul 2>&1

REM 备用方案：通过端口关闭
REM 查找并关闭占用 8000 端口的进程（后端）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

REM 查找并关闭占用 5173 端口的进程（前端）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo 所有服务已停止
pause

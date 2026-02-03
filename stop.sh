#!/bin/bash
# Cursor-Writing 停止脚本 (Linux/macOS)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${YELLOW}正在停止 Cursor-Writing 服务...${NC}"

# 通过 PID 文件停止
if [ -f "$SCRIPT_DIR/.pids/backend.pid" ]; then
    PID=$(cat "$SCRIPT_DIR/.pids/backend.pid")
    if kill -0 $PID 2>/dev/null; then
        kill $PID 2>/dev/null
        echo -e "${GREEN}后端服务已停止 (PID: $PID)${NC}"
    fi
    rm "$SCRIPT_DIR/.pids/backend.pid"
fi

if [ -f "$SCRIPT_DIR/.pids/frontend.pid" ]; then
    PID=$(cat "$SCRIPT_DIR/.pids/frontend.pid")
    if kill -0 $PID 2>/dev/null; then
        kill $PID 2>/dev/null
        echo -e "${GREEN}前端服务已停止 (PID: $PID)${NC}"
    fi
    rm "$SCRIPT_DIR/.pids/frontend.pid"
fi

# 备用方案：通过端口查找进程
# 停止后端 (port 8000)
BACKEND_PID=$(lsof -ti:8000 2>/dev/null)
if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID 2>/dev/null
    echo -e "${GREEN}后端服务已停止 (端口 8000)${NC}"
fi

# 停止前端 (port 5173)
FRONTEND_PID=$(lsof -ti:5173 2>/dev/null)
if [ -n "$FRONTEND_PID" ]; then
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}前端服务已停止 (端口 5173)${NC}"
fi

echo -e "${GREEN}所有服务已停止${NC}"

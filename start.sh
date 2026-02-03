#!/bin/bash
# Cursor-Writing 一键启动脚本 (Linux/macOS)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Cursor-Writing AI 小说创作助手${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 Python3，请先安装 Python 3.10+${NC}"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未找到 Node.js，请先安装 Node.js 18+${NC}"
    exit 1
fi

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}错误: 未找到 npm${NC}"
    exit 1
fi

# 检查后端虚拟环境
if [ ! -d "$SCRIPT_DIR/backend/venv" ]; then
    echo -e "${YELLOW}首次运行，正在创建 Python 虚拟环境...${NC}"
    cd "$SCRIPT_DIR/backend"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo -e "${GREEN}Python 环境创建完成${NC}"
else
    cd "$SCRIPT_DIR/backend"
    source venv/bin/activate
fi

# 检查前端依赖
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    echo -e "${YELLOW}首次运行，正在安装前端依赖...${NC}"
    cd "$SCRIPT_DIR/frontend"
    npm install
    echo -e "${GREEN}前端依赖安装完成${NC}"
fi

# 创建 PID 文件目录
mkdir -p "$SCRIPT_DIR/.pids"

# 启动后端
echo -e "${BLUE}正在启动后端服务...${NC}"
cd "$SCRIPT_DIR/backend"
source venv/bin/activate
python -m app.main &
BACKEND_PID=$!
echo $BACKEND_PID > "$SCRIPT_DIR/.pids/backend.pid"
echo -e "${GREEN}后端已启动 (PID: $BACKEND_PID)${NC}"

# 等待后端启动
sleep 2

# 启动前端
echo -e "${BLUE}正在启动前端服务...${NC}"
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$SCRIPT_DIR/.pids/frontend.pid"
echo -e "${GREEN}前端已启动 (PID: $FRONTEND_PID)${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   启动完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "后端地址: ${BLUE}http://localhost:8000${NC}"
echo -e "前端地址: ${BLUE}http://localhost:5173${NC}"
echo -e "API 文档: ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}提示: 使用 ./stop.sh 停止所有服务${NC}"
echo -e "${YELLOW}提示: 按 Ctrl+C 也可以停止服务${NC}"
echo ""

# 捕获退出信号
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"

    if [ -f "$SCRIPT_DIR/.pids/backend.pid" ]; then
        kill $(cat "$SCRIPT_DIR/.pids/backend.pid") 2>/dev/null || true
        rm "$SCRIPT_DIR/.pids/backend.pid"
    fi

    if [ -f "$SCRIPT_DIR/.pids/frontend.pid" ]; then
        kill $(cat "$SCRIPT_DIR/.pids/frontend.pid") 2>/dev/null || true
        rm "$SCRIPT_DIR/.pids/frontend.pid"
    fi

    # 也尝试杀死子进程
    pkill -P $BACKEND_PID 2>/dev/null || true
    pkill -P $FRONTEND_PID 2>/dev/null || true

    echo -e "${GREEN}服务已停止${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 等待子进程
wait

"""
WebSocket API
实时推送会话状态
"""

import json
import logging
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger(__name__)

# 连接管理：每个项目只保留一个活跃连接
connections: Dict[str, WebSocket] = {}


async def broadcast(project_id: str, message: dict):
    """向项目的连接发送消息"""
    if project_id not in connections:
        return

    ws = connections[project_id]
    try:
        await ws.send_json(message)
    except Exception as e:
        logger.debug(f"发送消息失败: {e}")
        del connections[project_id]


@router.websocket("/{project_id}/session")
async def session_websocket(websocket: WebSocket, project_id: str):
    """会话 WebSocket 端点"""
    await websocket.accept()

    # 关闭旧连接（如果存在）
    if project_id in connections:
        old_ws = connections[project_id]
        try:
            await old_ws.close()
        except:
            pass
        logger.debug(f"关闭旧 WebSocket 连接: {project_id}")

    # 保存新连接
    connections[project_id] = websocket
    logger.info(f"WebSocket 连接: {project_id}")

    try:
        while True:
            # 接收心跳或消息
            data = await websocket.receive_text()
            # 可以处理客户端消息
    except WebSocketDisconnect:
        pass
    finally:
        if connections.get(project_id) == websocket:
            del connections[project_id]
        logger.info(f"WebSocket 断开: {project_id}")

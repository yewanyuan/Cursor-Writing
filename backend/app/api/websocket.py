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

# 连接管理
connections: Dict[str, Set[WebSocket]] = {}


async def broadcast(project_id: str, message: dict):
    """向项目的所有连接广播消息"""
    if project_id not in connections:
        return

    dead = set()
    for ws in connections[project_id]:
        try:
            await ws.send_json(message)
        except:
            dead.add(ws)

    connections[project_id] -= dead


@router.websocket("/{project_id}/session")
async def session_websocket(websocket: WebSocket, project_id: str):
    """会话 WebSocket 端点"""
    await websocket.accept()

    # 添加连接
    if project_id not in connections:
        connections[project_id] = set()
    connections[project_id].add(websocket)

    logger.info(f"WebSocket 连接: {project_id}")

    try:
        while True:
            # 接收心跳或消息
            data = await websocket.receive_text()
            # 可以处理客户端消息
    except WebSocketDisconnect:
        pass
    finally:
        connections[project_id].discard(websocket)
        logger.info(f"WebSocket 断开: {project_id}")

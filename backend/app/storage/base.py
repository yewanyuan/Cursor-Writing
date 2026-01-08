"""
基础存储工具
提供 YAML、JSONL、Markdown 文件的读写
"""

import json
import logging
from pathlib import Path
from typing import Any, List, Optional, TypeVar, Type

import yaml
import aiofiles

from app.utils.exceptions import StorageError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseStorage:
    """基础存储类"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_project_dir(self, project_id: str) -> Path:
        """获取项目目录"""
        return self.data_dir / project_id

    def _ensure_dir(self, path: Path) -> None:
        """确保目录存在"""
        path.mkdir(parents=True, exist_ok=True)

    # ========== YAML 操作 ==========

    async def read_yaml(self, path: Path) -> Optional[dict]:
        """读取 YAML 文件"""
        if not path.exists():
            return None
        try:
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return yaml.safe_load(content)
        except Exception as e:
            logger.error(f"读取 YAML 失败: {path}, {e}")
            raise StorageError(f"读取失败: {path}", str(path))

    async def write_yaml(self, path: Path, data: dict) -> None:
        """写入 YAML 文件"""
        self._ensure_dir(path.parent)
        try:
            async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                content = yaml.dump(data, allow_unicode=True, sort_keys=False)
                await f.write(content)
        except Exception as e:
            logger.error(f"写入 YAML 失败: {path}, {e}")
            raise StorageError(f"写入失败: {path}", str(path))

    # ========== JSONL 操作 ==========

    async def read_jsonl(self, path: Path) -> List[dict]:
        """读取 JSONL 文件（每行一个 JSON）"""
        if not path.exists():
            return []
        try:
            items = []
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                async for line in f:
                    line = line.strip()
                    if line:
                        items.append(json.loads(line))
            return items
        except Exception as e:
            logger.error(f"读取 JSONL 失败: {path}, {e}")
            raise StorageError(f"读取失败: {path}", str(path))

    async def append_jsonl(self, path: Path, item: dict) -> None:
        """追加一行到 JSONL 文件"""
        self._ensure_dir(path.parent)
        try:
            async with aiofiles.open(path, 'a', encoding='utf-8') as f:
                await f.write(json.dumps(item, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"追加 JSONL 失败: {path}, {e}")
            raise StorageError(f"写入失败: {path}", str(path))

    async def write_jsonl(self, path: Path, items: List[dict]) -> None:
        """覆盖写入 JSONL 文件"""
        self._ensure_dir(path.parent)
        try:
            async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                for item in items:
                    await f.write(json.dumps(item, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"写入 JSONL 失败: {path}, {e}")
            raise StorageError(f"写入失败: {path}", str(path))

    # ========== Markdown/Text 操作 ==========

    async def read_text(self, path: Path) -> Optional[str]:
        """读取文本文件"""
        if not path.exists():
            return None
        try:
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception as e:
            logger.error(f"读取文本失败: {path}, {e}")
            raise StorageError(f"读取失败: {path}", str(path))

    async def write_text(self, path: Path, content: str) -> None:
        """写入文本文件"""
        self._ensure_dir(path.parent)
        try:
            async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                await f.write(content)
        except Exception as e:
            logger.error(f"写入文本失败: {path}, {e}")
            raise StorageError(f"写入失败: {path}", str(path))

    # ========== 通用操作 ==========

    async def exists(self, path: Path) -> bool:
        """检查文件是否存在"""
        return path.exists()

    async def delete(self, path: Path) -> bool:
        """删除文件"""
        if path.exists():
            path.unlink()
            return True
        return False

    async def list_dir(self, path: Path) -> List[str]:
        """列出目录内容"""
        if not path.exists():
            return []
        return [p.name for p in path.iterdir()]

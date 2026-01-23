"""
存储缓存层
减少文件读取，提升性能
"""

import logging
import time
from typing import Dict, Any, Optional, TypeVar, Generic, Callable
from dataclasses import dataclass, field
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """缓存条目"""
    value: T
    timestamp: float
    ttl: float  # 存活时间（秒）

    def is_expired(self) -> bool:
        """是否已过期"""
        return time.time() - self.timestamp > self.ttl


class LRUCache(Generic[T]):
    """LRU 缓存实现"""

    def __init__(self, maxsize: int = 100, default_ttl: float = 300.0):
        """
        Args:
            maxsize: 最大缓存条目数
            default_ttl: 默认存活时间（秒），默认5分钟
        """
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._access_order: list = []  # 记录访问顺序，用于 LRU 淘汰

    def get(self, key: str) -> Optional[T]:
        """获取缓存"""
        if key not in self._cache:
            return None

        entry = self._cache[key]

        # 检查是否过期
        if entry.is_expired():
            self.delete(key)
            return None

        # 更新访问顺序
        self._update_access(key)

        return entry.value

    def set(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """设置缓存"""
        if ttl is None:
            ttl = self.default_ttl

        # 如果缓存已满，淘汰最久未访问的
        if len(self._cache) >= self.maxsize and key not in self._cache:
            self._evict()

        self._cache[key] = CacheEntry(value=value, timestamp=time.time(), ttl=ttl)
        self._update_access(key)

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._access_order.clear()

    def invalidate_prefix(self, prefix: str) -> int:
        """使指定前缀的缓存失效"""
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            self.delete(key)
        return len(keys_to_delete)

    def _update_access(self, key: str) -> None:
        """更新访问顺序"""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def _evict(self) -> None:
        """淘汰最久未访问的条目"""
        if self._access_order:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]
                logger.debug(f"缓存淘汰: {oldest_key}")

    def stats(self) -> Dict[str, Any]:
        """缓存统计信息"""
        valid_count = sum(1 for e in self._cache.values() if not e.is_expired())
        return {
            "total": len(self._cache),
            "valid": valid_count,
            "expired": len(self._cache) - valid_count,
            "maxsize": self.maxsize
        }


class StorageCache:
    """存储层缓存管理器"""

    # TTL 配置（秒）
    TTL_CONFIG = {
        "character": 300.0,   # 角色卡 5分钟
        "world": 300.0,       # 世界观卡 5分钟
        "style": 600.0,       # 文风卡 10分钟（不常变化）
        "rules": 600.0,       # 规则卡 10分钟
        "fact": 120.0,        # 事实 2分钟（可能频繁更新）
        "timeline": 120.0,    # 时间线 2分钟
        "state": 120.0,       # 角色状态 2分钟
        "draft": 60.0,        # 草稿 1分钟（频繁更新）
        "summary": 300.0,     # 摘要 5分钟
        "project": 300.0,     # 项目信息 5分钟
    }

    def __init__(self, maxsize: int = 500):
        self._cache = LRUCache(maxsize=maxsize)
        self._hits = 0
        self._misses = 0

    def _make_key(self, category: str, project_id: str, *args) -> str:
        """生成缓存键"""
        parts = [category, project_id] + [str(a) for a in args if a]
        return ":".join(parts)

    def get(self, category: str, project_id: str, *args) -> Optional[Any]:
        """获取缓存"""
        key = self._make_key(category, project_id, *args)
        value = self._cache.get(key)

        if value is not None:
            self._hits += 1
            logger.debug(f"缓存命中: {key}")
        else:
            self._misses += 1

        return value

    def set(self, category: str, project_id: str, *args, value: Any) -> None:
        """设置缓存"""
        key = self._make_key(category, project_id, *args)
        ttl = self.TTL_CONFIG.get(category, 300.0)
        self._cache.set(key, value, ttl)
        logger.debug(f"缓存设置: {key} (TTL={ttl}s)")

    def delete(self, category: str, project_id: str, *args) -> bool:
        """删除缓存"""
        key = self._make_key(category, project_id, *args)
        return self._cache.delete(key)

    def invalidate_project(self, project_id: str) -> int:
        """使项目的所有缓存失效"""
        count = 0
        for category in self.TTL_CONFIG.keys():
            count += self._cache.invalidate_prefix(f"{category}:{project_id}")
        logger.info(f"项目 {project_id} 缓存已清除: {count} 条")
        return count

    def invalidate_category(self, category: str, project_id: str) -> int:
        """使项目某类别的缓存失效"""
        prefix = f"{category}:{project_id}"
        count = self._cache.invalidate_prefix(prefix)
        logger.debug(f"缓存失效: {prefix}* ({count} 条)")
        return count

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("缓存已全部清空")

    def stats(self) -> Dict[str, Any]:
        """缓存统计"""
        cache_stats = self._cache.stats()
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0

        return {
            **cache_stats,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2%}"
        }


# 全局缓存实例
_storage_cache: Optional[StorageCache] = None


def get_cache() -> StorageCache:
    """获取全局缓存实例"""
    global _storage_cache
    if _storage_cache is None:
        _storage_cache = StorageCache()
    return _storage_cache


def cached(category: str):
    """
    缓存装饰器

    Usage:
        @cached("character")
        async def get_character(self, project_id: str, name: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, project_id: str, *args, **kwargs):
            cache = get_cache()

            # 尝试从缓存获取
            cached_value = cache.get(category, project_id, *args)
            if cached_value is not None:
                return cached_value

            # 调用原函数
            result = await func(self, project_id, *args, **kwargs)

            # 缓存结果
            if result is not None:
                cache.set(category, project_id, *args, value=result)

            return result
        return wrapper
    return decorator


def invalidate_cache(category: str):
    """
    缓存失效装饰器，用于写操作

    Usage:
        @invalidate_cache("character")
        async def save_character(self, project_id: str, name: str, card):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, project_id: str, *args, **kwargs):
            result = await func(self, project_id, *args, **kwargs)

            # 使相关缓存失效
            cache = get_cache()
            cache.invalidate_category(category, project_id)

            return result
        return wrapper
    return decorator

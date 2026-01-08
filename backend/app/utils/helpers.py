"""
通用工具函数 (Helper Functions)
"""

import re
import uuid
from datetime import datetime
from typing import Optional


def generate_id(prefix: str = "") -> str:
    """
    生成唯一 ID

    Args:
        prefix: ID 前缀，如 "F" 表示 Fact，"T" 表示 Timeline

    Returns:
        格式化的 ID，如 "F0001" 或 UUID
    """
    if prefix:
        # 简单递增 ID（实际使用时需要配合存储层）
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        short_uuid = uuid.uuid4().hex[:4].upper()
        return f"{prefix}{timestamp}{short_uuid}"
    else:
        return uuid.uuid4().hex


def sanitize_filename(name: str) -> str:
    """
    清理文件名，移除不安全字符

    Args:
        name: 原始文件名

    Returns:
        安全的文件名
    """
    # 移除或替换不安全字符
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    # 移除开头和结尾的空格和点
    sanitized = sanitized.strip('. ')
    # 限制长度
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return sanitized or "unnamed"


def count_words(text: str, language: str = "auto") -> int:
    """
    统计文本字数

    Args:
        text: 文本内容
        language: 语言类型 ("zh" 中文, "en" 英文, "auto" 自动检测)

    Returns:
        字数/词数
    """
    if not text:
        return 0

    # 自动检测：如果中文字符超过 30%，按中文计数
    if language == "auto":
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text.replace(' ', ''))
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            language = "zh"
        else:
            language = "en"

    if language == "zh":
        # 中文：直接计算字符数（排除空白）
        return len(re.sub(r'\s', '', text))
    else:
        # 英文：按空格分词
        return len(text.split())


def parse_chapter_id(chapter: str) -> tuple[int, Optional[int]]:
    """
    解析章节 ID

    Args:
        chapter: 章节 ID，如 "ch01", "ch01-02", "prologue"

    Returns:
        (主章节号, 子章节号) 或 (0, None) 表示特殊章节
    """
    # 匹配 ch01, ch01-02 格式
    match = re.match(r'ch(\d+)(?:-(\d+))?', chapter.lower())
    if match:
        main = int(match.group(1))
        sub = int(match.group(2)) if match.group(2) else None
        return (main, sub)

    # 特殊章节（序章、尾声等）
    return (0, None)


def format_chapter_id(main: int, sub: Optional[int] = None) -> str:
    """
    格式化章节 ID

    Args:
        main: 主章节号
        sub: 子章节号（可选）

    Returns:
        格式化的章节 ID，如 "ch01", "ch01-02"
    """
    if main == 0:
        return "prologue"

    if sub is not None:
        return f"ch{main:02d}-{sub:02d}"
    else:
        return f"ch{main:02d}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本

    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

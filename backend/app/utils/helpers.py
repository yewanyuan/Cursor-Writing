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


def split_content_by_paragraphs(content: str, chunk_size: int = 3000, overlap: int = 200) -> list[str]:
    """
    按段落边界分割长文本，避免切断句子

    Args:
        content: 原始文本
        chunk_size: 每段目标大小
        overlap: 段落间重叠字符数（保证上下文连贯）

    Returns:
        分割后的文本块列表
    """
    if len(content) <= chunk_size:
        return [content]

    chunks = []
    paragraphs = content.split('\n\n')  # 按双换行分段

    current_chunk = ""
    for para in paragraphs:
        # 如果当前段落本身就超长，需要按句子分割
        if len(para) > chunk_size:
            # 先保存之前的内容
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            # 按句子分割超长段落
            sentences = re.split(r'([。！？.!?]+)', para)
            temp = ""
            for i in range(0, len(sentences), 2):
                sentence = sentences[i]
                punct = sentences[i + 1] if i + 1 < len(sentences) else ""
                full_sentence = sentence + punct

                if len(temp) + len(full_sentence) > chunk_size:
                    if temp:
                        chunks.append(temp.strip())
                    temp = full_sentence
                else:
                    temp += full_sentence

            if temp:
                current_chunk = temp
        else:
            # 正常段落处理
            if len(current_chunk) + len(para) + 2 > chunk_size:
                chunks.append(current_chunk.strip())
                # 保留一部分重叠内容
                if overlap > 0 and len(current_chunk) > overlap:
                    current_chunk = current_chunk[-overlap:] + "\n\n" + para
                else:
                    current_chunk = para
            else:
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def smart_truncate_content(content: str, budget: int = 4000) -> str:
    """
    智能截断：保留首尾和中间采样，适用于审稿等需要全局视角的场景

    Args:
        content: 原始文本
        budget: 总字符预算

    Returns:
        截断后的文本，包含首部、中部采样、尾部
    """
    if len(content) <= budget:
        return content

    # 分配预算：首部 40%，中间 20%，尾部 40%
    head_budget = int(budget * 0.4)
    middle_budget = int(budget * 0.2)
    tail_budget = budget - head_budget - middle_budget

    head = content[:head_budget]
    tail = content[-tail_budget:]

    # 中间采样：取中间位置的内容
    mid_start = len(content) // 2 - middle_budget // 2
    middle = content[mid_start:mid_start + middle_budget]

    return f"{head}\n\n[...中间部分省略，以下为中段采样...]\n\n{middle}\n\n[...省略部分结束，以下为结尾...]\n\n{tail}"


def estimate_tokens(text: str) -> int:
    """
    粗略估算文本的 token 数量

    Args:
        text: 文本内容

    Returns:
        估算的 token 数量
    """
    # 中文大约 1.5 字符 = 1 token，英文大约 4 字符 = 1 token
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    other_chars = len(text) - chinese_chars

    return int(chinese_chars / 1.5 + other_chars / 4)


def get_facts_by_token_budget(facts: list, token_budget: int = 2000) -> list:
    """
    在 token 预算内尽可能多取事实

    Args:
        facts: 事实列表（已按优先级排序）
        token_budget: token 预算

    Returns:
        筛选后的事实列表
    """
    selected = []
    used_tokens = 0

    for fact in facts:
        fact_tokens = estimate_tokens(fact.statement)
        if used_tokens + fact_tokens > token_budget:
            break
        selected.append(fact)
        used_tokens += fact_tokens

    return selected

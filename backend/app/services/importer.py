"""
小说导入服务
支持从 TXT / Markdown / EPUB / PDF 文件导入小说
自动分解章节、分析世界观和文风
"""

import io
import re
import zipfile
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ImportFormat(str, Enum):
    TXT = "txt"
    MARKDOWN = "markdown"
    EPUB = "epub"
    PDF = "pdf"


@dataclass
class ParsedChapter:
    """解析出的章节"""
    chapter_name: str  # 章节标识，如"第一章"
    title: str  # 章节标题，如"初入江湖"
    content: str  # 章节正文
    word_count: int = 0

    def __post_init__(self):
        if self.word_count == 0:
            self.word_count = len(self.content)


@dataclass
class ParsedNovel:
    """解析出的小说"""
    title: str  # 书名
    author: str = ""
    description: str = ""
    chapters: List[ParsedChapter] = field(default_factory=list)
    raw_content: str = ""  # 原始文本（用于AI分析）
    total_words: int = 0

    def __post_init__(self):
        if self.total_words == 0:
            self.total_words = sum(ch.word_count for ch in self.chapters)


@dataclass
class AnalysisResult:
    """AI 分析结果"""
    # 世界观设定
    world_settings: List[Dict[str, str]] = field(default_factory=list)  # [{name, category, description}]
    # 角色
    characters: List[Dict[str, Any]] = field(default_factory=list)  # [{name, identity, personality, background}]
    # 文风
    style: Dict[str, Any] = field(default_factory=dict)  # {narrative_distance, pacing, sentence_style, ...}
    # 规则（从内容推断）
    rules: Dict[str, List[str]] = field(default_factory=dict)  # {dos, donts}


class NovelParser:
    """小说解析器"""

    # 常见的章节标题模式
    CHAPTER_PATTERNS = [
        # 中文数字章节：第一章、第一百二十三章
        r'^第[零一二三四五六七八九十百千万〇]+章\s*[：:.]?\s*(.*)$',
        # 阿拉伯数字章节：第1章、第123章
        r'^第\d+章\s*[：:.]?\s*(.*)$',
        # 简化格式：章节一、章节1
        r'^章节[零一二三四五六七八九十百千万〇\d]+\s*[：:.]?\s*(.*)$',
        # 卷/篇 + 章
        r'^[卷篇][零一二三四五六七八九十百千万〇\d]+\s+第[零一二三四五六七八九十百千万〇\d]+章\s*[：:.]?\s*(.*)$',
        # Chapter X 格式
        r'^Chapter\s*\d+\s*[：:.]?\s*(.*)$',
        # 纯数字章节：1、2、3...（行首数字后跟标点或空格）
        r'^(\d+)[、.．。]\s*(.*)$',
        # 序章、楔子、尾声等
        r'^(序章|序|楔子|引子|尾声|番外|后记)\s*[：:.]?\s*(.*)$',
    ]

    def __init__(self):
        self.chapter_patterns = [re.compile(p, re.MULTILINE) for p in self.CHAPTER_PATTERNS]

    def detect_format(self, filename: str, content: bytes) -> ImportFormat:
        """检测文件格式"""
        filename_lower = filename.lower()

        if filename_lower.endswith('.txt'):
            return ImportFormat.TXT
        elif filename_lower.endswith('.md') or filename_lower.endswith('.markdown'):
            return ImportFormat.MARKDOWN
        elif filename_lower.endswith('.epub'):
            return ImportFormat.EPUB
        elif filename_lower.endswith('.pdf'):
            return ImportFormat.PDF

        # 尝试从内容检测
        if content[:4] == b'PK\x03\x04':  # ZIP 文件头（EPUB）
            return ImportFormat.EPUB
        if content[:4] == b'%PDF':
            return ImportFormat.PDF

        # 默认当作文本处理
        return ImportFormat.TXT

    def parse(self, filename: str, content: bytes) -> ParsedNovel:
        """解析小说文件"""
        format = self.detect_format(filename, content)

        if format == ImportFormat.TXT:
            return self.parse_txt(filename, content)
        elif format == ImportFormat.MARKDOWN:
            return self.parse_markdown(filename, content)
        elif format == ImportFormat.EPUB:
            return self.parse_epub(filename, content)
        elif format == ImportFormat.PDF:
            return self.parse_pdf(filename, content)
        else:
            raise ValueError(f"不支持的文件格式: {format}")

    def parse_txt(self, filename: str, content: bytes) -> ParsedNovel:
        """解析 TXT 文件"""
        # 尝试多种编码
        text = None
        for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']:
            try:
                text = content.decode(encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if text is None:
            # 强制使用 utf-8，忽略错误
            text = content.decode('utf-8', errors='ignore')

        # 从文件名推断书名
        title = Path(filename).stem

        return self._parse_text_content(title, text)

    def parse_markdown(self, filename: str, content: bytes) -> ParsedNovel:
        """解析 Markdown 文件"""
        text = content.decode('utf-8', errors='ignore')

        # 从文件名推断书名
        title = Path(filename).stem

        # Markdown 可能有 YAML front matter
        if text.startswith('---'):
            parts = text.split('---', 2)
            if len(parts) >= 3:
                # 解析 front matter
                front_matter = parts[1].strip()
                text = parts[2].strip()

                # 简单解析 title
                for line in front_matter.split('\n'):
                    if line.startswith('title:'):
                        title = line.split(':', 1)[1].strip().strip('"\'')

        # 移除 Markdown 格式标记，简化为纯文本后解析
        # 但保留章节标题格式
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # 将 ## 章节标题 转换为 章节标题
            if line.startswith('##'):
                line = line.lstrip('#').strip()
            elif line.startswith('#'):
                # 一级标题可能是书名
                potential_title = line.lstrip('#').strip()
                if not title or title == Path(filename).stem:
                    title = potential_title
                continue

            # 移除链接、图片等
            line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
            line = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', line)

            cleaned_lines.append(line)

        text = '\n'.join(cleaned_lines)

        return self._parse_text_content(title, text)

    def parse_epub(self, filename: str, content: bytes) -> ParsedNovel:
        """解析 EPUB 文件"""
        title = Path(filename).stem
        author = ""
        description = ""
        chapters_content = []

        try:
            with zipfile.ZipFile(io.BytesIO(content), 'r') as epub:
                # 读取 content.opf 获取元数据和阅读顺序
                opf_path = None

                # 查找 container.xml
                try:
                    container = epub.read('META-INF/container.xml').decode('utf-8')
                    match = re.search(r'full-path="([^"]+)"', container)
                    if match:
                        opf_path = match.group(1)
                except KeyError:
                    pass

                # 尝试常见路径
                if not opf_path:
                    for path in ['OEBPS/content.opf', 'content.opf', 'OPS/content.opf']:
                        if path in epub.namelist():
                            opf_path = path
                            break

                if opf_path:
                    opf_content = epub.read(opf_path).decode('utf-8')
                    opf_dir = str(Path(opf_path).parent)
                    if opf_dir == '.':
                        opf_dir = ''

                    # 解析元数据
                    soup = BeautifulSoup(opf_content, 'xml')

                    title_tag = soup.find('dc:title') or soup.find('title')
                    if title_tag:
                        title = title_tag.get_text().strip()

                    creator_tag = soup.find('dc:creator') or soup.find('creator')
                    if creator_tag:
                        author = creator_tag.get_text().strip()

                    desc_tag = soup.find('dc:description') or soup.find('description')
                    if desc_tag:
                        description = desc_tag.get_text().strip()

                    # 获取阅读顺序
                    spine = soup.find('spine')
                    manifest = soup.find('manifest')

                    if spine and manifest:
                        # 构建 id -> href 映射
                        id_to_href = {}
                        for item in manifest.find_all('item'):
                            item_id = item.get('id')
                            href = item.get('href')
                            if item_id and href:
                                id_to_href[item_id] = href

                        # 按阅读顺序读取内容
                        for itemref in spine.find_all('itemref'):
                            idref = itemref.get('idref')
                            if idref and idref in id_to_href:
                                href = id_to_href[idref]
                                if opf_dir:
                                    full_path = f"{opf_dir}/{href}"
                                else:
                                    full_path = href

                                try:
                                    html_content = epub.read(full_path).decode('utf-8')
                                    text = self._html_to_text(html_content)
                                    if text.strip():
                                        chapters_content.append(text)
                                except (KeyError, UnicodeDecodeError) as e:
                                    logger.warning(f"无法读取 EPUB 内容 {full_path}: {e}")

        except zipfile.BadZipFile:
            raise ValueError("无效的 EPUB 文件")

        # 合并所有内容，重新解析章节
        full_text = '\n\n'.join(chapters_content)

        novel = self._parse_text_content(title, full_text)
        novel.author = author
        novel.description = description

        return novel

    def parse_pdf(self, filename: str, content: bytes) -> ParsedNovel:
        """解析 PDF 文件"""
        try:
            import pypdf
        except ImportError:
            try:
                import PyPDF2 as pypdf
            except ImportError:
                raise ImportError("需要安装 pypdf 或 PyPDF2 库来解析 PDF 文件: pip install pypdf")

        title = Path(filename).stem
        text_parts = []

        try:
            pdf_reader = pypdf.PdfReader(io.BytesIO(content))

            # 尝试获取元数据
            if pdf_reader.metadata:
                if pdf_reader.metadata.title:
                    title = pdf_reader.metadata.title
                # author 等其他元数据也可以提取

            # 提取所有页面的文本
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

        except Exception as e:
            raise ValueError(f"PDF 解析失败: {e}")

        full_text = '\n'.join(text_parts)

        return self._parse_text_content(title, full_text)

    def _html_to_text(self, html: str) -> str:
        """将 HTML 转换为纯文本"""
        soup = BeautifulSoup(html, 'html.parser')

        # 移除 script 和 style
        for tag in soup(['script', 'style']):
            tag.decompose()

        # 获取文本
        text = soup.get_text(separator='\n')

        # 清理多余空白
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]

        return '\n'.join(lines)

    def _parse_text_content(self, title: str, text: str) -> ParsedNovel:
        """从纯文本解析章节结构"""
        # 清理文本
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 尝试匹配章节
        chapters = self._split_chapters(text)

        # 如果没有检测到章节，整体作为一章
        if not chapters:
            chapters = [ParsedChapter(
                chapter_name="全文",
                title="",
                content=text.strip(),
            )]

        return ParsedNovel(
            title=title,
            chapters=chapters,
            raw_content=text[:50000]  # 保留前5万字用于AI分析
        )

    def _split_chapters(self, text: str) -> List[ParsedChapter]:
        """分割章节"""
        chapters = []
        lines = text.split('\n')

        current_chapter_name = None
        current_title = ""
        current_content = []

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                if current_content:
                    current_content.append("")
                continue

            # 检查是否是章节标题
            chapter_match = self._match_chapter_title(line_stripped)

            if chapter_match:
                # 保存之前的章节
                if current_chapter_name is not None and current_content:
                    content_text = '\n'.join(current_content).strip()
                    if content_text:
                        chapters.append(ParsedChapter(
                            chapter_name=current_chapter_name,
                            title=current_title,
                            content=content_text
                        ))

                # 开始新章节
                current_chapter_name = chapter_match['chapter_name']
                current_title = chapter_match.get('title', '')
                current_content = []
            else:
                # 普通内容行
                current_content.append(line)

        # 保存最后一章
        if current_chapter_name is not None and current_content:
            content_text = '\n'.join(current_content).strip()
            if content_text:
                chapters.append(ParsedChapter(
                    chapter_name=current_chapter_name,
                    title=current_title,
                    content=content_text
                ))

        return chapters

    def _match_chapter_title(self, line: str) -> Optional[Dict[str, str]]:
        """匹配章节标题"""
        # 章节标题通常较短
        if len(line) > 50:
            return None

        for pattern in self.chapter_patterns:
            match = pattern.match(line)
            if match:
                groups = match.groups()

                # 提取章节名和标题
                if '第' in line and '章' in line:
                    # 提取 "第X章" 部分
                    ch_match = re.match(r'(第[零一二三四五六七八九十百千万〇\d]+章)', line)
                    if ch_match:
                        chapter_name = ch_match.group(1)
                        title = line[ch_match.end():].strip()
                        # 移除标题前的标点
                        title = re.sub(r'^[：:.\s]+', '', title)
                        return {'chapter_name': chapter_name, 'title': title}

                # 序章、楔子等特殊章节
                if groups and groups[0] in ['序章', '序', '楔子', '引子', '尾声', '番外', '后记']:
                    return {
                        'chapter_name': groups[0],
                        'title': groups[1] if len(groups) > 1 else ''
                    }

                # 纯数字章节
                if re.match(r'^\d+[、.．。]', line):
                    num_match = re.match(r'^(\d+)[、.．。]\s*(.*)', line)
                    if num_match:
                        return {
                            'chapter_name': f"第{num_match.group(1)}章",
                            'title': num_match.group(2)
                        }

                # Chapter X 格式
                if line.lower().startswith('chapter'):
                    ch_match = re.match(r'Chapter\s*(\d+)\s*[：:.]?\s*(.*)', line, re.IGNORECASE)
                    if ch_match:
                        return {
                            'chapter_name': f"第{ch_match.group(1)}章",
                            'title': ch_match.group(2)
                        }

                # 通用匹配
                if groups:
                    return {
                        'chapter_name': line.split()[0] if line.split() else line,
                        'title': groups[-1] if groups[-1] else ''
                    }

        return None


class NovelAnalyzer:
    """小说分析器 - 使用 AI 分析世界观和文风"""

    def __init__(self):
        from app.llm import get_client
        self.llm = get_client()

    async def analyze(self, novel: ParsedNovel, sample_chapters: int = 3) -> AnalysisResult:
        """
        分析小说的世界观和文风

        Args:
            novel: 解析后的小说
            sample_chapters: 用于分析的章节数量

        Returns:
            分析结果
        """
        # 选择用于分析的内容
        sample_content = self._prepare_sample_content(novel, sample_chapters)

        # 并行执行分析任务
        import asyncio
        world_task = self._analyze_world_settings(sample_content)
        characters_task = self._analyze_characters(sample_content)
        style_task = self._analyze_style(sample_content)

        world_settings, characters, style = await asyncio.gather(
            world_task, characters_task, style_task
        )

        return AnalysisResult(
            world_settings=world_settings,
            characters=characters,
            style=style
        )

    def _prepare_sample_content(self, novel: ParsedNovel, sample_chapters: int) -> str:
        """准备用于分析的样本内容"""
        # 取前几章作为样本
        sample_texts = []

        for i, chapter in enumerate(novel.chapters[:sample_chapters]):
            # 每章最多取3000字
            content = chapter.content[:3000]
            sample_texts.append(f"【{chapter.chapter_name} {chapter.title}】\n{content}")

        return "\n\n---\n\n".join(sample_texts)

    async def _analyze_world_settings(self, content: str) -> List[Dict[str, str]]:
        """分析世界观设定"""
        prompt = f"""请分析以下小说片段，提取其中的世界观设定信息。

{content}

请以 JSON 格式输出世界观设定列表，每个设定包含：
- name: 设定名称（如"修炼体系"、"势力分布"等）
- category: 分类（如"功法体系"、"地理环境"、"社会制度"、"历史背景"等）
- description: 详细描述

只输出 JSON 数组，不要其他内容：
[
  {{"name": "...", "category": "...", "description": "..."}},
  ...
]

如果无法提取到明确的世界观设定，返回空数组 []"""

        try:
            response = await self.llm.chat([
                {"role": "user", "content": prompt}
            ], temperature=0.3)

            result_text = response.get("content", "[]")

            # 提取 JSON
            import json
            # 尝试找到 JSON 数组
            match = re.search(r'\[[\s\S]*\]', result_text)
            if match:
                return json.loads(match.group())
            return []
        except Exception as e:
            logger.error(f"世界观分析失败: {e}")
            return []

    async def _analyze_characters(self, content: str) -> List[Dict[str, Any]]:
        """分析角色信息"""
        prompt = f"""请分析以下小说片段，提取其中的主要角色信息。

{content}

请以 JSON 格式输出角色列表，每个角色包含：
- name: 角色名
- identity: 身份（如"主角"、"配角"、"反派"等）
- personality: 性格特点列表
- speech_pattern: 说话风格（如有）
- background: 背景介绍

只输出 JSON 数组，不要其他内容：
[
  {{"name": "...", "identity": "...", "personality": ["...", "..."], "speech_pattern": "...", "background": "..."}},
  ...
]

只提取明确出现的角色，不要推测。如果无法提取，返回空数组 []"""

        try:
            response = await self.llm.chat([
                {"role": "user", "content": prompt}
            ], temperature=0.3)

            result_text = response.get("content", "[]")

            import json
            match = re.search(r'\[[\s\S]*\]', result_text)
            if match:
                return json.loads(match.group())
            return []
        except Exception as e:
            logger.error(f"角色分析失败: {e}")
            return []

    async def _analyze_style(self, content: str) -> Dict[str, Any]:
        """分析文风"""
        prompt = f"""请分析以下小说片段的文风特点。

{content}

请以 JSON 格式输出文风分析，包含：
- narrative_distance: 叙事距离（"close"近距离/第一人称、"medium"中距离/有限第三人称、"far"远距离/全知视角）
- pacing: 叙事节奏（"fast"快节奏、"moderate"中等、"slow"慢节奏）
- sentence_style: 句式特点描述
- vocabulary: 常用词汇或表达方式列表（最多5个）
- taboo_words: 作者避免使用的词汇或表达（如果能推断）
- example_passages: 代表性段落（1-2段，用于展示文风）

只输出 JSON 对象，不要其他内容：
{{
  "narrative_distance": "...",
  "pacing": "...",
  "sentence_style": "...",
  "vocabulary": ["...", "..."],
  "taboo_words": [],
  "example_passages": ["..."]
}}"""

        try:
            response = await self.llm.chat([
                {"role": "user", "content": prompt}
            ], temperature=0.3)

            result_text = response.get("content", "{}")

            import json
            match = re.search(r'\{[\s\S]*\}', result_text)
            if match:
                return json.loads(match.group())
            return {}
        except Exception as e:
            logger.error(f"文风分析失败: {e}")
            return {}


class ImportService:
    """导入服务 - 整合解析和分析功能"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            from app.config import get_config
            config = get_config()
            data_dir = str(config.data_dir)

        self.data_dir = data_dir
        self.parser = NovelParser()
        self.analyzer = NovelAnalyzer()

    async def import_novel(
        self,
        filename: str,
        content: bytes,
        project_name: Optional[str] = None,
        analyze: bool = True
    ) -> Dict[str, Any]:
        """
        导入小说

        Args:
            filename: 文件名
            content: 文件内容
            project_name: 项目名（可选，默认使用文件名）
            analyze: 是否进行 AI 分析

        Returns:
            导入结果，包含项目信息、章节列表、分析结果
        """
        # 1. 解析小说
        novel = self.parser.parse(filename, content)

        if project_name:
            novel.title = project_name

        # 2. AI 分析（可选）
        analysis = None
        if analyze and novel.chapters:
            try:
                analysis = await self.analyzer.analyze(novel)
            except Exception as e:
                logger.error(f"AI 分析失败: {e}")
                # 分析失败不影响导入

        return {
            "novel": {
                "title": novel.title,
                "author": novel.author,
                "description": novel.description,
                "total_words": novel.total_words,
                "chapter_count": len(novel.chapters)
            },
            "chapters": [
                {
                    "chapter_name": ch.chapter_name,
                    "title": ch.title,
                    "word_count": ch.word_count,
                    "content": ch.content
                }
                for ch in novel.chapters
            ],
            "analysis": {
                "world_settings": analysis.world_settings if analysis else [],
                "characters": analysis.characters if analysis else [],
                "style": analysis.style if analysis else {}
            } if analysis else None
        }


def get_import_service() -> ImportService:
    """获取导入服务实例"""
    return ImportService()

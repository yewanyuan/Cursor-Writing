"""
导出服务
支持导出整本小说为 TXT / Markdown / EPUB 格式
"""

import io
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.storage import ProjectStorage, DraftStorage


class ExportFormat(str, Enum):
    TXT = "txt"
    MARKDOWN = "markdown"
    EPUB = "epub"


@dataclass
class ChapterContent:
    """章节内容"""
    chapter: str
    title: str
    content: str
    word_count: int


@dataclass
class ExportResult:
    """导出结果"""
    filename: str
    content: bytes
    content_type: str
    total_words: int
    chapter_count: int


class ExportService:
    """导出服务"""

    def __init__(self, data_dir: str = "../data"):
        self.projects = ProjectStorage(data_dir)
        self.drafts = DraftStorage(data_dir)

    async def get_all_chapters(self, project_id: str, use_final: bool = True) -> List[ChapterContent]:
        """
        获取项目的所有章节内容

        Args:
            project_id: 项目 ID
            use_final: True 使用成稿，False 使用最新草稿

        Returns:
            章节内容列表（已排序）
        """
        chapters = await self.drafts.list_chapters(project_id)
        result = []

        for chapter in chapters:
            content = None

            if use_final:
                # 优先使用成稿
                content = await self.drafts.get_final(project_id, chapter)

            if content is None:
                # 没有成稿则使用最新草稿
                draft = await self.drafts.get_latest_draft(project_id, chapter)
                if draft:
                    content = draft.content

            if content:
                # 获取章节摘要中的标题（如果有）
                summary = await self.drafts.get_summary(project_id, chapter)
                title = ""
                if summary and hasattr(summary, 'title'):
                    title = summary.title or ""

                result.append(ChapterContent(
                    chapter=chapter,
                    title=title,
                    content=content,
                    word_count=len(content)
                ))

        return result

    async def export_txt(self, project_id: str, use_final: bool = True) -> ExportResult:
        """导出为 TXT 格式"""
        project = await self.projects.get_project(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        chapters = await self.get_all_chapters(project_id, use_final)

        lines = []

        # 标题
        lines.append(project.name)
        lines.append("=" * 40)
        lines.append("")

        # 简介（如果有）
        if project.description:
            lines.append(project.description)
            lines.append("")
            lines.append("-" * 40)
            lines.append("")

        # 章节内容
        total_words = 0
        for ch in chapters:
            # 章节标题
            if ch.title:
                lines.append(f"{ch.chapter} {ch.title}")
            else:
                lines.append(ch.chapter)
            lines.append("")

            # 正文
            lines.append(ch.content)
            lines.append("")
            lines.append("")

            total_words += ch.word_count

        content = "\n".join(lines)

        return ExportResult(
            filename=f"{project.name}.txt",
            content=content.encode("utf-8"),
            content_type="text/plain; charset=utf-8",
            total_words=total_words,
            chapter_count=len(chapters)
        )

    async def export_markdown(self, project_id: str, use_final: bool = True) -> ExportResult:
        """导出为 Markdown 格式"""
        project = await self.projects.get_project(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        chapters = await self.get_all_chapters(project_id, use_final)

        lines = []

        # 标题
        lines.append(f"# {project.name}")
        lines.append("")

        # 简介
        if project.description:
            lines.append(f"> {project.description}")
            lines.append("")

        # 目录
        lines.append("## 目录")
        lines.append("")
        for i, ch in enumerate(chapters, 1):
            anchor = ch.chapter.replace(" ", "-").lower()
            if ch.title:
                lines.append(f"{i}. [{ch.chapter} {ch.title}](#{anchor})")
            else:
                lines.append(f"{i}. [{ch.chapter}](#{anchor})")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 章节内容
        total_words = 0
        for ch in chapters:
            # 章节标题
            if ch.title:
                lines.append(f"## {ch.chapter} {ch.title}")
            else:
                lines.append(f"## {ch.chapter}")
            lines.append("")

            # 正文（按段落处理）
            paragraphs = ch.content.split("\n")
            for para in paragraphs:
                para = para.strip()
                if para:
                    lines.append(para)
                    lines.append("")

            lines.append("---")
            lines.append("")

            total_words += ch.word_count

        content = "\n".join(lines)

        return ExportResult(
            filename=f"{project.name}.md",
            content=content.encode("utf-8"),
            content_type="text/markdown; charset=utf-8",
            total_words=total_words,
            chapter_count=len(chapters)
        )

    async def export_epub(self, project_id: str, use_final: bool = True) -> ExportResult:
        """
        导出为 EPUB 格式

        EPUB 本质上是一个 ZIP 文件，包含：
        - mimetype
        - META-INF/container.xml
        - OEBPS/content.opf
        - OEBPS/toc.ncx
        - OEBPS/chapter_*.xhtml
        """
        project = await self.projects.get_project(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        chapters = await self.get_all_chapters(project_id, use_final)

        # 创建内存中的 ZIP 文件
        epub_buffer = io.BytesIO()

        with zipfile.ZipFile(epub_buffer, 'w', zipfile.ZIP_DEFLATED) as epub:
            # 1. mimetype (必须是第一个文件，且不压缩)
            epub.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

            # 2. META-INF/container.xml
            container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
            epub.writestr("META-INF/container.xml", container_xml)

            # 3. OEBPS/content.opf
            content_opf = self._generate_content_opf(project, chapters)
            epub.writestr("OEBPS/content.opf", content_opf)

            # 4. OEBPS/toc.ncx
            toc_ncx = self._generate_toc_ncx(project, chapters)
            epub.writestr("OEBPS/toc.ncx", toc_ncx)

            # 5. OEBPS/style.css
            style_css = self._generate_style_css()
            epub.writestr("OEBPS/style.css", style_css)

            # 6. OEBPS/title.xhtml (封面页)
            title_xhtml = self._generate_title_page(project)
            epub.writestr("OEBPS/title.xhtml", title_xhtml)

            # 7. OEBPS/chapter_*.xhtml (章节内容)
            total_words = 0
            for i, ch in enumerate(chapters):
                chapter_xhtml = self._generate_chapter_xhtml(ch, i + 1)
                epub.writestr(f"OEBPS/chapter_{i+1:03d}.xhtml", chapter_xhtml)
                total_words += ch.word_count

        epub_buffer.seek(0)

        return ExportResult(
            filename=f"{project.name}.epub",
            content=epub_buffer.read(),
            content_type="application/epub+zip",
            total_words=total_words,
            chapter_count=len(chapters)
        )

    def _generate_content_opf(self, project, chapters: List[ChapterContent]) -> str:
        """生成 content.opf"""
        from datetime import datetime

        manifest_items = [
            '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
            '<item id="style" href="style.css" media-type="text/css"/>',
            '<item id="title" href="title.xhtml" media-type="application/xhtml+xml"/>',
        ]

        spine_items = ['<itemref idref="title"/>']

        for i, ch in enumerate(chapters):
            item_id = f"chapter_{i+1:03d}"
            manifest_items.append(
                f'<item id="{item_id}" href="chapter_{i+1:03d}.xhtml" media-type="application/xhtml+xml"/>'
            )
            spine_items.append(f'<itemref idref="{item_id}"/>')

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="BookId">urn:uuid:{project.id}</dc:identifier>
    <dc:title>{self._escape_xml(project.name)}</dc:title>
    <dc:language>zh-CN</dc:language>
    <dc:creator>Cursor-Writing</dc:creator>
    <dc:date>{datetime.now().strftime("%Y-%m-%d")}</dc:date>
    {f'<dc:description>{self._escape_xml(project.description)}</dc:description>' if project.description else ''}
  </metadata>
  <manifest>
    {chr(10).join(manifest_items)}
  </manifest>
  <spine toc="ncx">
    {chr(10).join(spine_items)}
  </spine>
</package>'''

    def _generate_toc_ncx(self, project, chapters: List[ChapterContent]) -> str:
        """生成 toc.ncx (目录)"""
        nav_points = []

        # 封面
        nav_points.append(f'''    <navPoint id="title" playOrder="1">
      <navLabel><text>封面</text></navLabel>
      <content src="title.xhtml"/>
    </navPoint>''')

        # 章节
        for i, ch in enumerate(chapters):
            title = f"{ch.chapter} {ch.title}" if ch.title else ch.chapter
            nav_points.append(f'''    <navPoint id="chapter_{i+1:03d}" playOrder="{i+2}">
      <navLabel><text>{self._escape_xml(title)}</text></navLabel>
      <content src="chapter_{i+1:03d}.xhtml"/>
    </navPoint>''')

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:{project.id}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{self._escape_xml(project.name)}</text></docTitle>
  <navMap>
{chr(10).join(nav_points)}
  </navMap>
</ncx>'''

    def _generate_style_css(self) -> str:
        """生成样式表"""
        return '''body {
    font-family: "Source Han Serif CN", "Noto Serif CJK SC", serif;
    line-height: 1.8;
    margin: 1em;
    text-align: justify;
}

h1 {
    font-size: 2em;
    text-align: center;
    margin: 2em 0 1em 0;
}

h2 {
    font-size: 1.5em;
    margin: 1.5em 0 1em 0;
    border-bottom: 1px solid #ccc;
    padding-bottom: 0.3em;
}

p {
    text-indent: 2em;
    margin: 0.5em 0;
}

.title-page {
    text-align: center;
    padding-top: 30%;
}

.title-page h1 {
    font-size: 2.5em;
    margin-bottom: 1em;
}

.title-page .description {
    font-style: italic;
    color: #666;
    margin-top: 2em;
}
'''

    def _generate_title_page(self, project) -> str:
        """生成封面页"""
        desc = f'<p class="description">{self._escape_xml(project.description)}</p>' if project.description else ''

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN">
<head>
    <meta charset="UTF-8"/>
    <title>{self._escape_xml(project.name)}</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="title-page">
        <h1>{self._escape_xml(project.name)}</h1>
        {desc}
    </div>
</body>
</html>'''

    def _generate_chapter_xhtml(self, chapter: ChapterContent, index: int) -> str:
        """生成章节 XHTML"""
        title = f"{chapter.chapter} {chapter.title}" if chapter.title else chapter.chapter

        # 将内容转换为段落
        paragraphs = []
        for line in chapter.content.split("\n"):
            line = line.strip()
            if line:
                paragraphs.append(f"<p>{self._escape_xml(line)}</p>")

        content = "\n".join(paragraphs)

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN">
<head>
    <meta charset="UTF-8"/>
    <title>{self._escape_xml(title)}</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <h2>{self._escape_xml(title)}</h2>
    {content}
</body>
</html>'''

    def _escape_xml(self, text: str) -> str:
        """转义 XML 特殊字符"""
        if not text:
            return ""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))

    async def export(
        self,
        project_id: str,
        format: ExportFormat,
        use_final: bool = True
    ) -> ExportResult:
        """
        导出项目

        Args:
            project_id: 项目 ID
            format: 导出格式
            use_final: 是否使用成稿（否则用最新草稿）

        Returns:
            导出结果
        """
        if format == ExportFormat.TXT:
            return await self.export_txt(project_id, use_final)
        elif format == ExportFormat.MARKDOWN:
            return await self.export_markdown(project_id, use_final)
        elif format == ExportFormat.EPUB:
            return await self.export_epub(project_id, use_final)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

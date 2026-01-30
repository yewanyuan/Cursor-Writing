"""
导出 API
"""

from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional

from app.services.exporter import ExportService, ExportFormat

router = APIRouter()

_exporter = None


def get_exporter() -> ExportService:
    global _exporter
    if _exporter is None:
        _exporter = ExportService("../data")
    return _exporter


class ExportRequest(BaseModel):
    format: str = "txt"  # txt, markdown, epub
    use_final: bool = True  # True: 使用成稿, False: 使用最新草稿


class ExportInfo(BaseModel):
    """导出信息（不含实际内容）"""
    total_words: int
    chapter_count: int
    available_formats: list


@router.get("/{project_id}/info")
async def get_export_info(project_id: str) -> ExportInfo:
    """获取可导出的信息"""
    exporter = get_exporter()

    try:
        chapters = await exporter.get_all_chapters(project_id)

        total_words = sum(ch.word_count for ch in chapters)

        return ExportInfo(
            total_words=total_words,
            chapter_count=len(chapters),
            available_formats=["txt", "markdown", "epub"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}")
async def export_project(project_id: str, req: ExportRequest):
    """
    导出项目

    返回文件下载响应
    """
    exporter = get_exporter()

    # 转换格式
    try:
        format_enum = ExportFormat(req.format.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的格式: {req.format}，支持: txt, markdown, epub"
        )

    try:
        result = await exporter.export(project_id, format_enum, req.use_final)

        # 设置文件名（处理中文 - 使用 URL 编码）
        filename = result.filename
        encoded_filename = quote(filename)

        return Response(
            content=result.content,
            media_type=result.content_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "X-Total-Words": str(result.total_words),
                "X-Chapter-Count": str(result.chapter_count)
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/preview")
async def preview_export(
    project_id: str,
    format: str = "txt",
    use_final: bool = True,
    max_chars: int = 5000
):
    """
    预览导出内容（仅返回前 N 个字符）
    """
    exporter = get_exporter()

    try:
        format_enum = ExportFormat(format.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的格式: {format}"
        )

    try:
        result = await exporter.export(project_id, format_enum, use_final)

        # 解码内容
        if format_enum == ExportFormat.EPUB:
            # EPUB 是二进制，不支持预览
            return {
                "preview": "[EPUB 文件不支持预览]",
                "total_words": result.total_words,
                "chapter_count": result.chapter_count,
                "truncated": False
            }

        content = result.content.decode('utf-8')
        truncated = len(content) > max_chars

        return {
            "preview": content[:max_chars],
            "total_words": result.total_words,
            "chapter_count": result.chapter_count,
            "truncated": truncated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

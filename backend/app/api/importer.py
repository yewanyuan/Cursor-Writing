"""
小说导入 API
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.services.importer import get_import_service, ImportFormat
from app.storage import ProjectStorage, DraftStorage, CardStorage
from app.models.draft import Draft
from app.models.project import ProjectCreate
from app.models.card import WorldCard, CharacterCard, StyleCard

router = APIRouter()

_project_storage = None
_draft_storage = None
_card_storage = None


def get_project_storage() -> ProjectStorage:
    global _project_storage
    if _project_storage is None:
        _project_storage = ProjectStorage("../data")
    return _project_storage


def get_draft_storage() -> DraftStorage:
    global _draft_storage
    if _draft_storage is None:
        _draft_storage = DraftStorage("../data")
    return _draft_storage


def get_card_storage() -> CardStorage:
    global _card_storage
    if _card_storage is None:
        _card_storage = CardStorage("../data")
    return _card_storage


class ImportResponse(BaseModel):
    """导入响应"""
    success: bool
    project_id: str = ""
    message: str = ""
    novel_title: str = ""
    author: str = ""
    chapter_count: int = 0
    total_words: int = 0
    analysis_done: bool = False


class ParsePreviewResponse(BaseModel):
    """解析预览响应（不创建项目）"""
    success: bool
    title: str = ""
    author: str = ""
    description: str = ""
    chapter_count: int = 0
    total_words: int = 0
    chapters: list = []  # [{chapter_name, title, word_count}]
    message: str = ""


@router.post("/preview", response_model=ParsePreviewResponse)
async def preview_import(
    file: UploadFile = File(...),
):
    """
    预览导入结果（不实际创建项目）
    用于让用户确认章节分解是否正确
    """
    try:
        content = await file.read()
        filename = file.filename or "unknown.txt"

        import_service = get_import_service()
        # 只解析，不进行 AI 分析
        result = await import_service.import_novel(
            filename=filename,
            content=content,
            analyze=False
        )

        return ParsePreviewResponse(
            success=True,
            title=result["novel"]["title"],
            author=result["novel"]["author"],
            description=result["novel"]["description"],
            chapter_count=result["novel"]["chapter_count"],
            total_words=result["novel"]["total_words"],
            chapters=[
                {
                    "chapter_name": ch["chapter_name"],
                    "title": ch["title"],
                    "word_count": ch["word_count"]
                }
                for ch in result["chapters"]
            ]
        )

    except Exception as e:
        return ParsePreviewResponse(
            success=False,
            message=f"解析失败: {str(e)}"
        )


@router.post("/import", response_model=ImportResponse)
async def import_novel(
    file: UploadFile = File(...),
    project_name: Optional[str] = Form(None),
    genre: Optional[str] = Form(None),
    analyze: bool = Form(True),
):
    """
    导入小说文件，创建项目并生成章节

    Args:
        file: 上传的文件（支持 TXT、Markdown、EPUB、PDF）
        project_name: 项目名称（可选，默认使用文件名）
        genre: 小说类型（可选）
        analyze: 是否进行 AI 分析（默认 True）
    """
    try:
        content = await file.read()
        filename = file.filename or "unknown.txt"

        # 1. 解析小说
        import_service = get_import_service()
        result = await import_service.import_novel(
            filename=filename,
            content=content,
            project_name=project_name,
            analyze=analyze
        )

        novel_info = result["novel"]
        chapters = result["chapters"]
        analysis = result.get("analysis")

        # 2. 创建项目
        project_storage = get_project_storage()
        project_data = ProjectCreate(
            name=project_name or novel_info["title"],
            genre=genre or "导入小说",
            description=novel_info.get("description", ""),
        )
        project = await project_storage.create_project(project_data)
        project_id = project.id

        # 3. 保存章节为草稿（设为 final 状态）
        draft_storage = get_draft_storage()
        for idx, chapter in enumerate(chapters):
            # 创建 Draft 对象
            draft = Draft(
                chapter=chapter["chapter_name"],
                version=f"v1",
                content=chapter["content"],
                word_count=chapter["word_count"],
            )
            await draft_storage.save_draft(project_id, draft)
            # 同时保存为 final
            await draft_storage.save_final(project_id, chapter["chapter_name"], chapter["content"])

        # 4. 如果有 AI 分析结果，保存到设定卡片
        if analysis:
            card_storage = get_card_storage()

            # 保存世界观设定
            for setting in analysis.get("world_settings", []):
                world_card = WorldCard(
                    name=setting.get("name", "未命名设定"),
                    category=setting.get("category", "其他"),
                    description=setting.get("description", "")
                )
                await card_storage.save_world_card(project_id, world_card)

            # 保存角色信息
            for char in analysis.get("characters", []):
                char_card = CharacterCard(
                    name=char.get("name", "未命名角色"),
                    identity=char.get("identity", ""),
                    personality=char.get("personality", []),
                    speech_pattern=char.get("speech_pattern", "")
                )
                await card_storage.save_character(project_id, char_card)

            # 保存文风设定
            style = analysis.get("style", {})
            if style:
                style_card = StyleCard(
                    narrative_distance=style.get("narrative_distance", "medium"),
                    pacing=style.get("pacing", "moderate"),
                    sentence_style=style.get("sentence_style", ""),
                    vocabulary=style.get("vocabulary", []),
                    taboo_words=style.get("taboo_words", []),
                    example_passages=style.get("example_passages", [])
                )
                await card_storage.save_style(project_id, style_card)

        return ImportResponse(
            success=True,
            project_id=project_id,
            novel_title=novel_info["title"],
            author=novel_info.get("author", ""),
            chapter_count=len(chapters),
            total_words=novel_info["total_words"],
            analysis_done=analysis is not None,
            message=f"成功导入 {len(chapters)} 章，共 {novel_info['total_words']} 字"
            + ("，已完成 AI 分析" if analysis else "")
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"导入失败: {str(e)}")


@router.get("/formats")
async def get_supported_formats():
    """获取支持的导入格式"""
    return {
        "formats": [
            {"value": "txt", "label": "纯文本 (.txt)", "extensions": [".txt"]},
            {"value": "markdown", "label": "Markdown (.md)", "extensions": [".md", ".markdown"]},
            {"value": "epub", "label": "EPUB 电子书 (.epub)", "extensions": [".epub"]},
            {"value": "pdf", "label": "PDF 文档 (.pdf)", "extensions": [".pdf"]},
        ]
    }

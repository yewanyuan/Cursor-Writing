from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from openai import OpenAI
import os
from typing import Optional
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(dotenv_path="../.env")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cursor Writing API", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="../../frontend"), name="static")

# API 配置
api_key = os.getenv("OPENAI_API_KEY")
client = None

if api_key:
    # 初始化OpenAI客户端
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/beta"  # FIM（Fill-In-the-Middle）补全 API
    )
    logger.info("DeepSeek API client initialized successfully")
    logger.info("Using base_url: https://api.deepseek.com/beta")
else:
    logger.warning("API key not found in environment variables")

# 请求
class AIRequest(BaseModel):
    text: str
    context: Optional[str] = None

# 响应
class AIResponse(BaseModel):
    content: str
    model: str
    usage: dict

# 检查API客户端
def check_api_client():
    if not client:
        raise HTTPException(
            status_code=500,
            detail="DeepSeek API client not configured. Please set OPENAI_API_KEY environment variable."
        )
    return True

@app.get("/")
async def root():
    """根路径重定向到编辑器"""
    return RedirectResponse(url="/static/index.html")

@app.get("/health")
async def health_check():
    """检查端点"""
    return {"status": "healthy", "service": "text-editor-api"}

@app.post("/api/ai/complete", response_model=AIResponse)
async def ai_complete(request: AIRequest, _: bool = Depends(check_api_client)):
    """
    AI文本补全功能
    根据给定的文本和上下文，合理生成补全内容
    """
    try:
        # 构建prompt
        if request.context:
            prompt = f"""作为一个智能写作和编程助手，请根据以下上下文和当前光标位置的文本，生成合适的文本补全。

文档上下文：
{request.context}

需要补全的文本：
{request.text}

请对选中的文本进行补全，要求：
1. 保持原有的核心思想和逻辑
2. 根据合理的想象力撰写选中文本之后的内容
3. 尽可能去续写接下来的情节发展，或补充前文内容
4. 确保补全后的内容逻辑与上下文保持一致
5. 重要：不要直接复制或照抄文档上下文中紧邻选中文本之后的内容
6. 要生成原创的、具有衔接性的新内容，而不是重复已存在的文字

只返回补全的内容，不要包含解释或多余的文字。"""
        else:
            prompt = f"""作为一个智能写作和编程助手，请为以下文本生成合适的补全内容：

{request.text}

请对这段文本进行补全，要求：
1. 保持原有的核心思想
2. 续写或补充更多内容和深度
3. 增加文本内容表达的可读性和趣味性
4. 如果是代码，请改进结构和添加注释
5. 生成原创的、具有衔接性的新内容，避免简单重复输入文本

只返回补全后的内容，不要包含额外的解释。"""

        # 调用 DeepSeek API
        response = client.chat.completions.create(
            model="deepseek-chat",  # 备选模型 deepseek-reasoner
            messages=[
                {"role": "system", "content": "你是一个专业的文本补全助手，专注于续写给定的文本内容。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )

        content = response.choices[0].message.content.strip()
        
        return AIResponse(
            content=content,
            model=response.model,
            usage=response.usage.model_dump()
        )

    except Exception as e:
        logger.error(f"Error in AI completion: {e}")
        raise HTTPException(status_code=500, detail=f"AI completion failed: {str(e)}")

@app.post("/api/ai/expand", response_model=AIResponse)
async def ai_expand(request: AIRequest, _: bool = Depends(check_api_client)):
    """
    AI文本扩写功能
    根据给定的文本，合理生成扩展和改进的版本
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text to expand cannot be empty")

        # 构建提示词
        if request.context:
            prompt = f"""作为一个专业的写作和编程助手，请根据以下上下文，对选中的文本进行扩写和改进。

完整文档上下文：
{request.context}

需要扩写的文本：
{request.text}

请对选中的文本进行扩写，要求：
1. 保持原有的核心思想和逻辑
2. 增加更多细节、解释或实现
3. 改进代码结构或文档的清晰度
4. 确保扩写后的内容与上下文保持一致

只返回扩写后的内容，不要包含额外的解释。"""
        else:
            prompt = f"""作为一个专业的写作和编程助手，请对以下文本进行扩写和改进：

{request.text}

请对这段文本进行扩写，要求：
1. 保持原有的核心思想
2. 增加更多细节和深度
3. 改进表达的清晰度和完整性
4. 如果是代码，请改进结构和添加注释

只返回扩写后的内容，不要包含额外的解释。"""

        # 调用 DeepSeek API
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的文本扩写助手，专注于改进和扩展给定的文本内容。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.4,
            top_p=1.0,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )

        content = response.choices[0].message.content.strip()
        
        return AIResponse(
            content=content,
            model=response.model,
            usage=response.usage.model_dump()
        )

    except Exception as e:
        logger.error(f"Error in AI expansion: {e}")
        raise HTTPException(status_code=500, detail=f"AI expansion failed: {str(e)}")


# 错误处理器
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": "The requested resource was not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "An internal server error occurred"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
"""
自定义异常类 (Custom Exceptions)
细粒度的错误处理
"""


class CursorWritingError(Exception):
    """基础异常类"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class LLMError(CursorWritingError):
    """LLM 调用相关错误"""

    def __init__(self, message: str, provider: str = None, details: dict = None):
        super().__init__(message, details)
        self.provider = provider


class StorageError(CursorWritingError):
    """存储操作错误"""

    def __init__(self, message: str, path: str = None, details: dict = None):
        super().__init__(message, details)
        self.path = path


class ValidationError(CursorWritingError):
    """数据验证错误"""

    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(message, details)
        self.field = field


class AgentError(CursorWritingError):
    """Agent 执行错误"""

    def __init__(self, message: str, agent_name: str = None, details: dict = None):
        super().__init__(message, details)
        self.agent_name = agent_name


class SessionError(CursorWritingError):
    """会话错误"""

    def __init__(self, message: str, status: str = None, details: dict = None):
        super().__init__(message, details)
        self.status = status

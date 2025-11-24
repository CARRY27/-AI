"""
配置管理模块
从环境变量加载所有配置项
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # ========== 应用配置 ==========
    APP_NAME: str = "DocAgent"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    
    # ========== API 配置 ==========
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    API_WORKERS: int = Field(default=4)
    
    # ========== CORS 配置 ==========
    FRONTEND_URL: str = Field(default="http://localhost:5173")
    CORS_ORIGINS: str = Field(default="http://localhost:5173,http://localhost:3000")
    
    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        """将CORS_ORIGINS字符串转换为列表"""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if isinstance(self.CORS_ORIGINS, str):
            # 支持逗号分隔
            return [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]
        return ["http://localhost:5173", "http://localhost:3000"]
    
    # ========== 数据库配置 ==========
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="docagent")
    POSTGRES_USER: str = Field(default="docagent")
    POSTGRES_PASSWORD: str = Field(default="docagent_password")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # ========== Redis 配置 ==========
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_DB: int = Field(default=0)
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ========== 对象存储配置 ==========
    S3_ENDPOINT: str = Field(default="http://localhost:9000")
    S3_ACCESS_KEY: str = Field(default="minioadmin")
    S3_SECRET_KEY: str = Field(default="minioadmin")
    S3_BUCKET: str = Field(default="docagent-files")
    S3_REGION: str = Field(default="us-east-1")
    S3_USE_SSL: bool = Field(default=False)
    
    # ========== 向量数据库配置 ==========
    VECTOR_DB_TYPE: str = Field(default="faiss")  # faiss, milvus, chroma
    VECTOR_DB_PATH: str = Field(default="/app/data/faiss_index")
    
    # Milvus
    MILVUS_HOST: str = Field(default="localhost")
    MILVUS_PORT: int = Field(default=19530)
    MILVUS_COLLECTION: str = Field(default="docagent_vectors")
    
    # ========== LLM 配置 ==========
    LLM_PROVIDER: str = Field(default="openai")  # openai, azure, ollama, tongyi
    LLM_MODEL: str = Field(default="gpt-4o-mini")
    LLM_TEMPERATURE: float = Field(default=0.1)
    LLM_MAX_TOKENS: int = Field(default=2000)
    
    # OpenAI
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1")
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None)
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None)
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = Field(default=None)
    
    # Ollama
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="llama2")
    
    # 通义千问 (Tongyi Qwen)
    TONGYI_API_KEY: str = Field(default="")
    TONGYI_MODEL: str = Field(default="qwen-turbo")  # qwen-turbo, qwen-plus, qwen-max
    
    # ========== Embedding 配置 ==========
    EMBEDDING_PROVIDER: str = Field(default="openai")
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-small")
    EMBEDDING_DIMENSION: int = Field(default=1536)
    EMBEDDING_BATCH_SIZE: int = Field(default=100)
    
    # ========== 检索配置 ==========
    RETRIEVAL_TOP_N: int = Field(default=20)
    RETRIEVAL_TOP_K: int = Field(default=5)
    SIMILARITY_THRESHOLD: float = Field(default=0.75)
    USE_RERANKER: bool = Field(default=True)
    RERANKER_MODEL: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2")
    
    # ========== 文档处理配置 ==========
    CHUNK_SIZE: int = Field(default=800)
    CHUNK_OVERLAP: int = Field(default=200)
    MAX_FILE_SIZE_MB: int = Field(default=50)
    ALLOWED_FILE_TYPES: str = Field(default="pdf,docx,txt,html,xlsx,pptx,md")
    
    @property
    def ALLOWED_FILE_TYPES_LIST(self) -> List[str]:
        """将ALLOWED_FILE_TYPES字符串转换为列表"""
        if isinstance(self.ALLOWED_FILE_TYPES, list):
            return self.ALLOWED_FILE_TYPES
        if isinstance(self.ALLOWED_FILE_TYPES, str):
            return [ft.strip() for ft in self.ALLOWED_FILE_TYPES.split(',') if ft.strip()]
        return ["pdf", "docx", "txt", "html", "xlsx", "pptx", "md"]
    
    # ========== JWT 配置 ==========
    JWT_SECRET_KEY: str = Field(default="your-super-secret-jwt-key-change-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRE_MINUTES: int = Field(default=1440)  # 24小时
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # ========== 限流配置 ==========
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_PER_HOUR: int = Field(default=1000)
    
    # ========== 日志配置 ==========
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")
    
    # ========== 监控配置 ==========
    ENABLE_METRICS: bool = Field(default=True)
    METRICS_PORT: int = Field(default=9090)
    
    # ========== Celery 配置 ==========
    CELERY_BROKER_URL: Optional[str] = Field(default=None)
    CELERY_RESULT_BACKEND: Optional[str] = Field(default=None)
    
    @property
    def CELERY_BROKER(self) -> str:
        if self.CELERY_BROKER_URL:
            return self.CELERY_BROKER_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"
    
    @property
    def CELERY_BACKEND(self) -> str:
        if self.CELERY_RESULT_BACKEND:
            return self.CELERY_RESULT_BACKEND
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/2"
    
    # ========== 功能开关 ==========
    ENABLE_RERANKER: bool = Field(default=True)
    ENABLE_AUDIT_LOG: bool = Field(default=True)
    ENABLE_FILE_ENCRYPTION: bool = Field(default=False)
    ENABLE_PII_DETECTION: bool = Field(default=False)
    
    # ========== 知识更新配置 ==========
    REFRESH_INTERVAL_HOURS: int = Field(default=24)  # 文档刷新间隔（小时）
    ENABLE_AUTO_REFRESH: bool = Field(default=False)  # 是否启用自动刷新
    INCREMENTAL_UPDATE_THRESHOLD: float = Field(default=0.5)  # 增量更新阈值
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()


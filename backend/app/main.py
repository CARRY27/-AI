"""
FastAPI 应用主入口
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from app.config import settings
from app.api import router
from app.database.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 正在启动...")
    print(f"📝 环境: {settings.ENVIRONMENT}")
    print(f"🔗 数据库: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    print(f"🔗 Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    print(f"🤖 LLM: {settings.LLM_PROVIDER} - {settings.LLM_MODEL}")
    
    # 初始化数据库
    await init_db()
    
    yield
    
    # 关闭时执行
    print(f"👋 {settings.APP_NAME} 正在关闭...")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="企业级文档问答系统 - 基于 RAG 技术",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ========== 中间件配置 ==========

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip 压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ========== 请求处理中间件 ==========

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加请求处理时间到响应头"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求"""
    print(f"📥 {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"📤 {request.method} {request.url.path} - {response.status_code}")
    return response


# ========== 异常处理 ==========

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    print(f"❌ 错误: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else None
        }
    )


# ========== 路由注册 ==========

# 健康检查
@app.get("/health", tags=["监控"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# 根路径
@app.get("/", tags=["根"])
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用 {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


# 注册所有 API 路由
app.include_router(router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        workers=settings.API_WORKERS if not settings.DEBUG else 1
    )


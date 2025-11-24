"""
模型调度器 (Model Orchestrator)
支持多模型、fallback机制、rate limiter
"""

from typing import Dict, List, Optional, Any, AsyncGenerator
from enum import Enum
import time
import asyncio
from datetime import datetime, timedelta

import openai
from app.config import settings
from app.services.cache_service import cache_service


class ModelProvider(str, Enum):
    """模型提供商"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    CLAUDE = "claude"
    TONGYI = "tongyi"  # 通义千问
    OLLAMA = "ollama"


class TaskType(str, Enum):
    """任务类型"""
    QA = "qa"  # 问答
    SUMMARIZATION = "summarization"  # 摘要
    EXTRACTION = "extraction"  # 提取
    TRANSLATION = "translation"  # 翻译
    GENERAL = "general"  # 通用


class ModelConfig:
    """模型配置"""
    
    def __init__(
        self,
        provider: ModelProvider,
        model_name: str,
        api_key: str,
        api_base: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.1,
        priority: int = 1,  # 优先级，数字越小优先级越高
        rate_limit_per_minute: int = 60,
        timeout: int = 30
    ):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.api_base = api_base
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.priority = priority
        self.rate_limit_per_minute = rate_limit_per_minute
        self.timeout = timeout
        
        # 运行时状态
        self.is_available = True
        self.error_count = 0
        self.last_error_time = None


class ModelOrchestrator:
    """模型调度器"""
    
    def __init__(self):
        self.models: Dict[TaskType, List[ModelConfig]] = {}
        self.call_history: Dict[str, List[float]] = {}  # 用于rate limiting
        
        # 初始化默认模型配置
        self._init_default_models()
    
    def _init_default_models(self):
        """初始化默认模型配置"""
        
        # OpenAI GPT-4 - 高质量问答
        if settings.OPENAI_API_KEY:
            gpt4_config = ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
                api_base=settings.OPENAI_API_BASE,
                max_tokens=2000,
                temperature=0.1,
                priority=1,
                rate_limit_per_minute=60
            )
            
            # GPT-4用于所有任务类型
            for task_type in TaskType:
                if task_type not in self.models:
                    self.models[task_type] = []
                self.models[task_type].append(gpt4_config)
        
        # 通义千问 - 中文优化
        if settings.TONGYI_API_KEY:
            tongyi_config = ModelConfig(
                provider=ModelProvider.TONGYI,
                model_name=settings.TONGYI_MODEL,
                api_key=settings.TONGYI_API_KEY,
                max_tokens=2000,
                temperature=0.1,
                priority=1,  # 设置为高优先级，优先使用通义千问
                rate_limit_per_minute=60
            )
            
            # 通义千问用于所有任务类型
            for task_type in TaskType:
                if task_type not in self.models:
                    self.models[task_type] = []
                # 插入到列表开头，使其优先于其他模型
                self.models[task_type].insert(0, tongyi_config)
        
        # 可以添加更多模型配置
        # 例如：Claude for summarization, etc.
    
    def register_model(self, task_type: TaskType, model_config: ModelConfig):
        """注册新模型"""
        if task_type not in self.models:
            self.models[task_type] = []
        
        self.models[task_type].append(model_config)
        # 按优先级排序
        self.models[task_type].sort(key=lambda x: x.priority)
    
    def _check_rate_limit(self, model_key: str, rate_limit: int) -> bool:
        """检查是否超过速率限制"""
        now = time.time()
        minute_ago = now - 60
        
        # 清理旧记录
        if model_key in self.call_history:
            self.call_history[model_key] = [
                t for t in self.call_history[model_key] if t > minute_ago
            ]
        else:
            self.call_history[model_key] = []
        
        # 检查是否超限
        if len(self.call_history[model_key]) >= rate_limit:
            return False
        
        # 记录本次调用
        self.call_history[model_key].append(now)
        return True
    
    def _mark_model_error(self, model_config: ModelConfig):
        """标记模型错误"""
        model_config.error_count += 1
        model_config.last_error_time = datetime.utcnow()
        
        # 如果连续错误超过3次，暂时标记为不可用
        if model_config.error_count >= 3:
            model_config.is_available = False
            print(f"⚠️ 模型 {model_config.model_name} 暂时不可用")
    
    def _recover_model(self, model_config: ModelConfig):
        """恢复模型可用性"""
        if not model_config.is_available and model_config.last_error_time:
            # 如果距离上次错误超过5分钟，尝试恢复
            time_since_error = datetime.utcnow() - model_config.last_error_time
            if time_since_error > timedelta(minutes=5):
                model_config.is_available = True
                model_config.error_count = 0
                print(f"✅ 模型 {model_config.model_name} 已恢复")
    
    def _select_model(self, task_type: TaskType) -> Optional[ModelConfig]:
        """选择合适的模型"""
        if task_type not in self.models or not self.models[task_type]:
            return None
        
        # 按优先级尝试选择可用模型
        for model_config in self.models[task_type]:
            # 尝试恢复模型
            self._recover_model(model_config)
            
            # 检查模型是否可用
            if not model_config.is_available:
                continue
            
            # 检查速率限制
            model_key = f"{model_config.provider}:{model_config.model_name}"
            if not self._check_rate_limit(model_key, model_config.rate_limit_per_minute):
                print(f"⚠️ 模型 {model_config.model_name} 达到速率限制")
                continue
            
            return model_config
        
        return None
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        task_type: TaskType = TaskType.GENERAL,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        fallback: bool = True
    ) -> str:
        """
        生成文本（带fallback）
        
        Args:
            messages: 消息列表
            task_type: 任务类型
            temperature: 温度参数（覆盖默认值）
            max_tokens: 最大token数（覆盖默认值）
            fallback: 是否启用fallback
        
        Returns:
            生成的文本
        """
        
        attempted_models = []
        
        while True:
            # 选择模型
            model_config = self._select_model(task_type)
            
            if not model_config:
                if attempted_models:
                    raise Exception(f"所有模型都不可用。已尝试: {attempted_models}")
                else:
                    raise Exception(f"没有可用的模型用于任务类型: {task_type}")
            
            # 避免重复尝试同一模型
            model_key = f"{model_config.provider}:{model_config.model_name}"
            if model_key in attempted_models:
                if fallback and len(attempted_models) < len(self.models.get(task_type, [])):
                    continue
                else:
                    raise Exception(f"所有fallback模型都已尝试失败: {attempted_models}")
            
            attempted_models.append(model_key)
            
            try:
                print(f"🤖 使用模型: {model_config.model_name}")
                
                # 根据provider调用不同的API
                if model_config.provider == ModelProvider.OPENAI:
                    result = await self._call_openai(
                        model_config=model_config,
                        messages=messages,
                        temperature=temperature or model_config.temperature,
                        max_tokens=max_tokens or model_config.max_tokens
                    )
                    
                elif model_config.provider == ModelProvider.AZURE_OPENAI:
                    result = await self._call_azure_openai(
                        model_config=model_config,
                        messages=messages,
                        temperature=temperature or model_config.temperature,
                        max_tokens=max_tokens or model_config.max_tokens
                    )
                    
                elif model_config.provider == ModelProvider.OLLAMA:
                    result = await self._call_ollama(
                        model_config=model_config,
                        messages=messages,
                        temperature=temperature or model_config.temperature,
                        max_tokens=max_tokens or model_config.max_tokens
                    )
                    
                elif model_config.provider == ModelProvider.TONGYI:
                    result = await self._call_tongyi(
                        model_config=model_config,
                        messages=messages,
                        temperature=temperature or model_config.temperature,
                        max_tokens=max_tokens or model_config.max_tokens
                    )
                    
                else:
                    raise Exception(f"不支持的模型提供商: {model_config.provider}")
                
                # 成功，重置错误计数
                model_config.error_count = 0
                
                return result
                
            except Exception as e:
                print(f"❌ 模型 {model_config.model_name} 调用失败: {str(e)}")
                
                # 标记错误
                self._mark_model_error(model_config)
                
                # 如果不启用fallback，直接抛出异常
                if not fallback:
                    raise
                
                # 继续尝试下一个模型
                continue
    
    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        task_type: TaskType = TaskType.GENERAL,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式生成文本
        
        Args:
            messages: 消息列表
            task_type: 任务类型
            temperature: 温度参数
            max_tokens: 最大token数
        
        Yields:
            生成的文本片段
        """
        
        # 选择模型
        model_config = self._select_model(task_type)
        
        if not model_config:
            raise Exception(f"没有可用的模型用于任务类型: {task_type}")
        
        try:
            print(f"🤖 流式使用模型: {model_config.model_name}")
            
            if model_config.provider == ModelProvider.OPENAI:
                async for chunk in self._stream_openai(
                    model_config=model_config,
                    messages=messages,
                    temperature=temperature or model_config.temperature,
                    max_tokens=max_tokens or model_config.max_tokens
                ):
                    yield chunk
            
            elif model_config.provider == ModelProvider.TONGYI:
                async for chunk in self._stream_tongyi(
                    model_config=model_config,
                    messages=messages,
                    temperature=temperature or model_config.temperature,
                    max_tokens=max_tokens or model_config.max_tokens
                ):
                    yield chunk
            
            else:
                raise Exception(f"模型 {model_config.provider} 不支持流式输出")
            
            # 成功，重置错误计数
            model_config.error_count = 0
            
        except Exception as e:
            print(f"❌ 流式生成失败: {str(e)}")
            self._mark_model_error(model_config)
            raise
    
    async def _call_openai(
        self,
        model_config: ModelConfig,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用OpenAI API"""
        
        # 配置OpenAI
        openai.api_key = model_config.api_key
        if model_config.api_base:
            openai.api_base = model_config.api_base
        
        response = await openai.ChatCompletion.acreate(
            model=model_config.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=model_config.timeout
        )
        
        return response.choices[0].message.content
    
    async def _stream_openai(
        self,
        model_config: ModelConfig,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """流式调用OpenAI API"""
        
        openai.api_key = model_config.api_key
        if model_config.api_base:
            openai.api_base = model_config.api_base
        
        response = await openai.ChatCompletion.acreate(
            model=model_config.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=model_config.timeout,
            stream=True
        )
        
        async for chunk in response:
            if chunk.choices[0].delta.get("content"):
                yield chunk.choices[0].delta.content
    
    async def _call_azure_openai(
        self,
        model_config: ModelConfig,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用Azure OpenAI API"""
        
        # Azure OpenAI配置略有不同
        openai.api_type = "azure"
        openai.api_key = model_config.api_key
        openai.api_base = model_config.api_base
        openai.api_version = "2023-05-15"
        
        response = await openai.ChatCompletion.acreate(
            engine=model_config.model_name,  # Azure使用engine而不是model
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=model_config.timeout
        )
        
        return response.choices[0].message.content
    
    async def _call_ollama(
        self,
        model_config: ModelConfig,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用Ollama本地模型"""
        
        import aiohttp
        
        url = f"{model_config.api_base}/api/chat"
        
        # 转换消息格式
        ollama_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
        
        payload = {
            "model": model_config.model_name,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=model_config.timeout)
            ) as response:
                result = await response.json()
                return result["message"]["content"]
    
    async def _call_tongyi(
        self,
        model_config: ModelConfig,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用通义千问 API"""
        
        import dashscope
        from dashscope import Generation
        
        # 设置 API Key
        dashscope.api_key = model_config.api_key
        
        # 转换消息格式
        tongyi_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
        
        # 定义同步调用函数
        def _sync_call():
            return Generation.call(
                model=model_config.model_name,
                messages=tongyi_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                result_format='message'
            )
        
        # 在异步上下文中调用同步函数
        response = await asyncio.to_thread(_sync_call)
        
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            raise Exception(f"通义千问 API 调用失败: {response.message}")
    
    async def _stream_tongyi(
        self,
        model_config: ModelConfig,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """流式调用通义千问 API"""
        
        import dashscope
        from dashscope import Generation
        
        # 设置 API Key
        dashscope.api_key = model_config.api_key
        
        # 转换消息格式
        tongyi_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
        
        # 定义同步流式调用函数，返回生成器
        def _get_stream_generator():
            return Generation.call(
                model=model_config.model_name,
                messages=tongyi_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                result_format='message',
                stream=True,
                incremental_output=True
            )
        
        # 在线程中获取生成器对象
        responses = await asyncio.to_thread(_get_stream_generator)
        
        # 在循环中处理响应，每次迭代后让出控制权
        for response in responses:
            # 让出控制权，允许其他协程运行
            await asyncio.sleep(0)
            
            if response.status_code == 200:
                if hasattr(response.output, 'choices') and len(response.output.choices) > 0:
                    choice = response.output.choices[0]
                    # 检查是否有增量输出
                    if hasattr(choice, 'delta') and hasattr(choice.delta, 'content'):
                        content = choice.delta.content
                        if content:
                            yield content
                    # 或者检查是否有完整消息（某些情况下）
                    elif hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                        content = choice.message.content
                        if content:
                            yield content
            else:
                error_msg = getattr(response, 'message', '未知错误')
                raise Exception(f"通义千问流式 API 调用失败: {error_msg}")
    
    def get_model_stats(self) -> Dict[str, Any]:
        """获取模型统计信息"""
        
        stats = {}
        
        for task_type, models in self.models.items():
            stats[task_type.value] = []
            
            for model in models:
                model_key = f"{model.provider}:{model.model_name}"
                
                # 计算最近一分钟的调用次数
                call_count = len(self.call_history.get(model_key, []))
                
                stats[task_type.value].append({
                    "provider": model.provider.value,
                    "model_name": model.model_name,
                    "priority": model.priority,
                    "is_available": model.is_available,
                    "error_count": model.error_count,
                    "calls_last_minute": call_count,
                    "rate_limit": model.rate_limit_per_minute
                })
        
        return stats


# 全局模型调度器实例
model_orchestrator = ModelOrchestrator()


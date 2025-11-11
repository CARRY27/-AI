"""
Prompt 模板管理模型
支持多角色、参数化配置
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from app.database.session import Base


class PromptTemplate(Base):
    """Prompt 模板表"""
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # 模板基本信息
    name = Column(String(100), nullable=False)  # 模板名称
    description = Column(Text, nullable=True)  # 模板描述
    category = Column(String(50), nullable=False)  # 类别：customer_service, legal, training, general
    
    # 模板内容
    system_prompt = Column(Text, nullable=False)  # 系统提示词
    user_prompt_template = Column(Text, nullable=False)  # 用户提示词模板（支持变量）
    
    # 参数配置
    temperature = Column(Float, default=0.1)  # 温度参数 0-2
    max_tokens = Column(Integer, default=2000)  # 最大token数
    top_p = Column(Float, default=1.0)  # top_p参数
    frequency_penalty = Column(Float, default=0.0)  # 频率惩罚
    presence_penalty = Column(Float, default=0.0)  # 存在惩罚
    
    # 模板变量
    variables = Column(JSONB, default=list)  # 模板中的变量定义
    # 例如: [{"name": "context", "type": "string", "required": true}]
    
    # 示例
    examples = Column(JSONB, default=list)  # Few-shot 示例
    # 例如: [{"input": "...", "output": "..."}]
    
    # 状态管理
    is_active = Column(Boolean, default=True)  # 是否启用
    is_default = Column(Boolean, default=False)  # 是否为默认模板
    version = Column(String(20), default="1.0.0")  # 版本号
    
    # 使用统计
    usage_count = Column(Integer, default=0)  # 使用次数
    success_count = Column(Integer, default=0)  # 成功次数
    average_rating = Column(Float, default=0.0)  # 平均评分
    
    # 创建者
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 元数据
    meta_data = Column(JSONB, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    organization = relationship("Organization", back_populates="prompt_templates")
    creator = relationship("User", back_populates="prompt_templates")
    
    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, name={self.name}, category={self.category})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "variables": self.variables,
            "examples": self.examples,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "version": self.version,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "average_rating": self.average_rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def render(self, **kwargs) -> str:
        """
        渲染模板
        将变量替换为实际值
        """
        prompt = self.user_prompt_template
        
        for var in self.variables:
            var_name = var['name']
            if var_name in kwargs:
                placeholder = f"{{{var_name}}}"
                prompt = prompt.replace(placeholder, str(kwargs[var_name]))
            elif var.get('required', False):
                raise ValueError(f"Required variable '{var_name}' not provided")
        
        return prompt


class PromptTemplateUsageLog(Base):
    """Prompt 模板使用日志"""
    __tablename__ = "prompt_template_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("prompt_templates.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id"))
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    
    # 使用信息
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    
    # 结果
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # 评价
    rating = Column(Integer, nullable=True)  # 1-5
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PromptTemplateUsageLog(id={self.id}, template_id={self.template_id})>"


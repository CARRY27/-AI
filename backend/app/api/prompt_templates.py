"""
Prompt 模板管理 API
支持管理员创建、编辑、管理多种Prompt模板
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database.session import get_db
from app.models.user import User
from app.models.prompt_template import PromptTemplate, PromptTemplateUsageLog
from app.api.auth import get_current_active_user

router = APIRouter()


# ========== Schemas ==========

class PromptTemplateVariable(BaseModel):
    """模板变量定义"""
    name: str
    type: str = "string"  # string, number, boolean
    required: bool = True
    default: Optional[str] = None
    description: Optional[str] = None


class PromptTemplateExample(BaseModel):
    """Few-shot示例"""
    input: str
    output: str


class PromptTemplateCreate(BaseModel):
    """创建Prompt模板"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: str = Field(..., regex="^(customer_service|legal|training|general|technical|sales)$")
    
    system_prompt: str = Field(..., min_length=10)
    user_prompt_template: str = Field(..., min_length=10)
    
    temperature: float = Field(default=0.1, ge=0, le=2)
    max_tokens: int = Field(default=2000, ge=100, le=8000)
    top_p: float = Field(default=1.0, ge=0, le=1)
    frequency_penalty: float = Field(default=0.0, ge=-2, le=2)
    presence_penalty: float = Field(default=0.0, ge=-2, le=2)
    
    variables: List[PromptTemplateVariable] = []
    examples: List[PromptTemplateExample] = []
    
    is_default: bool = False


class PromptTemplateUpdate(BaseModel):
    """更新Prompt模板"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = None
    
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=100, le=8000)
    top_p: Optional[float] = Field(None, ge=0, le=1)
    frequency_penalty: Optional[float] = Field(None, ge=-2, le=2)
    presence_penalty: Optional[float] = Field(None, ge=-2, le=2)
    
    variables: Optional[List[PromptTemplateVariable]] = None
    examples: Optional[List[PromptTemplateExample]] = None
    
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class PromptTemplateResponse(BaseModel):
    """Prompt模板响应"""
    id: int
    org_id: int
    name: str
    description: Optional[str]
    category: str
    
    system_prompt: str
    user_prompt_template: str
    
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    
    variables: List[Dict]
    examples: List[Dict]
    
    is_active: bool
    is_default: bool
    version: str
    
    usage_count: int
    success_count: int
    average_rating: float
    
    created_at: datetime
    updated_at: datetime


class PromptTemplateRenderRequest(BaseModel):
    """渲染Prompt模板请求"""
    variables: Dict[str, Any]


class PromptTemplateRenderResponse(BaseModel):
    """渲染Prompt模板响应"""
    rendered_prompt: str


# ========== 依赖项 ==========

async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """要求管理员权限"""
    if current_user.role not in ["admin", "superuser"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


# ========== API 端点 ==========

@router.post("/", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt_template(
    data: PromptTemplateCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建Prompt模板（管理员）"""
    
    # 如果设置为默认模板，取消该类别的其他默认模板
    if data.is_default:
        await db.execute(
            select(PromptTemplate).where(
                and_(
                    PromptTemplate.org_id == current_user.org_id,
                    PromptTemplate.category == data.category,
                    PromptTemplate.is_default == True
                )
            )
        )
        existing_defaults = (await db.execute(
            select(PromptTemplate).where(
                and_(
                    PromptTemplate.org_id == current_user.org_id,
                    PromptTemplate.category == data.category,
                    PromptTemplate.is_default == True
                )
            )
        )).scalars().all()
        
        for template in existing_defaults:
            template.is_default = False
    
    # 创建模板
    template = PromptTemplate(
        org_id=current_user.org_id,
        created_by=current_user.id,
        name=data.name,
        description=data.description,
        category=data.category,
        system_prompt=data.system_prompt,
        user_prompt_template=data.user_prompt_template,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        top_p=data.top_p,
        frequency_penalty=data.frequency_penalty,
        presence_penalty=data.presence_penalty,
        variables=[v.dict() for v in data.variables],
        examples=[e.dict() for e in data.examples],
        is_default=data.is_default
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return template.to_dict()


@router.get("/", response_model=List[PromptTemplateResponse])
async def list_prompt_templates(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取Prompt模板列表"""
    
    query = select(PromptTemplate).where(
        PromptTemplate.org_id == current_user.org_id
    )
    
    if category:
        query = query.where(PromptTemplate.category == category)
    
    if is_active is not None:
        query = query.where(PromptTemplate.is_active == is_active)
    
    query = query.order_by(PromptTemplate.created_at.desc())
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return [t.to_dict() for t in templates]


@router.get("/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单个Prompt模板"""
    
    result = await db.execute(
        select(PromptTemplate).where(
            and_(
                PromptTemplate.id == template_id,
                PromptTemplate.org_id == current_user.org_id
            )
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return template.to_dict()


@router.put("/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt_template(
    template_id: int,
    data: PromptTemplateUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新Prompt模板（管理员）"""
    
    # 获取模板
    result = await db.execute(
        select(PromptTemplate).where(
            and_(
                PromptTemplate.id == template_id,
                PromptTemplate.org_id == current_user.org_id
            )
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 更新字段
    update_data = data.dict(exclude_unset=True)
    
    # 处理变量和示例
    if "variables" in update_data:
        update_data["variables"] = [v.dict() for v in data.variables]
    if "examples" in update_data:
        update_data["examples"] = [e.dict() for e in data.examples]
    
    # 如果设置为默认，取消其他默认
    if data.is_default:
        existing_defaults = (await db.execute(
            select(PromptTemplate).where(
                and_(
                    PromptTemplate.org_id == current_user.org_id,
                    PromptTemplate.category == template.category,
                    PromptTemplate.is_default == True,
                    PromptTemplate.id != template_id
                )
            )
        )).scalars().all()
        
        for t in existing_defaults:
            t.is_default = False
    
    for field, value in update_data.items():
        setattr(template, field, value)
    
    template.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(template)
    
    return template.to_dict()


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt_template(
    template_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除Prompt模板（管理员）"""
    
    result = await db.execute(
        select(PromptTemplate).where(
            and_(
                PromptTemplate.id == template_id,
                PromptTemplate.org_id == current_user.org_id
            )
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    await db.delete(template)
    await db.commit()


@router.post("/{template_id}/render", response_model=PromptTemplateRenderResponse)
async def render_prompt_template(
    template_id: int,
    data: PromptTemplateRenderRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """渲染Prompt模板（用于测试）"""
    
    result = await db.execute(
        select(PromptTemplate).where(
            and_(
                PromptTemplate.id == template_id,
                PromptTemplate.org_id == current_user.org_id
            )
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    try:
        rendered = template.render(**data.variables)
        return {"rendered_prompt": rendered}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{template_id}/stats")
async def get_prompt_template_stats(
    template_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取Prompt模板使用统计"""
    
    result = await db.execute(
        select(PromptTemplate).where(
            and_(
                PromptTemplate.id == template_id,
                PromptTemplate.org_id == current_user.org_id
            )
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 获取使用日志
    logs_result = await db.execute(
        select(PromptTemplateUsageLog).where(
            PromptTemplateUsageLog.template_id == template_id
        ).order_by(PromptTemplateUsageLog.created_at.desc()).limit(100)
    )
    recent_logs = logs_result.scalars().all()
    
    # 统计
    from sqlalchemy import func
    stats_result = await db.execute(
        select(
            func.count(PromptTemplateUsageLog.id),
            func.sum(PromptTemplateUsageLog.input_tokens),
            func.sum(PromptTemplateUsageLog.output_tokens),
            func.avg(PromptTemplateUsageLog.latency_ms),
            func.avg(PromptTemplateUsageLog.rating)
        ).where(PromptTemplateUsageLog.template_id == template_id)
    )
    stats = stats_result.first()
    
    return {
        "template_id": template_id,
        "total_usage": stats[0] or 0,
        "total_input_tokens": stats[1] or 0,
        "total_output_tokens": stats[2] or 0,
        "average_latency_ms": stats[3] or 0,
        "average_rating": stats[4] or 0,
        "recent_logs": [
            {
                "id": log.id,
                "created_at": log.created_at.isoformat(),
                "input_tokens": log.input_tokens,
                "output_tokens": log.output_tokens,
                "latency_ms": log.latency_ms,
                "success": log.success,
                "rating": log.rating
            }
            for log in recent_logs[:10]
        ]
    }


@router.post("/{template_id}/duplicate", response_model=PromptTemplateResponse)
async def duplicate_prompt_template(
    template_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """复制Prompt模板"""
    
    result = await db.execute(
        select(PromptTemplate).where(
            and_(
                PromptTemplate.id == template_id,
                PromptTemplate.org_id == current_user.org_id
            )
        )
    )
    original = result.scalar_one_or_none()
    
    if not original:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 创建副本
    duplicate = PromptTemplate(
        org_id=current_user.org_id,
        created_by=current_user.id,
        name=f"{original.name} (副本)",
        description=original.description,
        category=original.category,
        system_prompt=original.system_prompt,
        user_prompt_template=original.user_prompt_template,
        temperature=original.temperature,
        max_tokens=original.max_tokens,
        top_p=original.top_p,
        frequency_penalty=original.frequency_penalty,
        presence_penalty=original.presence_penalty,
        variables=original.variables,
        examples=original.examples,
        is_default=False  # 副本不设为默认
    )
    
    db.add(duplicate)
    await db.commit()
    await db.refresh(duplicate)
    
    return duplicate.to_dict()


"""
安全服务
敏感词检测、内容审核
"""

import re
from typing import Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import SensitiveWordLog


class SecurityService:
    """安全服务"""
    
    # 敏感词库（示例，实际应从配置或数据库加载）
    SENSITIVE_WORDS = {
        "political": ["政治敏感词1", "政治敏感词2"],  # 政治类
        "discrimination": ["歧视词1", "歧视词2"],  # 歧视类
        "adult": ["涉黄词1", "涉黄词2"],  # 成人内容
        "violence": ["暴力词1", "暴力词2"],  # 暴力类
        "commercial_secret": ["机密", "内部资料", "绝密"],  # 商业机密
    }
    
    # 风险等级
    RISK_LEVELS = {
        "political": "critical",
        "discrimination": "high",
        "adult": "critical",
        "violence": "high",
        "commercial_secret": "medium",
    }
    
    def __init__(self, db: AsyncSession = None):
        self.db = db
    
    def check_sensitive_content(self, text: str) -> Dict:
        """检查文本是否包含敏感内容
        
        Returns:
            {
                "has_sensitive": bool,
                "risk_level": str,
                "detected_words": List[str],
                "categories": List[str],
                "should_block": bool
            }
        """
        detected_words = []
        categories = []
        max_risk_level = "low"
        
        for category, words in self.SENSITIVE_WORDS.items():
            for word in words:
                if word in text:
                    detected_words.append(word)
                    if category not in categories:
                        categories.append(category)
                    
                    # 更新风险等级
                    current_risk = self.RISK_LEVELS.get(category, "low")
                    if self._compare_risk_level(current_risk, max_risk_level) > 0:
                        max_risk_level = current_risk
        
        has_sensitive = len(detected_words) > 0
        should_block = max_risk_level in ["critical", "high"]
        
        return {
            "has_sensitive": has_sensitive,
            "risk_level": max_risk_level,
            "detected_words": detected_words,
            "categories": categories,
            "should_block": should_block
        }
    
    def _compare_risk_level(self, level1: str, level2: str) -> int:
        """比较风险等级
        
        Returns:
            1: level1 > level2
            0: level1 == level2
            -1: level1 < level2
        """
        levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return levels.get(level1, 0) - levels.get(level2, 0)
    
    async def log_sensitive_detection(
        self,
        content_type: str,
        text: str,
        detection_result: Dict,
        message_id: int = None,
        file_id: int = None
    ):
        """记录敏感词检测日志"""
        if not self.db or not detection_result["has_sensitive"]:
            return
        
        import json
        
        log = SensitiveWordLog(
            message_id=message_id,
            file_id=file_id,
            content_type=content_type,
            detected_words=json.dumps(detection_result["detected_words"], ensure_ascii=False),
            risk_level=detection_result["risk_level"],
            original_text=text[:500],  # 只保存前500字符
            is_blocked=detection_result["should_block"]
        )
        
        self.db.add(log)
        await self.db.commit()
    
    def calculate_confidence(self, similarities: List[float], threshold: float = 0.75) -> float:
        """计算答案置信度
        
        基于检索到的文档相似度计算整体置信度
        
        Args:
            similarities: 检索到的文档相似度列表
            threshold: 相似度阈值
        
        Returns:
            置信度分数 (0.0-1.0)
        """
        if not similarities:
            return 0.0
        
        # 过滤低于阈值的结果
        valid_sims = [s for s in similarities if s >= threshold]
        
        if not valid_sims:
            return 0.0
        
        # 加权平均（越靠前权重越高）
        weights = [1.0 / (i + 1) for i in range(len(valid_sims))]
        weighted_sum = sum(s * w for s, w in zip(valid_sims, weights))
        weight_sum = sum(weights)
        
        confidence = weighted_sum / weight_sum
        
        # 根据召回数量调整置信度
        if len(valid_sims) < 3:
            confidence *= 0.8  # 召回数量少，降低置信度
        
        return min(confidence, 1.0)
    
    def add_disclaimer(self, answer: str) -> str:
        """为AI回答添加免责声明"""
        disclaimer = "\n\n---\n💡 **免责声明**：以上回答由 AI 基于企业知识库生成，仅供参考。如有疑问请咨询相关部门或查阅原始文档。"
        return answer + disclaimer


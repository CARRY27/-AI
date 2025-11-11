"""
导出服务
支持导出对话为 PDF 或 Markdown
"""

from typing import List, Dict
from datetime import datetime
import markdown
from io import BytesIO


class ExportService:
    """导出服务"""
    
    @staticmethod
    def export_to_markdown(
        conversation_title: str,
        messages: List[Dict],
        user_name: str = None
    ) -> str:
        """导出对话为 Markdown 格式"""
        
        md_content = f"""# {conversation_title}

**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{f"**用户**: {user_name}" if user_name else ""}

---

"""
        
        for i, msg in enumerate(messages, 1):
            role_icon = "👤" if msg["role"] == "user" else "🤖"
            role_name = "用户" if msg["role"] == "user" else "AI 助手"
            
            md_content += f"""
## {role_icon} {role_name} - 消息 #{i}

**时间**: {msg.get('created_at', 'N/A')}

{msg['content']}

"""
            
            # 如果是AI回答，添加来源引用
            if msg["role"] == "assistant" and msg.get("source_refs"):
                md_content += "\n### 📎 参考来源\n\n"
                for idx, source in enumerate(msg["source_refs"], 1):
                    md_content += f"{idx}. **{source['file_name']}** "
                    if source.get('page'):
                        md_content += f"- 第 {source['page']} 页"
                    md_content += "\n"
                md_content += "\n"
            
            md_content += "---\n"
        
        # 添加声明
        md_content += """
## 📝 免责声明

本对话记录由 DocAgent 企业知识问答系统生成。AI 回答基于企业知识库内容，仅供参考。
如有疑问，请查阅原始文档或咨询相关部门。

---
*Powered by DocAgent v1.0*
"""
        
        return md_content
    
    @staticmethod
    def export_to_pdf(
        conversation_title: str,
        messages: List[Dict],
        user_name: str = None
    ) -> bytes:
        """导出对话为 PDF 格式
        
        Note: 需要安装 reportlab 或 weasyprint
        这里提供简化版本，将 Markdown 转为 HTML 再转 PDF
        """
        try:
            from weasyprint import HTML
            
            # 先生成 Markdown
            md_content = ExportService.export_to_markdown(
                conversation_title, messages, user_name
            )
            
            # 转换为 HTML
            html_content = markdown.markdown(
                md_content,
                extensions=['extra', 'codehilite', 'tables']
            )
            
            # 添加 CSS 样式
            styled_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
            line-height: 1.8;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
        }}
        h1 {{ color: #333; border-bottom: 2px solid #409eff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        h3 {{ color: #777; }}
        code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }}
        pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        hr {{ border: none; border-top: 1px solid #eee; margin: 20px 0; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 50px; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""
            
            # 生成 PDF
            pdf_bytes = HTML(string=styled_html).write_pdf()
            return pdf_bytes
        
        except ImportError:
            # 如果没有安装 weasyprint，返回简单的文本PDF
            raise NotImplementedError("PDF 导出需要安装 weasyprint 库")
    
    @staticmethod
    def export_to_html(
        conversation_title: str,
        messages: List[Dict],
        user_name: str = None
    ) -> str:
        """导出对话为 HTML 格式"""
        
        md_content = ExportService.export_to_markdown(
            conversation_title, messages, user_name
        )
        
        html_content = markdown.markdown(
            md_content,
            extensions=['extra', 'codehilite', 'tables']
        )
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{conversation_title}</title>
    <style>
        body {{
            font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
            line-height: 1.8;
            max-width: 900px;
            margin: 40px auto;
            padding: 30px;
            background: #f9f9f9;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; border-bottom: 3px solid #409eff; padding-bottom: 15px; }}
        h2 {{ color: #555; margin-top: 35px; background: #f5f7fa; padding: 10px 15px; border-left: 4px solid #409eff; }}
        h3 {{ color: #777; margin-top: 20px; }}
        code {{ background: #f0f2f5; padding: 3px 8px; border-radius: 4px; font-family: 'Courier New', monospace; }}
        pre {{ background: #f5f5f5; padding: 20px; border-radius: 6px; overflow-x: auto; border: 1px solid #e4e7ed; }}
        hr {{ border: none; border-top: 1px solid #dcdfe6; margin: 30px 0; }}
        .footer {{ text-align: center; color: #999; font-size: 13px; margin-top: 60px; padding-top: 20px; border-top: 1px solid #eee; }}
        a {{ color: #409eff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        {html_content}
        <div class="footer">
            导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
            Powered by <strong>DocAgent</strong>
        </div>
    </div>
</body>
</html>
"""


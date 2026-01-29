#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dify工作流客户端
用于调用Dify API进行知识点筛选和分类
"""

import os
import json
from typing import Dict, List, Any
import httpx
from loguru import logger
from dotenv import load_dotenv

load_dotenv("config/.env")


class DifyClient:
    """Dify API客户端"""
    
    def __init__(self):
        self.api_key = os.getenv("DIFY_API_KEY", "")
        self.api_base = os.getenv("DIFY_API_BASE", "https://api.dify.ai/v1")
        self.workflow_id = os.getenv("DIFY_WORKFLOW_ID", "")
        
        # if not self.api_key:
        #     logger.warning("未设置DIFY_API_KEY，Dify功能将不可用")
        
        self.client = httpx.Client(timeout=60.0)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def filter_knowledge(self, knowledge_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用Dify工作流筛选和分类知识点
        
        Args:
            knowledge_item: 原始知识点数据
            
        Returns:
            处理后的知识点数据
        """
        try:
            if not self.api_key:
                logger.warning("Dify未配置，跳过AI筛选")
                return self._default_filter(knowledge_item)
            
            # 构建提示词
            prompt = self._build_filter_prompt(knowledge_item)
            
            # 调用Dify工作流
            response = self._call_workflow(prompt)
            
            if response:
                # 解析Dify返回结果
                filtered = self._parse_dify_response(response, knowledge_item)
                logger.info(f"成功筛选知识点: {knowledge_item.get('name', 'unknown')}")
                return filtered
            else:
                logger.warning("Dify调用失败，使用默认筛选")
                return self._default_filter(knowledge_item)
                
        except Exception as e:
            logger.error(f"Dify筛选失败: {str(e)}")
            return self._default_filter(knowledge_item)
    
    def _build_filter_prompt(self, knowledge_item: Dict[str, Any]) -> str:
        """构建用于Dify的提示词"""
        
        item_type = knowledge_item.get("type", "Unknown")
        name = knowledge_item.get("name", "")
        description = knowledge_item.get("description", "")
        
        prompt = f"""
请分析以下安全知识点，并提供分类和标签：

类型: {item_type}
名称: {name}
描述: {description}

请返回JSON格式，包含以下字段：
1. category: 主要分类（如：Web安全、系统安全、网络安全等）
2. sub_category: 子分类（更具体的分类）
3. tags: 相关标签列表（3-5个关键标签）
4. severity: 严重程度（CRITICAL/HIGH/MEDIUM/LOW，如适用）
5. difficulty: 学习难度（BEGINNER/INTERMEDIATE/ADVANCED）
6. is_relevant: 是否为有效的安全知识点（true/false）
7. summary: 简短总结（50字以内）

示例输出：
{{
  "category": "Web安全",
  "sub_category": "注入攻击",
  "tags": ["SQL注入", "数据库安全", "OWASP Top 10"],
  "severity": "HIGH",
  "difficulty": "INTERMEDIATE",
  "is_relevant": true,
  "summary": "通过SQL注入攻击数据库的常见漏洞"
}}
"""
        return prompt
    
    def _call_workflow(self, prompt: str) -> Dict[str, Any]:
        """调用Dify工作流API"""
        
        try:
            url = f"{self.api_base}/workflows/run"
            
            payload = {
                "inputs": {
                    "query": prompt
                },
                "response_mode": "blocking",
                "user": "security-kg-system"
            }
            
            response = self.client.post(
                url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Dify API调用失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"调用Dify工作流异常: {str(e)}")
            return None
    
    def _parse_dify_response(self, response: Dict, original: Dict) -> Dict:
        """解析Dify返回的结果"""
        
        try:
            # 从Dify响应中提取结果
            # 实际结构取决于您的Dify工作流配置
            outputs = response.get("data", {}).get("outputs", {})
            text_output = outputs.get("text", "")
            
            # 尝试解析JSON
            try:
                ai_result = json.loads(text_output)
            except:
                # 如果不是JSON，使用默认值
                ai_result = {}
            
            # 合并AI结果和原始数据
            filtered = original.copy()
            filtered.update({
                "category": ai_result.get("category", "未分类"),
                "sub_category": ai_result.get("sub_category", ""),
                "tags": ai_result.get("tags", []),
                "ai_severity": ai_result.get("severity"),
                "difficulty": ai_result.get("difficulty", "INTERMEDIATE"),
                "is_relevant": ai_result.get("is_relevant", True),
                "ai_summary": ai_result.get("summary", ""),
                "ai_processed": True
            })
            
            return filtered
            
        except Exception as e:
            logger.error(f"解析Dify响应失败: {str(e)}")
            return self._default_filter(original)
    
    def _default_filter(self, knowledge_item: Dict[str, Any]) -> Dict:
        """默认筛选逻辑（当Dify不可用时）"""
        
        item_type = knowledge_item.get("type", "")
        
        # 基于类型的简单分类
        category_map = {
            "CVE": "漏洞库",
            "Exploit": "漏洞利用",
            "Lab": "实践靶场",
            "Technique": "攻击技术",
            "Defense": "防御技术",
            "Tool": "安全工具"
        }
        
        filtered = knowledge_item.copy()
        filtered.update({
            "category": category_map.get(item_type, "其他"),
            "sub_category": "",
            "tags": self._extract_default_tags(knowledge_item),
            "difficulty": "INTERMEDIATE",
            "is_relevant": True,
            "ai_processed": False
        })
        
        return filtered
    
    def _extract_default_tags(self, item: Dict) -> List[str]:
        """提取默认标签"""
        tags = []
        
        # 从名称和描述中提取关键词
        text = f"{item.get('name', '')} {item.get('description', '')}"
        text_lower = text.lower()
        
        # 常见安全关键词
        keywords = {
            "sql": "SQL注入",
            "xss": "XSS",
            "csrf": "CSRF",
            "rce": "远程代码执行",
            "ssrf": "SSRF",
            "xxe": "XXE",
            "injection": "注入攻击",
            "authentication": "身份认证",
            "authorization": "授权",
            "encryption": "加密",
            "buffer overflow": "缓冲区溢出",
            "privilege escalation": "权限提升"
        }
        
        for keyword, tag in keywords.items():
            if keyword in text_lower:
                tags.append(tag)
        
        return tags[:5]  # 最多5个标签
    
    def batch_filter(self, knowledge_list: List[Dict]) -> List[Dict]:
        """批量筛选知识点"""
        
        logger.info(f"开始批量筛选 {len(knowledge_list)} 个知识点")
        
        filtered_list = []
        for idx, item in enumerate(knowledge_list):
            logger.info(f"处理 {idx+1}/{len(knowledge_list)}: {item.get('name', 'unknown')}")
            filtered = self.filter_knowledge(item)
            
            # 只保留相关的知识点
            if filtered.get("is_relevant", True):
                filtered_list.append(filtered)
        
        logger.info(f"筛选完成，保留 {len(filtered_list)} 个有效知识点")
        return filtered_list


if __name__ == "__main__":
    # 测试Dify客户端
    logger.add("dify_workflow/logs/dify.log", rotation="1 day")
    
    client = DifyClient()
    
    # 测试数据
    test_knowledge = {
        "type": "Technique",
        "name": "SQL注入攻击",
        "description": "通过在SQL查询中注入恶意代码来攻击数据库的常见Web安全漏洞"
    }
    
    result = client.filter_knowledge(test_knowledge)
    print(json.dumps(result, ensure_ascii=False, indent=2))


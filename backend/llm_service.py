#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LLM服务模块
集成大语言模型进行知识整合和问答
"""

import os
from typing import Dict, List, Any, Optional
from loguru import logger
from dotenv import load_dotenv
import json

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI库未安装，LLM功能受限")

load_dotenv("config/.env")


class LLMService:
    """LLM服务类"""
    
    def __init__(self, graph_query=None):
        self.graph_query = graph_query
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        
        # 定义需要追踪的安全主题
        self.security_terms = [
            "SQL注入", "XSS", "CSRF", "RCE", "SSRF", "XXE", 
            "缓冲区溢出", "权限提升", "命令注入", "文件包含", 
            "文件上传", "反序列化", "越权", "逻辑漏洞", "加密", 
            "认证", "CVE", "漏洞", "攻击", "防御", "渗透测试",
            "SQL Injection", "Cross-Site Scripting", "Remote Code Execution"
        ]
        
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY", "")
            api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
            
            if api_key:
                self.client = OpenAI(
                    api_key=api_key,
                    base_url=api_base
                )
                logger.info("OpenAI客户端初始化成功")
            else:
                self.client = None
                logger.warning("未设置OPENAI_API_KEY")
        else:
            self.client = None
    
    def query(self, question: str, context_depth: int = 2, user_id: str = None, conversation_id: str = None) -> Dict[str, Any]:
        """
        基于知识图谱的LLM问答 (Context-Aware Modular)
        """
        try:
            # 1. 获取历史记录并判断该主题是否已模块化输出过
            history_context = ""
            current_topic = self._detect_security_topic(question)
            should_use_json = False
            
            if conversation_id and self.graph_query:
                try:
                    history = self.graph_query.get_conversation_messages(conversation_id)
                    recent_history = history[-6:] if history else []
                    
                    if recent_history:
                        history_context = "对话历史:\n"
                        for msg in recent_history:
                            history_context += f"User: {msg.get('question', '')}\nAssistant: {msg.get('answer', '')}\n"
                    
                    # 核心逻辑：如果检测到是已知安全主题
                    if current_topic:
                        # 检查历史上是否已经针对该特定主题输出过JSON模块
                        topic_already_covered = False
                        for msg in history:
                            answer_text = msg.get("answer", "")
                            # 简单的启发式检查：如果回答包含 strict JSON 里的关键key，说明是模块化输出
                            if "vulnerability_introduction" in answer_text and "classic_cases" in answer_text:
                                # 检查该历史消息的问题是否也关于同一主题
                                prev_topic = self._detect_security_topic(msg.get("question", ""))
                                if prev_topic == current_topic:
                                    topic_already_covered = True
                                    break
                        
                        # 如果是新主题且未覆盖 => 强制JSON
                        if not topic_already_covered:
                            should_use_json = True
                    
                except Exception as e:
                    logger.warning(f"历史记录处理失败: {e}")

            # 2. 从图谱中搜索相关知识
            context_knowledge = self._search_relevant_knowledge(question)
            
            # 3. 构建上下文
            context = self._build_context(context_knowledge)
            
            # 4. 调用LLM生成答案 (传入模式)
            if self.client:
                mode = "JSON" if should_use_json else "TEXT"
                answer = self._call_llm(question, context, history_context, mode=mode)
            else:
                answer = self._fallback_answer(question, context_knowledge)
            
            # 5. 保存历史记录
            if user_id and conversation_id and self.graph_query:
                # context_knowledge 就是 related_knowledge
                self.graph_query.save_chat_history(user_id, conversation_id, question, answer, context_knowledge)
            
            # 6. 构建响应
            response = {
                "answer": answer,
                "related_knowledge": context_knowledge,
                "context_used": bool(context_knowledge)
            }
            
            return response
            
        except Exception as e:
            logger.error(f"LLM查询失败: {str(e)}")
            return {
                "answer": f"抱歉，处理您的问题时出现错误: {str(e)}",
                "related_knowledge": [],
                "context_used": False
            }
    
    def _search_relevant_knowledge(self, question: str) -> List[Dict]:
        """从图谱中搜索相关知识"""
        if not self.graph_query:
            return []
        
        try:
            # 提取关键词
            keywords = self._extract_keywords(question)
            
            # 搜索知识点
            all_results = []
            for keyword in keywords:
                results = self.graph_query.search_knowledge(keyword, limit=5)
                all_results.extend(results)
            
            # 去重
            seen = set()
            unique_results = []
            for item in all_results:
                item_id = item.get("name", str(item))
                if item_id not in seen:
                    seen.add(item_id)
                    unique_results.append(item)
            
            return unique_results[:10]  # 最多返回10个
            
        except Exception as e:
            logger.error(f"搜索相关知识失败: {str(e)}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词 (基于预定义列表)"""
        keywords = []
        text_lower = text.lower()
        
        # 优先匹配预定义的准确术语
        for term in self.security_terms:
            if term.lower() in text_lower:
                keywords.append(term)
        
        # 如果没有找到术语，使用简单的分词兜底
        if not keywords:
            words = text.split()
            keywords = [w for w in words if len(w) > 2][:3]
        
        return keywords if keywords else [text[:20]]

    def _detect_security_topic(self, text: str) -> Optional[str]:
        """检测文本中提到的首要安全主题"""
        text_lower = text.lower()
        for term in self.security_terms:
            if term.lower() in text_lower:
                return term
        return None
    
    def _build_context(self, knowledge_list: List[Dict]) -> str:
        """构建上下文字符串"""
        if not knowledge_list:
            return "暂无相关知识点。"
        
        context_parts = ["以下是从知识图谱中检索到的相关安全知识：\n"]
        
        for idx, item in enumerate(knowledge_list, 1):
            name = item.get("name", "未命名")
            description = item.get("description", "无描述")
            item_type = item.get("type", "Unknown")
            severity = item.get("severity", "")
            
            context_parts.append(f"\n{idx}. 【{item_type}】{name}")
            if severity:
                context_parts.append(f" [严重程度: {severity}]")
            context_parts.append(f"\n   描述: {description}")
            
            # 添加相关链接
            if item.get("url"):
                context_parts.append(f"\n   链接: {item['url']}")
        
        return "".join(context_parts)
    
    def _call_llm(self, question: str, context: str, history_context: str = "", mode: str = "TEXT") -> str:
        """调用OpenAI LLM"""
        try:
            if mode == "JSON":
                # JSON模式：严格的模块化输出
                system_prompt = """你是一个安全领域的AI助手。请务必以JSON格式输出回答，不要包含 markdown 代码块标记，直接返回合法的 JSON 对象。
JSON 结构必须严格包含以下字段，如果某个字段没有相关信息，请填"暂无"：
{
    "vulnerability_introduction": "漏洞介绍",
    "vulnerability_principle": "漏洞原理",
    "classic_cases": "经典案例",
    "preventive_measures": "预防措施",
    "practice_range": "实践靶场",
    "relevant_links": [
        {"name": "链接名称", "url": "链接地址"}
    ]
}
确保回答准确、专业、易懂，使用中文。"""
                response_format = {"type": "json_object"}
            else:
                # TEXT模式：自然语言回答
                system_prompt = """你是一个安全领域的AI助手，专门帮助用户学习和理解网络安全知识。
请用自然语言（Plain Text）回答用户的问题。不要使用JSON格式。
回答应准确、专业、易懂，并结合上下文。"""
                response_format = None

            user_prompt = f"""{history_context}

问题: {question}

{context}

请基于上述知识图谱信息和对话历史回答。"""

            # 构建请求参数
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            if response_format:
                kwargs["response_format"] = response_format

            response = self.client.chat.completions.create(**kwargs)
            
            answer = response.choices[0].message.content
            logger.info(f"LLM回答生成成功 (模式: {mode})，token使用: {response.usage.total_tokens}")
            
            return answer
            
        except Exception as e:
            logger.error(f"调用LLM失败: {str(e)}")
            return self._fallback_answer(question, [])
    
    def _fallback_answer(self, question: str, knowledge_list: List[Dict]) -> str:
        """降级回答（LLM不可用时）"""
        if not knowledge_list:
            return "抱歉，我暂时无法回答这个问题。请检查问题是否与安全知识相关，或联系管理员启用LLM服务。"
        
        # 基于检索结果生成简单回答
        answer_parts = [f"关于「{question}」，我找到了以下相关信息：\n"]
        
        for idx, item in enumerate(knowledge_list[:3], 1):
            name = item.get("name", "未命名")
            description = item.get("description", "")
            
            answer_parts.append(f"\n{idx}. {name}")
            if description:
                answer_parts.append(f"\n   {description[:200]}...")
        
        answer_parts.append("\n\n提示: 启用LLM服务可以获得更详细和智能的回答。")
        
        return "".join(answer_parts)
    
    def summarize_knowledge(self, node_name: str) -> str:
        """总结指定知识点"""
        if not self.graph_query:
            return "图数据库服务不可用"
        
        try:
            # 获取知识点及相关内容
            related = self.graph_query.get_related_knowledge(node_name, depth=1)
            nodes = related.get("nodes", [])
            
            if not nodes:
                return f"未找到知识点: {node_name}"
            
            # 找到主节点
            main_node = next((n for n in nodes if n.get("name") == node_name), nodes[0])
            
            if not self.client:
                # 简单总结
                return f"{main_node.get('name')}: {main_node.get('description', '无描述')}"
            
            # 使用LLM生成总结
            context = f"""
知识点名称: {main_node.get('name')}
类型: {main_node.get('type')}
描述: {main_node.get('description', '')}
相关知识点数量: {len(nodes) - 1}
"""
            
            prompt = f"请用2-3句话总结以下安全知识点：\n{context}"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个安全知识总结助手"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"总结知识失败: {str(e)}")
            return f"总结失败: {str(e)}"


if __name__ == "__main__":
    logger.add("backend/logs/llm.log", rotation="1 day")
    
    # 测试LLM服务
    service = LLMService()
    
    response = service.query("什么是SQL注入攻击？如何防御？")
    print(response["answer"])


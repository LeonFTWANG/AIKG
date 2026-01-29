#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Neo4j图查询模块
提供各种图数据查询功能
"""

import os
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from loguru import logger
from dotenv import load_dotenv
import json

load_dotenv("config/.env")


class GraphQuery:
    """图查询服务"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "neo4j")
        
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            self.driver.verify_connectivity()
            logger.info("Neo4j查询服务初始化成功")
        except Exception as e:
            logger.error(f"Neo4j连接失败: {str(e)}")
            raise
    
    def create_user(self, username, password_hash):
        """创建新用户"""
        with self.driver.session() as session:
            # 检查用户是否存在
            check_query = "MATCH (u:User {username: $username}) RETURN u"
            if session.run(check_query, username=username).single():
                return False
            
            # 创建用户
            query = """
            CREATE (u:User {
                username: $username,
                password_hash: $password_hash,
                created_at: datetime()
            })
            RETURN u
            """
            session.run(query, username=username, password_hash=password_hash)
            return True

    def get_user_password(self, username):
        """获取用户密码哈希"""
        with self.driver.session() as session:
            query = "MATCH (u:User {username: $username}) RETURN u.password_hash as hash"
            result = session.run(query, username=username).single()
            return result["hash"] if result else None

    def create_conversation(self, user_id, title="New Chat"):
        """创建新对话"""
        import uuid
        conversation_id = str(uuid.uuid4())
        
        with self.driver.session() as session:
            query = """
            MATCH (u:User {username: $user_id})
            CREATE (c:Conversation {
                id: $conversation_id,
                title: $title,
                created_at: datetime(),
                updated_at: datetime()
            })
            MERGE (u)-[:HAS_CONVERSATION]->(c)
            RETURN c.id as id, c.title as title, c.created_at as created_at
            """
            result = session.run(query, user_id=user_id, title=title, conversation_id=conversation_id).single()
            if result:
                return {
                    "id": result["id"],
                    "title": result["title"],
                    "created_at": result["created_at"].iso_format()
                }
            return None

    def get_user_conversations(self, user_id):
        """获取用户的所有对话"""
        with self.driver.session() as session:
            query = """
            MATCH (u:User {username: $user_id})-[:HAS_CONVERSATION]->(c)
            RETURN c
            ORDER BY c.updated_at DESC
            """
            result = session.run(query, user_id=user_id)
            conversations = []
            for record in result:
                node = record["c"]
                
                created_at = node.get("created_at")
                updated_at = node.get("updated_at")
                
                conversations.append({
                    "id": node.get("id"),
                    "title": node.get("title"),
                    "created_at": created_at.iso_format() if created_at else None,
                    "updated_at": updated_at.iso_format() if updated_at else None
                })
            return conversations

    def save_chat_history(self, user_id, conversation_id, question, answer, related_knowledge=None):
        """保存聊天记录到指定对话"""
        if related_knowledge is None:
            related_knowledge = []
            
        # 辅助序列化函数
        def default_serializer(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return str(obj)

        # 将复杂对象序列化为JSON字符串存储
        try:
            related_knowledge_json = json.dumps(related_knowledge, default=default_serializer, ensure_ascii=False)
        except Exception as e:
            logger.error(f"序列化相关知识失败: {e}")
            related_knowledge_json = "[]"
        
        with self.driver.session() as session:
            query = """
            MATCH (c:Conversation {id: $conversation_id})
            CREATE (m:Message {
                question: $question,
                answer: $answer,
                related_knowledge: $related_knowledge,
                timestamp: datetime()
            })
            MERGE (c)-[:HAS_MESSAGE]->(m)
            SET c.updated_at = datetime()
            """
            session.run(query, conversation_id=conversation_id, question=question, answer=answer, related_knowledge=related_knowledge_json)

    def get_conversation_messages(self, conversation_id):
        """获取指定对话的消息记录"""
        with self.driver.session() as session:
            query = """
            MATCH (c:Conversation {id: $conversation_id})-[:HAS_MESSAGE]->(m)
            RETURN m
            ORDER BY m.timestamp ASC
            """
            result = session.run(query, conversation_id=conversation_id)
            history = []
            for record in result:
                node = record["m"]
                timestamp = node.get("timestamp")
                
                # 解析related_knowledge
                related_knowledge = []
                rk_json = node.get("related_knowledge")
                if rk_json:
                    try:
                        related_knowledge = json.loads(rk_json)
                    except:
                        related_knowledge = []
                
                history.append({
                    "question": node.get("question"),
                    "answer": node.get("answer"),
                    "related_knowledge": related_knowledge,
                    "timestamp": timestamp.iso_format() if timestamp else None
                })
            return history

    def delete_conversation(self, conversation_id, user_id):
        """删除指定对话及其所有消息"""
        with self.driver.session() as session:
            # 验证用户拥有此对话，并删除对话及其消息
            query = """
            MATCH (u:User {username: $user_id})-[:HAS_CONVERSATION]->(c:Conversation {id: $conversation_id})
            OPTIONAL MATCH (c)-[:HAS_MESSAGE]->(m:Message)
            WITH c, collect(m) as messages
            FOREACH (msg IN messages | DETACH DELETE msg)
            DETACH DELETE c
            RETURN count(c) as deleted_count
            """
            result = session.run(query, user_id=user_id, conversation_id=conversation_id)
            record = result.single()
            
            # 返回是否成功删除（找到并删除了对话）
            if record and record["deleted_count"] > 0:
                logger.info(f"成功删除用户 {user_id} 的对话 {conversation_id}")
                return True
            else:
                logger.warning(f"未找到用户 {user_id} 的对话 {conversation_id}，或无权删除")
                return False

    def get_chat_history(self, username, limit=50):
        """(Deprecated) 获取聊天记录 - 保留兼容性"""
        return []

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
    
    def search_knowledge(self, query: str, limit: int = 10) -> List[Dict]:
        """
        搜索知识点
        支持全文搜索名称、描述、标签
        """
        with self.driver.session() as session:
            cypher = """
            MATCH (n)
            WHERE toLower(n.name) CONTAINS toLower($search_term)
               OR toLower(n.description) CONTAINS toLower($search_term)
               OR any(tag IN n.tags WHERE toLower(tag) CONTAINS toLower($search_term))
            RETURN n, labels(n) as type
            LIMIT $limit
            """
            
            result = session.run(cypher, search_term=query, limit=limit)
            
            nodes = []
            for record in result:
                node = dict(record["n"])
                node["type"] = record["type"][0] if record["type"] else "Unknown"
                nodes.append(node)
            
            logger.info(f"搜索 '{query}' 找到 {len(nodes)} 个结果")
            return nodes
    
    def get_related_knowledge(self, node_name: str, depth: int = 2) -> Dict:
        """
        获取相关知识点
        返回以指定节点为中心的子图
        """
        with self.driver.session() as session:
            cypher = """
            MATCH path = (n)-[*1..$depth]-(related)
            WHERE n.name = $name
            WITH nodes(path) as nodes, relationships(path) as rels
            UNWIND nodes as node
            WITH collect(DISTINCT node) as uniqueNodes, rels
            UNWIND rels as rel
            WITH uniqueNodes, collect(DISTINCT rel) as uniqueRels
            RETURN uniqueNodes, uniqueRels
            """
            
            result = session.run(cypher, name=node_name, depth=depth)
            
            record = result.single()
            if not record:
                return {"nodes": [], "relationships": []}
            
            nodes = []
            for node in record["uniqueNodes"]:
                node_dict = dict(node)
                node_dict["id"] = node.element_id
                node_dict["labels"] = list(node.labels)
                nodes.append(node_dict)
            
            relationships = []
            for rel in record["uniqueRels"]:
                relationships.append({
                    "id": rel.element_id,
                    "type": rel.type,
                    "start": rel.start_node.element_id,
                    "end": rel.end_node.element_id
                })
            
            logger.info(f"获取相关知识: {node_name}, {len(nodes)} 节点, {len(relationships)} 关系")
            return {
                "nodes": nodes,
                "relationships": relationships
            }
    
    def get_graph_for_visualization(self, limit: int = 100) -> Dict:
        """
        获取用于可视化的图数据
        """
        with self.driver.session() as session:
            cypher = """
            MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT $limit
            """
            
            result = session.run(cypher, limit=limit)
            
            nodes_dict = {}
            edges = []
            
            for record in result:
                # 源节点
                n = record["n"]
                n_id = n.element_id
                if n_id not in nodes_dict:
                    nodes_dict[n_id] = {
                        "id": n_id,
                        "label": n.get("name", "Unknown"),
                        "type": list(n.labels)[0] if n.labels else "Unknown",
                        "properties": dict(n)
                    }
                
                # 目标节点
                m = record["m"]
                m_id = m.element_id
                if m_id not in nodes_dict:
                    nodes_dict[m_id] = {
                        "id": m_id,
                        "label": m.get("name", "Unknown"),
                        "type": list(m.labels)[0] if m.labels else "Unknown",
                        "properties": dict(m)
                    }
                
                # 关系
                r = record["r"]
                edges.append({
                    "source": n_id,
                    "target": m_id,
                    "type": r.type,
                    "label": r.type
                })
            
            nodes = list(nodes_dict.values())
            
            logger.info(f"获取可视化图数据: {len(nodes)} 节点, {len(edges)} 边")
            return {
                "nodes": nodes,
                "edges": edges
            }
    
    def get_learning_path(self, start_topic: str, end_topic: str) -> List[Dict]:
        """
        获取学习路径
        找出从起始主题到目标主题的最短路径
        """
        with self.driver.session() as session:
            cypher = """
            MATCH path = shortestPath(
                (start)-[*]-(end)
            )
            WHERE start.name = $start_topic AND end.name = $end_topic
            RETURN nodes(path) as nodes, relationships(path) as rels
            """
            
            result = session.run(cypher, start_topic=start_topic, end_topic=end_topic)
            
            record = result.single()
            if not record:
                logger.warning(f"未找到从 {start_topic} 到 {end_topic} 的路径")
                return []
            
            path = []
            nodes = record["nodes"]
            rels = record["rels"]
            
            for i, node in enumerate(nodes):
                step = {
                    "name": node.get("name"),
                    "type": list(node.labels)[0] if node.labels else "Unknown",
                    "description": node.get("description", "")
                }
                
                if i < len(rels):
                    step["relation"] = rels[i].type
                
                path.append(step)
            
            logger.info(f"找到学习路径，共 {len(path)} 步")
            return path
    
    def get_techniques_by_severity(self, severity: str) -> List[Dict]:
        """获取指定严重程度的技术"""
        with self.driver.session() as session:
            cypher = """
            MATCH (t:Technique {severity: $severity})
            RETURN t
            ORDER BY t.name
            """
            
            result = session.run(cypher, severity=severity)
            
            techniques = [dict(record["t"]) for record in result]
            return techniques
    
    def get_labs_for_technique(self, technique_name: str) -> List[Dict]:
        """获取练习指定技术的靶场"""
        with self.driver.session() as session:
            cypher = """
            MATCH (l:Lab)-[:PRACTICES]->(t:Technique {name: $technique_name})
            RETURN l
            ORDER BY l.difficulty
            """
            
            result = session.run(cypher, technique_name=technique_name)
            
            labs = [dict(record["l"]) for record in result]
            
            logger.info(f"找到 {len(labs)} 个相关靶场")
            return labs
    
    def get_defenses_for_technique(self, technique_name: str) -> List[Dict]:
        """获取针对指定技术的防御措施"""
        with self.driver.session() as session:
            cypher = """
            MATCH (d:Defense)-[:MITIGATES]->(t:Technique {name: $technique_name})
            RETURN d
            """
            
            result = session.run(cypher, technique_name=technique_name)
            
            defenses = [dict(record["d"]) for record in result]
            return defenses
    
    def get_statistics(self) -> Dict[str, int]:
        """获取数据库统计信息"""
        with self.driver.session() as session:
            stats = {}
            
            # 各类型节点数量
            for label in ["CVE", "Technique", "Lab", "Defense", "Tool"]:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                record = result.single()
                stats[label.lower()] = record["count"] if record else 0
            
            # 关系数量
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            record = result.single()
            stats["relationships"] = record["count"] if record else 0
            
            return stats
    
    def get_knowledge_by_id(self, node_id: str) -> Optional[Dict]:
        """根据ID获取知识点详情"""
        with self.driver.session() as session:
            cypher = """
            MATCH (n)
            WHERE elementId(n) = $node_id
            RETURN n, labels(n) as type
            """
            
            result = session.run(cypher, node_id=node_id)
            record = result.single()
            
            if not record:
                return None
            
            node = dict(record["n"])
            node["type"] = record["type"][0] if record["type"] else "Unknown"
            node["id"] = node_id
            
            return node


if __name__ == "__main__":
    logger.add("neo4j_service/logs/query.log", rotation="1 day")
    
    # 测试查询
    query_service = GraphQuery()
    
    # 搜索测试
    results = query_service.search_knowledge("SQL", limit=5)
    print(f"搜索结果: {len(results)} 个")
    
    # 统计信息
    stats = query_service.get_statistics()
    print(f"数据库统计: {stats}")
    
    query_service.close()


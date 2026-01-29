#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Neo4j知识导入模块
将爬取和筛选后的知识点导入到Neo4j图数据库
"""

import os
from typing import List, Dict, Any
from neo4j import GraphDatabase
from loguru import logger
from dotenv import load_dotenv

load_dotenv("config/.env")


class KnowledgeImporter:
    """知识导入器"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "neo4j")
        
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # 测试连接
            self.driver.verify_connectivity()
            logger.info("Neo4j连接成功")
            
            # 初始化数据库约束和索引
            self._initialize_constraints()
            
        except Exception as e:
            logger.error(f"Neo4j连接失败: {str(e)}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
    
    def _initialize_constraints(self):
        """初始化数据库约束和索引"""
        with self.driver.session() as session:
            # 创建唯一性约束
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (v:Vulnerability) REQUIRE v.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:CVE) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Technique) REQUIRE t.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Lab) REQUIRE l.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Defense) REQUIRE d.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Tool) REQUIRE t.name IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.warning(f"创建约束失败（可能已存在）: {str(e)}")
            
            logger.info("数据库约束初始化完成")
    
    def import_cve(self, cve_data: Dict[str, Any]) -> bool:
        """导入CVE漏洞"""
        try:
            with self.driver.session() as session:
                query = """
                MERGE (c:CVE {id: $id})
                SET c.name = $name,
                    c.description = $description,
                    c.severity = $severity,
                    c.cvss_score = $cvss_score,
                    c.published = $published,
                    c.url = $url,
                    c.category = $category,
                    c.tags = $tags,
                    c.updated_at = datetime()
                RETURN c
                """
                
                result = session.run(query, 
                    id=cve_data.get("id", cve_data.get("name")),
                    name=cve_data.get("name", ""),
                    description=cve_data.get("description", ""),
                    severity=cve_data.get("severity", "UNKNOWN"),
                    cvss_score=cve_data.get("cvss_score"),
                    published=cve_data.get("published", ""),
                    url=cve_data.get("url", ""),
                    category=cve_data.get("category", "漏洞库"),
                    tags=cve_data.get("tags", [])
                )
                
                logger.info(f"导入CVE: {cve_data.get('id')}")
                return True
                
        except Exception as e:
            logger.error(f"导入CVE失败: {str(e)}")
            return False
    
    def import_technique(self, tech_data: Dict[str, Any]) -> bool:
        """导入攻击技术"""
        try:
            with self.driver.session() as session:
                # 创建技术节点
                query = """
                MERGE (t:Technique {name: $name})
                SET t.description = $description,
                    t.category = $category,
                    t.severity = $severity,
                    t.mitre_id = $mitre_id,
                    t.tags = $tags,
                    t.difficulty = $difficulty,
                    t.updated_at = datetime()
                RETURN t
                """
                
                session.run(query,
                    name=tech_data.get("name", ""),
                    description=tech_data.get("description", ""),
                    category=tech_data.get("category", "未分类"),
                    severity=tech_data.get("severity", "MEDIUM"),
                    mitre_id=tech_data.get("mitre_id", ""),
                    tags=tech_data.get("tags", []),
                    difficulty=tech_data.get("difficulty", "INTERMEDIATE")
                )
                
                # 创建与防御措施的关系
                if tech_data.get("defenses"):
                    for defense in tech_data["defenses"]:
                        self._create_defense_relation(tech_data["name"], defense)
                
                # 创建与工具的关系
                if tech_data.get("tools"):
                    for tool in tech_data["tools"]:
                        self._create_tool_relation(tech_data["name"], tool)
                
                logger.info(f"导入技术: {tech_data.get('name')}")
                return True
                
        except Exception as e:
            logger.error(f"导入技术失败: {str(e)}")
            return False
    
    def import_lab(self, lab_data: Dict[str, Any]) -> bool:
        """导入靶场"""
        try:
            with self.driver.session() as session:
                query = """
                MERGE (l:Lab {name: $name})
                SET l.description = $description,
                    l.url = $url,
                    l.category = $category,
                    l.difficulty = $difficulty,
                    l.topics = $topics,
                    l.free = $free,
                    l.tags = $tags,
                    l.updated_at = datetime()
                RETURN l
                """
                
                session.run(query,
                    name=lab_data.get("name", ""),
                    description=lab_data.get("description", ""),
                    url=lab_data.get("url", ""),
                    category=lab_data.get("category", "综合靶场"),
                    difficulty=lab_data.get("difficulty", "INTERMEDIATE"),
                    topics=lab_data.get("topics", []),
                    free=lab_data.get("free", False),
                    tags=lab_data.get("tags", [])
                )
                
                # 创建与相关技术的关系
                if lab_data.get("topics"):
                    for topic in lab_data["topics"]:
                        self._create_lab_topic_relation(lab_data["name"], topic)
                
                logger.info(f"导入靶场: {lab_data.get('name')}")
                return True
                
        except Exception as e:
            logger.error(f"导入靶场失败: {str(e)}")
            return False
    
    def _create_defense_relation(self, technique_name: str, defense_name: str):
        """创建技术与防御的关系"""
        with self.driver.session() as session:
            query = """
            MATCH (t:Technique {name: $technique_name})
            MERGE (d:Defense {name: $defense_name})
            MERGE (d)-[:MITIGATES]->(t)
            """
            session.run(query, technique_name=technique_name, defense_name=defense_name)
    
    def _create_tool_relation(self, technique_name: str, tool_name: str):
        """创建技术与工具的关系"""
        with self.driver.session() as session:
            query = """
            MATCH (t:Technique {name: $technique_name})
            MERGE (tool:Tool {name: $tool_name})
            MERGE (tool)-[:USED_FOR]->(t)
            """
            session.run(query, technique_name=technique_name, tool_name=tool_name)
    
    def _create_lab_topic_relation(self, lab_name: str, topic: str):
        """创建靶场与主题的关系"""
        with self.driver.session() as session:
            # 尝试匹配已存在的技术节点
            query = """
            MATCH (l:Lab {name: $lab_name})
            OPTIONAL MATCH (t:Technique)
            WHERE t.name CONTAINS $topic OR $topic CONTAINS t.name
            WITH l, t
            WHERE t IS NOT NULL
            MERGE (l)-[:PRACTICES]->(t)
            """
            session.run(query, lab_name=lab_name, topic=topic)
    
    def import_batch(self, knowledge_list: List[Dict[str, Any]]) -> Dict[str, int]:
        """批量导入知识点"""
        
        logger.info(f"开始批量导入 {len(knowledge_list)} 个知识点")
        
        stats = {
            "cve": 0,
            "technique": 0,
            "lab": 0,
            "exploit": 0,
            "other": 0,
            "failed": 0
        }
        
        for item in knowledge_list:
            item_type = item.get("type", "").lower()
            
            try:
                if item_type == "cve":
                    if self.import_cve(item):
                        stats["cve"] += 1
                elif item_type == "technique":
                    if self.import_technique(item):
                        stats["technique"] += 1
                elif item_type == "lab":
                    if self.import_lab(item):
                        stats["lab"] += 1
                elif item_type == "exploit":
                    if self.import_cve(item):  # Exploit也作为漏洞处理
                        stats["exploit"] += 1
                else:
                    stats["other"] += 1
            except Exception as e:
                logger.error(f"导入失败: {str(e)}")
                stats["failed"] += 1
        
        logger.info(f"批量导入完成: {stats}")
        return stats
    
    def create_relations(self):
        """创建知识点之间的关系"""
        
        logger.info("开始创建知识点关系")
        
        with self.driver.session() as session:
            # CVE与技术的关联（基于标签和名称匹配）
            query = """
            MATCH (c:CVE), (t:Technique)
            WHERE any(tag IN c.tags WHERE toLower(t.name) CONTAINS toLower(tag))
               OR toLower(c.description) CONTAINS toLower(t.name)
            MERGE (c)-[:RELATED_TO]->(t)
            """
            session.run(query)
            
            # 技术之间的关联（基于类别）
            query = """
            MATCH (t1:Technique), (t2:Technique)
            WHERE t1 <> t2 AND t1.category = t2.category
            MERGE (t1)-[:SIMILAR_TO]->(t2)
            """
            session.run(query)
            
            logger.info("关系创建完成")


if __name__ == "__main__":
    logger.add("neo4j_service/logs/import.log", rotation="1 day")
    
    # 测试导入
    importer = KnowledgeImporter()
    
    # 测试数据
    test_data = [
        {
            "type": "Technique",
            "name": "SQL注入",
            "description": "通过SQL查询注入恶意代码",
            "category": "注入攻击",
            "severity": "HIGH",
            "defenses": ["输入验证", "参数化查询"],
            "tools": ["SQLMap"]
        }
    ]
    
    stats = importer.import_batch(test_data)
    print(f"导入统计: {stats}")
    
    importer.close()


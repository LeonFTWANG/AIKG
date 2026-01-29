#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整流程运行脚本
执行: 爬虫 -> Dify筛选 -> Neo4j导入
"""

import os
import sys
import json
from loguru import logger

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.security_spider import SecuritySpider
from dify_workflow.dify_client import DifyClient
from neo4j_service.knowledge_import import KnowledgeImporter


def run_pipeline():
    """运行完整流程"""
    
    logger.info("=" * 60)
    logger.info("开始运行AI安全知识图谱构建流程")
    logger.info("=" * 60)
    
    # 步骤1: 爬取数据
    logger.info("\n📡 步骤1: 爬取安全知识数据...")
    try:
        spider = SecuritySpider()
        crawled_data = spider.crawl_all(cve_keyword="web security", cve_limit=10)
        
        total_items = sum(len(v) for v in crawled_data.values())
        logger.info(f"✓ 爬取完成，共获取 {total_items} 条数据")
        
        # 合并所有数据
        all_knowledge = []
        for items in crawled_data.values():
            all_knowledge.extend(items)
        
    except Exception as e:
        logger.error(f"✗ 爬取失败: {str(e)}")
        return False
    
    # 步骤2: Dify筛选
    logger.info("\n🤖 步骤2: 使用Dify工作流筛选知识点...")
    try:
        dify_client = DifyClient()
        filtered_knowledge = dify_client.batch_filter(all_knowledge)
        
        logger.info(f"✓ 筛选完成，保留 {len(filtered_knowledge)} 条有效知识")
        
    except Exception as e:
        logger.warning(f"⚠️  Dify筛选失败，使用原始数据: {str(e)}")
        filtered_knowledge = all_knowledge
    
    # 步骤3: 导入Neo4j
    logger.info("\n💾 步骤3: 导入知识到Neo4j图数据库...")
    try:
        importer = KnowledgeImporter()
        
        # 批量导入
        stats = importer.import_batch(filtered_knowledge)
        logger.info(f"✓ 导入完成: {stats}")
        
        # 创建关系
        logger.info("创建知识点之间的关系...")
        importer.create_relations()
        logger.info("✓ 关系创建完成")
        
        importer.close()
        
    except Exception as e:
        logger.error(f"✗ Neo4j导入失败: {str(e)}")
        return False
    
    # 完成
    logger.info("\n" + "=" * 60)
    logger.info("✅ 知识图谱构建完成！")
    logger.info("=" * 60)
    logger.info("\n统计信息:")
    logger.info(f"  • 爬取数据: {total_items} 条")
    logger.info(f"  • 筛选后: {len(filtered_knowledge)} 条")
    logger.info(f"  • CVE: {stats.get('cve', 0)} 个")
    logger.info(f"  • 技术: {stats.get('technique', 0)} 个")
    logger.info(f"  • 靶场: {stats.get('lab', 0)} 个")
    logger.info(f"  • 其他: {stats.get('other', 0)} 个")
    logger.info("\n下一步:")
    logger.info("  1. 启动后端API: python backend/main.py")
    logger.info("  2. 启动前端: cd frontend && npm run dev")
    logger.info("  3. 访问: http://localhost:3000")
    
    return True


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/pipeline.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )
    
    # 运行流程
    success = run_pipeline()
    
    sys.exit(0 if success else 1)


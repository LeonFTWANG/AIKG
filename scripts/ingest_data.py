#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据摄入脚本
连接爬虫、Dify和Neo4j导入器，完成数据从采集到存储的全流程
"""

import os
import sys
import asyncio
import argparse
from loguru import logger
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.security_spider import SecuritySpider
from dify_workflow.dify_client import DifyClient
from neo4j_service.knowledge_import import KnowledgeImporter

# 加载配置
load_dotenv("config/.env")

def ingest_data(keyword=None, limit=10, use_ai=True):
    """
    执行数据摄入流程
    1. 爬虫采集
    2. AI处理 (可选)
    3. 数据库导入
    """
    logger.info("开始数据摄入流程...")
    
    # 1. 初始化组件
    spider = SecuritySpider()
    
    try:
        importer = KnowledgeImporter()
    except Exception as e:
        logger.error(f"无法连接Neo4j，请确保数据库已启动: {str(e)}")
        return
    
    # 2. 采集数据
    logger.info("步骤 1/3: 采集数据...")
    crawled_data = spider.crawl_all(cve_keyword=keyword, cve_limit=limit)
    
    all_items = []
    all_items.extend(crawled_data.get("cves", []))
    all_items.extend(crawled_data.get("labs", []))
    all_items.extend(crawled_data.get("techniques", []))
    # all_items.extend(crawled_data.get("exploits", []))
    
    logger.info(f"采集完成，共 {len(all_items)} 条原始数据")
    
    # 3. AI处理
    processed_items = []
    
    # 检查是否已在爬虫阶段完成清洗 (通过 DIFY_CLEANING_API_KEY)
    if use_ai and os.getenv("DIFY_CLEANING_API_KEY"):
        logger.info("步骤 2/3: 检测到 DIFY_CLEANING_API_KEY，数据已在爬虫阶段清洗，跳过二次处理...")
        processed_items = all_items
    else:
        logger.info("步骤 2/3: 未配置爬虫清洗或禁用AI，使用默认规则处理...")
        # 使用默认规则处理 (不依赖 DIFY_API_KEY)
        dify_client = DifyClient()
        for item in all_items:
            processed_items.append(dify_client._default_filter(item))
            
    # 4. 导入数据库
    logger.info(f"步骤 3/3: 导入Neo4j ({len(processed_items)} 条)...")
    stats = importer.import_batch(processed_items)
    
    # 5. 创建关系
    logger.info("创建知识关联...")
    importer.create_relations()
    
    importer.close()
    logger.info(f"数据摄入完成! 统计: {stats}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIKG 数据摄入脚本")
    parser.add_argument("--keyword", type=str, help="CVE搜索关键词")
    parser.add_argument("--limit", type=int, default=10, help="每类数据采集数量限制")
    parser.add_argument("--no-ai", action="store_true", help="禁用AI处理")
    
    args = parser.parse_args()
    
    # 配置日志
    logger.add("scripts/logs/ingest.log", rotation="1 day")
    
    ingest_data(
        keyword=args.keyword,
        limit=args.limit,
        use_ai=not args.no_ai
    )

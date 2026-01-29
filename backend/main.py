#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
后端API主应用
FastAPI服务，提供RESTful API
"""

import os
import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from loguru import logger
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j_service.graph_query import GraphQuery
from backend.llm_service import LLMService
from backend.auth import (
    Token, User, UserInDB, create_access_token, 
    get_current_user, get_password_hash, verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

load_dotenv("config/.env")

# 创建FastAPI应用
app = FastAPI(
    title="AI Security Knowledge Graph API",
    description="安全知识图谱API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        os.getenv("FRONTEND_URL", "http://localhost:3000")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
graph_query = None
llm_service = None


# Pydantic模型
class SearchRequest(BaseModel):
    query: str
    limit: int = 10


class LLMQueryRequest(BaseModel):
    question: str
    context_depth: int = 2
    conversation_id: Optional[str] = None

class ConversationCreate(BaseModel):
    title: str = "New Chat"


class KnowledgeNode(BaseModel):
    name: str
    type: str
    description: Optional[str] = ""


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    global graph_query, llm_service
    
    logger.info("正在启动API服务...")
    
    try:
        graph_query = GraphQuery()
        logger.info("Neo4j查询服务已初始化")
    except Exception as e:
        logger.error(f"Neo4j初始化失败: {str(e)}")
    
    try:
        llm_service = LLMService(graph_query)
        logger.info("LLM服务已初始化")
    except Exception as e:
        logger.error(f"LLM初始化失败: {str(e)}")
    
    logger.info("API服务启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global graph_query
    
    if graph_query:
        graph_query.close()
    
    logger.info("API服务已关闭")


@app.post("/api/auth/register", response_model=Token)
async def register(user: User):
    """用户注册"""
    if not graph_query:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    # 检查用户是否存在并创建
    hashed_password = get_password_hash(user.password)
    if not graph_query.create_user(user.username, hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # 生成token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录"""
    if not graph_query:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    # 验证用户
    stored_hash = graph_query.get_user_password(form_data.username)
    if not stored_hash or not verify_password(form_data.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI Security Knowledge Graph API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "neo4j": graph_query is not None,
        "llm": llm_service is not None
    }


@app.get("/api/statistics")
async def get_statistics():
    """获取统计信息"""
    if not graph_query:
        raise HTTPException(status_code=503, detail="图数据库服务不可用")
    
    try:
        stats = graph_query.get_statistics()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"获取统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge/search")
async def search_knowledge(request: SearchRequest):
    """搜索知识点"""
    if not graph_query:
        raise HTTPException(status_code=503, detail="图数据库服务不可用")
    
    try:
        results = graph_query.search_knowledge(request.query, request.limit)
        return {
            "success": True,
            "data": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge/{node_id}")
async def get_knowledge_detail(node_id: str):
    """获取知识点详情"""
    if not graph_query:
        raise HTTPException(status_code=503, detail="图数据库服务不可用")
    
    try:
        node = graph_query.get_knowledge_by_id(node_id)
        if not node:
            raise HTTPException(status_code=404, detail="知识点不存在")
        
        return {"success": True, "data": node}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge/{node_name}/related")
async def get_related_knowledge(
    node_name: str,
    depth: int = Query(default=2, ge=1, le=5)
):
    """获取相关知识点"""
    if not graph_query:
        raise HTTPException(status_code=503, detail="图数据库服务不可用")
    
    try:
        result = graph_query.get_related_knowledge(node_name, depth)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"获取相关知识失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/visualization")
async def get_graph_visualization(
    limit: int = Query(default=100, ge=10, le=500)
):
    """获取图谱可视化数据"""
    if not graph_query:
        raise HTTPException(status_code=503, detail="图数据库服务不可用")
    
    try:
        data = graph_query.get_graph_for_visualization(limit)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"获取可视化数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/learning-path")
async def get_learning_path(
    start: str = Query(..., description="起始主题"),
    end: str = Query(..., description="目标主题")
):
    """获取学习路径"""
    if not graph_query:
        raise HTTPException(status_code=503, detail="图数据库服务不可用")
    
    try:
        path = graph_query.get_learning_path(start, end)
        return {
            "success": True,
            "data": path,
            "steps": len(path)
        }
    except Exception as e:
        logger.error(f"获取学习路径失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/techniques/{severity}")
async def get_techniques_by_severity(severity: str):
    """根据严重程度获取技术"""
    if not graph_query:
        raise HTTPException(status_code=503, detail="图数据库服务不可用")
    
    try:
        techniques = graph_query.get_techniques_by_severity(severity.upper())
        return {
            "success": True,
            "data": techniques,
            "count": len(techniques)
        }
    except Exception as e:
        logger.error(f"获取技术列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/labs")
async def get_labs(
    technique: Optional[str] = Query(None, description="技术名称")
):
    """获取靶场列表"""
    if not graph_query:
        raise HTTPException(status_code=503, detail="图数据库服务不可用")
    
    try:
        if technique:
            labs = graph_query.get_labs_for_technique(technique)
        else:
            # 获取所有靶场
            labs = graph_query.search_knowledge("", limit=100)
            labs = [lab for lab in labs if lab.get("type") == "Lab"]
        
        return {
            "success": True,
            "data": labs,
            "count": len(labs)
        }
    except Exception as e:
        logger.error(f"获取靶场列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/llm/query")
async def llm_query(
    request: LLMQueryRequest,
    current_user: str = Depends(get_current_user)
):
    """LLM问答 (需认证)"""
    if not llm_service:
        raise HTTPException(status_code=503, detail="LLM服务不可用")
    
    try:
        response = llm_service.query(
            question=request.question,
            context_depth=request.context_depth,
            user_id=current_user,
            conversation_id=request.conversation_id
        )
        return {"success": True, "data": response}
    except Exception as e:
        logger.error(f"LLM查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/conversations")
async def create_conversation(
    request: ConversationCreate,
    current_user: str = Depends(get_current_user)
):
    """创建新对话"""
    if not graph_query:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    try:
        conversation = graph_query.create_conversation(current_user, request.title)
        return {"success": True, "data": conversation}
    except Exception as e:
        logger.error(f"创建对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/conversations")
async def get_conversations(
    current_user: str = Depends(get_current_user)
):
    """获取用户对话列表"""
    if not graph_query:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    try:
        conversations = graph_query.get_user_conversations(current_user)
        return {"success": True, "data": conversations}
    except Exception as e:
        logger.error(f"获取对话列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    current_user: str = Depends(get_current_user)
):
    """获取对话消息记录"""
    if not graph_query:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    try:
        # TODO: Verify user owns conversation (omitted for simplicity, but recommended)
        messages = graph_query.get_conversation_messages(conversation_id)
        return {"success": True, "data": messages}
    except Exception as e:
        logger.error(f"获取消息记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: str = Depends(get_current_user)
):
    """删除指定对话"""
    if not graph_query:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    try:
        success = graph_query.delete_conversation(conversation_id, current_user)
        if success:
            return {"success": True, "message": "对话已删除"}
        else:
            raise HTTPException(status_code=404, detail="对话不存在或无权删除")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/defenses/{technique_name}")
async def get_defenses(technique_name: str):
    """获取防御措施"""
    if not graph_query:
        raise HTTPException(status_code=503, detail="图数据库服务不可用")
    
    try:
        defenses = graph_query.get_defenses_for_technique(technique_name)
        return {
            "success": True,
            "data": defenses,
            "count": len(defenses)
        }
    except Exception as e:
        logger.error(f"获取防御措施失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # 配置日志
    logger.add(
        "backend/logs/api.log",
        rotation="1 day",
        retention="7 days",
        level="INFO"
    )
    
    # 启动服务
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8000))
    
    logger.info(f"启动FastAPI服务: {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )


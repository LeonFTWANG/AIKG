# 安全知识图谱系统 (AI Security Knowledge Graph)

一个基于AI和知识图谱的智能安全学习平台，集成爬虫、Dify工作流、Neo4j图数据库和大语言模型。

## 项目特性

- **智能爬虫**: 自动爬取多源安全知识点（CVE、靶场、漏洞库等）
- **AI筛选**: 通过Dify工作流智能筛选和归类安全知识
- **知识图谱**: 使用Neo4j构建安全知识关系网络
- **LLM增强**: 集成大语言模型进行知识整合和问答
- **可视化**: 交互式知识图谱可视化展示
- **资源链接**: 自动关联靶场和漏洞库资源

## 系统架构

```
┌─────────────────┐
│   Web爬虫层      │ → 爬取安全知识、CVE、靶场信息
└────────┬────────┘
         ↓
┌─────────────────┐
│  Dify工作流层    │ → AI筛选、分类、标注知识点
└────────┬────────┘
         ↓
┌─────────────────┐
│   Neo4j图库     │ → 存储知识图谱关系
└────────┬────────┘
         ↓
┌─────────────────┐
│   后端API层     │ → FastAPI + LLM集成
└────────┬────────┘
         ↓
┌─────────────────┐
│   前端Web层     │ → React + D3.js可视化
└─────────────────┘
```

## 项目结构

```
aikg/
├── crawler/              # 爬虫模块
│   ├── security_spider.py    # 主爬虫
│   ├── sources/              # 数据源配置
│   └── parsers/              # 解析器
├── dify_workflow/        # Dify工作流配置
│   ├── workflow_config.json  # 工作流配置
│   └── dify_client.py        # Dify API客户端
├── neo4j_service/        # Neo4j服务
│   ├── knowledge_import.py   # 知识导入
│   ├── graph_query.py        # 图查询
│   └── models.py             # 数据模型
├── backend/              # 后端API
│   ├── main.py              # FastAPI主应用
│   ├── api/                 # API路由
│   ├── llm_service.py       # LLM服务
│   └── config.py            # 配置
├── frontend/             # 前端应用
│   ├── src/
│   │   ├── components/      # React组件
│   │   ├── pages/           # 页面
│   │   └── utils/           # 工具函数
│   └── package.json
├── config/               # 配置文件
├── requirements.txt      # Python依赖
└── docker-compose.yml    # Docker编排
```

## 快速开始

### 前置要求

- Python 3.9+
- Node.js 16+
- Neo4j 5.0+
- Dify API访问权限
- OpenAI/其他LLM API密钥

### 安装步骤

1. **克隆项目**
```bash
git clone <your-repo>
cd aikg
```

2. **安装Python依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp config/.env.example config/.env
# 编辑 config/.env 填入必要的配置
```

4. **启动Neo4j**

使用Docker:
```bash
docker-compose up -d neo4j
```

或本地安装:
- Windows推荐: Neo4j Desktop
- Linux: apt/yum安装
- macOS: brew安装

5. **运行爬虫**
```bash
python crawler/security_spider.py
```

6. **启动后端**
```bash
cd backend
python main.py
```

7. **启动前端**
```bash
cd frontend
npm install
npm start
```

## 配置说明（config/env可以替换为你的数据就好）

### 1. Neo4j配置
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### 2. Dify配置
```env
DIFY_API_BASE=http://localhost:8333/v1
DIFY_CLEANING_API_KEY=app-xxxxxx
```

### 3. LLM配置
```env
OPENAI_API_KEY=your_ai_key
# 或使用其他模型
LLM_MODEL=gpt-4
```
## 数据源

目前系统支持从以下源爬取安全知识：

- **CVE数据库**: 漏洞详情
- **CNVD/CNNVD**: 国家漏洞库
- **exploit-db**: 漏洞利用代码
- **HackTheBox/VulnHub**: 靶场信息
- **OWASP**: 安全最佳实践
- **安全博客**: FreeBuf、先知社区等

## 功能展示

### 1. 知识图谱可视化
- 节点：安全概念、漏洞、攻击技术
- 关系：影响、利用、防御、关联

### 2. AI问答
- 输入安全问题
- LLM基于知识图谱生成答案
- 展示相关知识点路径

### 3. 学习路径
- 自动生成学习路线
- 推荐相关靶场练习
- 提供漏洞库参考

## 知识图谱模型

### 节点类型
- `Vulnerability`: 漏洞
- `Technique`: 攻击技术
- `Defense`: 防御方法
- `Tool`: 安全工具
- `Lab`: 靶场
- `CVE`: CVE编号

### 关系类型
- `EXPLOITS`: 利用关系
- `MITIGATES`: 缓解关系
- `RELATES_TO`: 相关关系
- `PRACTICES_IN`: 实践关系
- `USES`: 使用关系

## API文档

启动后端后访问: `http://localhost:8000/docs`

主要端点：
- `GET /api/knowledge/search`: 搜索知识点
- `GET /api/knowledge/graph`: 获取图谱数据
- `POST /api/llm/query`: LLM问答
- `GET /api/labs`: 获取靶场列表
- `GET /api/vulnerabilities/{id}`: 获取漏洞详情

## 技术栈

**后端**:
- FastAPI - Web框架
- Neo4j - 图数据库
- LangChain - LLM编排
- Scrapy - 爬虫框架
- Dify SDK - AI工作流

**前端**:
- React 18
- D3.js / Vis.js - 图谱可视化
- Ant Design - UI组件
- Axios - HTTP客户端

**⚠️ 免责声明**: 本项目仅用于安全学习和研究，请勿用于非法用途。


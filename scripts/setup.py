#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目初始化脚本
创建必要的目录和配置文件
"""

import os
import sys

def create_directories():
    """创建必要的目录"""
    directories = [
        "crawler/data",
        "crawler/logs",
        "dify_workflow/logs",
        "neo4j_service/logs",
        "backend/logs",
        "backend/api",
        "logs",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ 创建目录: {directory}")

def create_env_file():
    """创建.env文件（如果不存在）"""
    env_path = "config/.env"
    example_path = "config/.env.example"
    
    if not os.path.exists(env_path):
        if os.path.exists(example_path):
            with open(example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 创建配置文件: {env_path}")
            print("⚠️  请编辑 config/.env 填入必要的配置信息")
        else:
            print(f"⚠️  未找到 {example_path}，跳过创建.env文件")
    else:
        print(f"✓ 配置文件已存在: {env_path}")

def create_gitignore():
    """创建.gitignore文件"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.venv
config/.env

# Logs
*.log
logs/
crawler/logs/
dify_workflow/logs/
neo4j_service/logs/
backend/logs/

# Data
crawler/data/
*.db
*.sqlite

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Node
node_modules/
npm-debug.log
yarn-error.log
frontend/dist/
frontend/build/

# OS
.DS_Store
Thumbs.db

# Neo4j
data/
"""
    
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    print("✓ 创建 .gitignore 文件")

def create_init_files():
    """创建__init__.py文件"""
    init_files = [
        "crawler/__init__.py",
        "dify_workflow/__init__.py",
        "neo4j_service/__init__.py",
        "backend/__init__.py",
        "backend/api/__init__.py",
    ]
    
    for init_file in init_files:
        os.makedirs(os.path.dirname(init_file), exist_ok=True)
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("")
            print(f"✓ 创建 {init_file}")

def main():
    """主函数"""
    print("=" * 50)
    print("AI Security Knowledge Graph - 项目初始化")
    print("=" * 50)
    print()
    
    # 创建目录
    print("1. 创建项目目录...")
    create_directories()
    print()
    
    # 创建__init__.py
    print("2. 创建Python包文件...")
    create_init_files()
    print()
    
    # 创建环境配置
    print("3. 创建环境配置...")
    create_env_file()
    print()
    
    # 创建.gitignore
    print("4. 创建.gitignore...")
    create_gitignore()
    print()
    
    print("=" * 50)
    print("✅ 初始化完成！")
    print()
    print("下一步:")
    print("1. 编辑 config/.env 填入必要的配置（Neo4j、Dify、OpenAI等）")
    print("2. 安装Python依赖: pip install -r requirements.txt")
    print("3. 启动Neo4j: docker-compose up -d neo4j")
    print("4. 运行爬虫: python crawler/security_spider.py")
    print("5. 启动后端: python backend/main.py")
    print("6. 启动前端: cd frontend && npm install && npm run dev")
    print("=" * 50)

if __name__ == "__main__":
    main()


#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全知识爬虫主模块
支持多源爬取：CVE、CNVD、exploit-db、靶场信息等
"""

import asyncio
import json
from typing import List, Dict, Any
from loguru import logger
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import os


class SecuritySpider:
    """安全知识爬虫"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.results = []
        
    def clean_data_with_dify(self, raw_text: str) -> Dict:
        """
        使用Dify工作流清洗数据
        """
        api_key = os.getenv("DIFY_CLEANING_API_KEY")
        api_base = os.getenv("DIFY_API_BASE", "http://localhost:8333/v1")
        
        if not api_key:
            logger.warning("未配置DIFY_CLEANING_API_KEY，跳过清洗")
            return None
            
        url = f"{api_base}/workflows/run"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": {"raw_text": raw_text},
            "response_mode": "blocking",
            "user": "spider_bot"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                # 解析工作流输出
                # 假设工作流输出变量名为 'result'
                cleaned_text = result.get("data", {}).get("outputs", {}).get("result", "")
                
                # 尝试解析JSON
                try:
                    # 清理可能的markdown标记
                    cleaned_text = cleaned_text.replace("```json", "").replace("```", "").strip()
                    return json.loads(cleaned_text)
                except json.JSONDecodeError:
                    logger.warning(f"Dify返回的不是有效JSON: {cleaned_text[:100]}...")
                    return None
            else:
                logger.error(f"Dify请求失败: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"调用Dify失败: {str(e)}")
            return None

    def crawl_cve(self, keyword: str = None, limit: int = 10) -> List[Dict]:
        """
        爬取CVE漏洞信息
        使用NVD API (https://nvd.nist.gov/developers/vulnerabilities)
        """
        logger.info(f"开始爬取CVE数据，关键词: {keyword}, 限制: {limit}")
        
        try:
            # CVE API endpoint
            base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
            params = {
                "resultsPerPage": limit
            }
            
            if keyword:
                params["keywordSearch"] = keyword
            
            response = self.session.get(base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                cves = []
                
                for item in data.get("vulnerabilities", [])[:limit]:
                    cve = item.get("cve", {})
                    cve_id = cve.get("id", "")
                    
                    descriptions = cve.get("descriptions", [])
                    description = descriptions[0].get("value", "") if descriptions else ""
                    
                    # 尝试使用Dify清洗数据
                    raw_text = f"CVE ID: {cve_id}\nDescription: {description}"
                    cleaned_data = self.clean_data_with_dify(raw_text)
                    
                    if cleaned_data:
                        logger.info(f"Dify清洗成功: {cve_id}")
                        # 合并清洗后的数据，保留关键ID
                        cve_info = {
                            "id": cve_id,
                            "type": "CVE",
                            "name": cleaned_data.get("name", cve_id),
                            "description": cleaned_data.get("description", description),
                            "severity": cleaned_data.get("severity"), # 优先使用清洗后的严重程度
                            "tags": cleaned_data.get("tags", []),
                            "crawled_at": datetime.now().isoformat()
                        }
                    else:
                        # 降级处理：使用原始数据
                        metrics = cve.get("metrics", {})
                        cvss_score = None
                        severity = None
                        
                        if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
                            cvss_data = metrics["cvssMetricV31"][0].get("cvssData", {})
                            cvss_score = cvss_data.get("baseScore")
                            severity = cvss_data.get("baseSeverity")
                            
                        cve_info = {
                            "id": cve_id,
                            "type": "CVE",
                            "name": cve_id,
                            "description": description,
                            "severity": severity,
                            "cvss_score": cvss_score,
                            "published": cve.get("published", ""),
                            "source": "NVD",
                            "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                            "crawled_at": datetime.now().isoformat()
                        }
                    
                    cves.append(cve_info)
                    logger.info(f"爬取CVE: {cve_id}")
                
                return cves
            else:
                logger.error(f"CVE API请求失败: {response.status_code}, URL: {response.url}")
                logger.error(f"响应内容: {response.text[:200]}")
                return []
                
        except Exception as e:
            logger.error(f"爬取CVE数据失败: {str(e)}")
            return []
    
    def crawl_exploit_db(self, limit: int = 10) -> List[Dict]:
        """
        爬取Exploit-DB漏洞利用信息
        """
        # ... (保持原样，或者同样添加清洗逻辑)
        return []
    
    def crawl_labs(self) -> List[Dict]:
        """
        爬取靶场信息
        """
        logger.info("收集靶场信息")
        
        # 这里提供常见靶场的静态信息
        # 实际项目中可以从靶场网站爬取更多详情
        labs = [
            {
                "type": "Lab",
                "name": "HackTheBox",
                "description": "渗透测试实验室平台，提供各种难度的靶机",
                "category": "综合靶场",
                "difficulty": "初级到高级",
                "url": "https://www.hackthebox.com",
                "topics": ["Web安全", "系统渗透", "网络安全", "逆向工程"],
                "free": False
            },
            {
                "type": "Lab",
                "name": "VulnHub",
                "description": "提供可下载的漏洞虚拟机进行本地练习",
                "category": "虚拟机靶场",
                "difficulty": "初级到高级",
                "url": "https://www.vulnhub.com",
                "topics": ["Web安全", "系统渗透", "权限提升"],
                "free": True
            },
            {
                "type": "Lab",
                "name": "PortSwigger Web Security Academy",
                "description": "Web安全学习平台，包含大量Web漏洞实验",
                "category": "Web安全",
                "difficulty": "初级到专家",
                "url": "https://portswigger.net/web-security",
                "topics": ["SQL注入", "XSS", "CSRF", "XXE", "SSRF"],
                "free": True
            },
            {
                "type": "Lab",
                "name": "TryHackMe",
                "description": "互动式网络安全学习平台",
                "category": "综合靶场",
                "difficulty": "初级到高级",
                "url": "https://tryhackme.com",
                "topics": ["渗透测试", "取证分析", "Web安全", "网络安全"],
                "free": True
            },
            {
                "type": "Lab",
                "name": "PentesterLab",
                "description": "渗透测试实验室，提供系统化的学习路径",
                "category": "渗透测试",
                "difficulty": "初级到高级",
                "url": "https://pentesterlab.com",
                "topics": ["Web安全", "渗透测试", "代码审计"],
                "free": False
            },
            {
                "type": "Lab",
                "name": "DVWA",
                "description": "Damn Vulnerable Web Application - 故意存在漏洞的Web应用",
                "category": "Web安全",
                "difficulty": "初级到中级",
                "url": "https://github.com/digininja/DVWA",
                "topics": ["SQL注入", "XSS", "命令注入", "文件包含"],
                "free": True
            },
            {
                "type": "Lab",
                "name": "WebGoat",
                "description": "OWASP开发的Web安全学习平台",
                "category": "Web安全",
                "difficulty": "初级到中级",
                "url": "https://owasp.org/www-project-webgoat/",
                "topics": ["OWASP Top 10", "安全编码", "Web漏洞"],
                "free": True
            }
        ]
        
        for lab in labs:
            lab["crawled_at"] = datetime.now().isoformat()
        
        logger.info(f"收集了 {len(labs)} 个靶场信息")
        return labs
    
    def crawl_security_techniques(self) -> List[Dict]:
        """
        爬取安全攻击技术（基于MITRE ATT&CK等）
        """
        logger.info("收集安全攻击技术")
        
        # 这里提供一些常见的安全技术
        # 实际可以从MITRE ATT&CK API获取
        techniques = [
            {
                "type": "Technique",
                "name": "SQL注入",
                "description": "通过在SQL查询中注入恶意SQL代码来攻击数据库",
                "category": "注入攻击",
                "severity": "HIGH",
                "mitre_id": "T1190",
                "defenses": ["输入验证", "参数化查询", "最小权限原则"],
                "tools": ["SQLMap", "Havij"],
                "related_cves": ["CVE-2021-XXXX"]
            },
            {
                "type": "Technique",
                "name": "跨站脚本攻击(XSS)",
                "description": "在网页中注入恶意脚本，当其他用户浏览该页面时执行",
                "category": "注入攻击",
                "severity": "MEDIUM",
                "mitre_id": "T1059",
                "defenses": ["输出编码", "CSP策略", "输入过滤"],
                "tools": ["XSSer", "BeEF"],
                "related_cves": []
            },
            {
                "type": "Technique",
                "name": "跨站请求伪造(CSRF)",
                "description": "诱使用户在已认证的Web应用上执行非预期操作",
                "category": "Web攻击",
                "severity": "MEDIUM",
                "mitre_id": "",
                "defenses": ["CSRF Token", "Same-Site Cookie", "验证Referer"],
                "tools": [],
                "related_cves": []
            },
            {
                "type": "Technique",
                "name": "命令注入",
                "description": "在应用程序中注入操作系统命令",
                "category": "注入攻击",
                "severity": "CRITICAL",
                "mitre_id": "T1059",
                "defenses": ["输入验证", "避免调用系统命令", "最小权限"],
                "tools": ["Commix"],
                "related_cves": []
            },
            {
                "type": "Technique",
                "name": "文件包含漏洞",
                "description": "通过包含恶意文件执行任意代码",
                "category": "Web攻击",
                "severity": "HIGH",
                "mitre_id": "",
                "defenses": ["路径验证", "白名单机制"],
                "tools": [],
                "related_cves": []
            },
            {
                "type": "Technique",
                "name": "XXE(XML外部实体注入)",
                "description": "利用XML解析器的外部实体引用功能",
                "category": "注入攻击",
                "severity": "HIGH",
                "mitre_id": "",
                "defenses": ["禁用外部实体", "使用安全的XML解析器"],
                "tools": [],
                "related_cves": []
            },
            {
                "type": "Technique",
                "name": "SSRF(服务端请求伪造)",
                "description": "利用服务器发起恶意请求",
                "category": "Web攻击",
                "severity": "HIGH",
                "mitre_id": "T1090",
                "defenses": ["URL白名单", "网络隔离", "禁止私有IP访问"],
                "tools": [],
                "related_cves": []
            },
            {
                "type": "Technique",
                "name": "反序列化漏洞",
                "description": "通过恶意序列化数据执行任意代码",
                "category": "代码执行",
                "severity": "CRITICAL",
                "mitre_id": "",
                "defenses": ["避免反序列化不可信数据", "类型检查"],
                "tools": ["ysoserial"],
                "related_cves": []
            }
        ]
        
        for tech in techniques:
            tech["crawled_at"] = datetime.now().isoformat()
        
        logger.info(f"收集了 {len(techniques)} 个安全技术")
        return techniques
    
    def crawl_all(self, cve_keyword: str = None, cve_limit: int = 10) -> Dict[str, List]:
        """
        执行全部爬取任务
        """
        logger.info("开始执行全部爬取任务")
        
        results = {
            "cves": [],
            "exploits": [],
            "labs": [],
            "techniques": []
        }
        
        # 爬取CVE
        try:
            results["cves"] = self.crawl_cve(keyword=cve_keyword, limit=cve_limit)
            time.sleep(2)  # 避免请求过快
        except Exception as e:
            logger.error(f"CVE爬取失败: {str(e)}")
        
        # 爬取Exploit（可选，因为网站可能有反爬）
        # try:
        #     results["exploits"] = self.crawl_exploit_db(limit=10)
        #     time.sleep(2)
        # except Exception as e:
        #     logger.error(f"Exploit爬取失败: {str(e)}")
        
        # 收集靶场信息
        results["labs"] = self.crawl_labs()
        
        # 收集安全技术
        results["techniques"] = self.crawl_security_techniques()
        
        # 保存结果
        self._save_results(results)
        
        total = sum(len(v) for v in results.values())
        logger.info(f"爬取任务完成，共获取 {total} 条数据")
        
        return results
    
    def _save_results(self, results: Dict[str, List]):
        """保存爬取结果到JSON文件"""
        output_file = f"crawler/data/crawled_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import os
        os.makedirs("crawler/data", exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"结果已保存到: {output_file}")


if __name__ == "__main__":
    # 配置日志
    logger.add("crawler/logs/spider.log", rotation="1 day")
    
    # 创建爬虫实例
    spider = SecuritySpider()
    
    # 执行爬取
    results = spider.crawl_all(cve_keyword="sql injection", cve_limit=5)
    
    # 打印统计
    print("\n" + "="*50)
    print("爬取统计:")
    print(f"CVE漏洞: {len(results['cves'])} 条")
    print(f"Exploit: {len(results['exploits'])} 条")
    print(f"靶场: {len(results['labs'])} 个")
    print(f"攻击技术: {len(results['techniques'])} 个")
    print("="*50)


#!/usr/bin/env python3
"""
网站描述自动生成工具
自动读取网站信息并生成对应描述，更新webstack.yml文件
"""

import yaml
import requests
import time
import argparse
import sys
import os
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json
from bs4 import BeautifulSoup
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class WebsiteDescriptionGenerator:
    def __init__(self, webstack_file: str, timeout: int = 10, retries: int = 3):
        """
        初始化网站描述生成器
        
        Args:
            webstack_file: webstack.yml 文件路径
            timeout: 请求超时时间（秒）
            retries: 重试次数
        """
        self.webstack_file = webstack_file
        self.timeout = timeout
        self.retries = retries
        
        # 配置会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 配置重试策略
        retry_strategy = Retry(
            total=retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def load_webstack_data(self) -> List[Dict]:
        """加载webstack.yml文件数据"""
        try:
            with open(self.webstack_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data
        except FileNotFoundError:
            print(f"错误: 找不到文件 {self.webstack_file}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"错误: YAML 文件格式错误: {e}")
            sys.exit(1)

    def extract_website_info(self, url: str) -> Dict[str, str]:
        """
        从网站提取信息生成描述
        
        Args:
            url: 网站URL
            
        Returns:
            包含网站信息的字典
        """
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取网站标题
            title = None
            if soup.title:
                title = soup.title.string.strip() if soup.title.string else None
            
            # 提取meta描述
            meta_description = None
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                meta_description = meta_desc.get('content').strip()
            
            # 提取meta关键词
            meta_keywords = None
            meta_keys = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keys and meta_keys.get('content'):
                meta_keywords = meta_keys.get('content').strip()
                
            # 提取OG描述
            og_description = None
            og_desc = soup.find('meta', property='og:description')
            if og_desc and og_desc.get('content'):
                og_description = og_desc.get('content').strip()
                
            # 提取OG标题
            og_title = None
            og_t = soup.find('meta', property='og:title')
            if og_t and og_t.get('content'):
                og_title = og_t.get('content').strip()
                
            # 提取主要内容文字（前200字符）
            main_text = None
            # 移除脚本和样式标签
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            # 清理文本
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            if text and len(text) > 50:
                main_text = text[:200] + "..." if len(text) > 200 else text
                
            return {
                'title': title,
                'meta_description': meta_description,
                'og_description': og_description,
                'og_title': og_title,
                'meta_keywords': meta_keywords,
                'main_text': main_text,
                'status': 'success'
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': str(e)
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f"解析错误: {str(e)}"
            }

    def generate_description(self, website_info: Dict[str, str], title: str, url: str) -> Optional[str]:
        """
        根据网站信息生成描述
        
        Args:
            website_info: 网站信息字典
            title: 网站在配置中的标题
            url: 网站URL
            
        Returns:
            生成的描述文本，如果无法访问则返回None
        """
        if website_info['status'] == 'error':
            return None
        
        # 优先级顺序：meta描述 > OG描述 > 网站标题 > 主要文本内容
        description_sources = [
            website_info.get('meta_description'),
            website_info.get('og_description'),
            website_info.get('og_title'),
            website_info.get('title'),
            website_info.get('main_text')
        ]
        
        # 选择第一个有效的描述
        for desc in description_sources:
            if desc and len(desc.strip()) > 10:  # 至少10个字符
                # 清理描述文本
                cleaned_desc = re.sub(r'\s+', ' ', desc).strip()
                # 如果描述太长，截断
                if len(cleaned_desc) > 100:
                    cleaned_desc = cleaned_desc[:100] + "..."
                return cleaned_desc
        
        # 如果没有找到合适的描述，使用域名生成默认描述
        domain = urlparse(url).netloc
        return f"{title} - {domain}"

    def update_descriptions(self, only_null: bool = True, max_workers: int = 5) -> Dict:
        """
        更新webstack.yml中的描述
        
        Args:
            only_null: 是否仅更新description为null的条目
            max_workers: 并发工作线程数
            
        Returns:
            更新结果统计
        """
        data = self.load_webstack_data()
        
        # 收集需要更新的链接
        links_to_update = []
        for category in data:
            for term_group in category.get('list', []):
                for link in term_group.get('links', []):
                    if only_null and link.get('description') is not None:
                        continue
                    if link.get('url'):
                        links_to_update.append({
                            'category': category.get('taxonomy'),
                            'term': term_group.get('term'),
                            'title': link.get('title'),
                            'url': link.get('url'),
                            'link_obj': link
                        })
        
        print(f"找到 {len(links_to_update)} 个需要更新的链接")
        
        updated_count = 0
        failed_count = 0
        
        # 并发处理链接
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            future_to_link = {
                executor.submit(self.extract_website_info, link['url']): link 
                for link in links_to_update
            }
            
            # 处理结果
            for future in as_completed(future_to_link):
                link = future_to_link[future]
                try:
                    website_info = future.result()
                    description = self.generate_description(
                        website_info, 
                        link['title'], 
                        link['url']
                    )
                    
                    # 更新描述（如果无法访问则保持为null）
                    if description is not None:
                        link['link_obj']['description'] = description
                        updated_count += 1
                        print(f"✓ {link['title']}: {description}")
                    else:
                        # 保持description为null，不设置任何值
                        failed_count += 1
                        print(f"✗ {link['title']}: 无法访问，保持description为空")
                        
                except Exception as e:
                    failed_count += 1
                    print(f"✗ {link['title']}: 处理异常，保持description为空 - {str(e)}")
                
                # 添加延迟避免过于频繁的请求
                time.sleep(0.5)
        
        # 保存更新后的数据
        try:
            with open(self.webstack_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, 
                         sort_keys=False, indent=2)
            print(f"\n✓ 已保存更新到 {self.webstack_file}")
        except Exception as e:
            print(f"\n✗ 保存文件失败: {e}")
            return {
                'updated': 0,
                'failed': len(links_to_update),
                'total': len(links_to_update)
            }
        
        return {
            'updated': updated_count,
            'failed': failed_count,
            'total': len(links_to_update)
        }

    def generate_single_description(self, url: str) -> Optional[str]:
        """
        为单个URL生成描述（用于测试）
        
        Args:
            url: 网站URL
            
        Returns:
            生成的描述，如果无法访问则返回None
        """
        website_info = self.extract_website_info(url)
        return self.generate_description(website_info, "", url)

def main():
    parser = argparse.ArgumentParser(description='网站描述自动生成工具')
    parser.add_argument('--file', '-f', 
                       default='data/webstack.yml',
                       help='webstack.yml 文件路径 (默认: data/webstack.yml)')
    parser.add_argument('--timeout', '-t', 
                       type=int, default=10,
                       help='请求超时时间，秒 (默认: 10)')
    parser.add_argument('--retries', '-r', 
                       type=int, default=3,
                       help='重试次数 (默认: 3)')
    parser.add_argument('--workers', '-w', 
                       type=int, default=5,
                       help='并发工作线程数 (默认: 5)')
    parser.add_argument('--all', 
                       action='store_true',
                       help='更新所有链接的描述（默认只更新null值）')
    parser.add_argument('--test-url', 
                       help='测试单个URL的描述生成')
    
    args = parser.parse_args()
    
    # 确保文件路径是绝对路径
    if not os.path.isabs(args.file):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        args.file = os.path.join(os.path.dirname(script_dir), args.file)
    
    generator = WebsiteDescriptionGenerator(
        args.file, 
        timeout=args.timeout, 
        retries=args.retries
    )
    
    if args.test_url:
        # 测试单个URL
        print(f"正在测试URL: {args.test_url}")
        description = generator.generate_single_description(args.test_url)
        if description is not None:
            print(f"生成的描述: {description}")
        else:
            print("无法访问网站，description将保持为空")
        return
    
    # 批量更新描述
    print("开始批量更新网站描述...")
    start_time = time.time()
    
    results = generator.update_descriptions(
        only_null=not args.all,
        max_workers=args.workers
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n" + "="*50)
    print(f"更新完成!")
    print(f"总计: {results['total']} 个链接")
    print(f"成功: {results['updated']} 个")
    print(f"失败: {results['failed']} 个")
    print(f"耗时: {duration:.2f} 秒")
    print(f"平均: {duration/results['total']:.2f} 秒/个" if results['total'] > 0 else "")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网站链接检测工具
检查webstack.yml中所有网站链接的可用性
"""

import yaml
import requests
import time
import argparse
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from datetime import datetime
import json

class LinkChecker:
    def __init__(self, webstack_file):
        self.webstack_file = webstack_file
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 状态统计
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'timeout': 0,
            'redirect': 0,
            'ssl_error': 0,
            'dns_error': 0,
            'unknown_error': 0
        }
        
        # 失败的链接详情
        self.failed_links = []
        
    def load_webstack_data(self):
        """加载webstack.yml数据"""
        try:
            with open(self.webstack_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"❌ 文件不存在: {self.webstack_file}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"❌ YAML解析错误: {e}")
            sys.exit(1)
    
    def extract_all_links(self, data):
        """提取所有网站链接"""
        links = []
        
        def extract_from_category(items, category_name=""):
            for item in items:
                if 'taxonomy' in item:
                    # 这是一个分类
                    category_title = item.get('taxonomy', 'Unknown Category')
                    if 'list' in item:
                        # 处理list下的子分类
                        for sub_item in item['list']:
                            if 'term' in sub_item:
                                sub_category = sub_item.get('term', 'Unknown Subcategory')
                                full_category = f"{category_title} > {sub_category}"
                                if 'links' in sub_item:
                                    extract_from_category(sub_item['links'], full_category)
                            elif 'links' in sub_item:
                                extract_from_category(sub_item['links'], category_title)
                elif 'term' in item:
                    # 这是一个子分类
                    sub_category = item.get('term', 'Unknown Subcategory')
                    if 'links' in item:
                        extract_from_category(item['links'], f"{category_name} > {sub_category}")
                else:
                    # 这是一个链接
                    url = item.get('url', '').strip()
                    title = item.get('title', 'Unknown')
                    description = item.get('description', '')
                    logo = item.get('logo', '')
                    
                    if url:
                        links.append({
                            'url': url,
                            'title': title,
                            'description': description,
                            'logo': logo,
                            'category': category_name
                        })
        
        if isinstance(data, list):
            extract_from_category(data)
        elif isinstance(data, dict) and 'webstack' in data:
            extract_from_category(data['webstack'])
        
        return links
    
    def normalize_url(self, url):
        """标准化URL格式"""
        if not url:
            return None
        
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    def is_china_domain(self, url):
        """检测是否为中国域名"""
        if not url:
            return False
        
        try:
            domain = urlparse(url).netloc.lower()
            china_suffixes = ['.cn', '.com.cn', '.net.cn', '.org.cn', '.gov.cn', '.edu.cn']
            return any(domain.endswith(suffix) for suffix in china_suffixes)
        except:
            return False
    
    def check_single_link(self, link_info, timeout=10):
        """检查单个链接的可用性"""
        url = self.normalize_url(link_info['url'])
        if not url:
            return {
                'url': link_info['url'],
                'title': link_info['title'],
                'category': link_info['category'],
                'status': 'invalid_url',
                'status_code': None,
                'response_time': None,
                'final_url': None,
                'error': 'Invalid URL format'
            }
        
        # 中国网站使用更长的超时时间
        if self.is_china_domain(url):
            timeout = 20
        
        start_time = time.time()
        
        try:
            response = self.session.get(
                url, 
                timeout=timeout, 
                allow_redirects=True,
                verify=False  # 忽略SSL证书验证
            )
            
            response_time = time.time() - start_time
            
            result = {
                'url': link_info['url'],
                'title': link_info['title'],
                'category': link_info['category'],
                'status_code': response.status_code,
                'response_time': round(response_time, 2),
                'final_url': response.url if response.url != url else None,
                'error': None
            }
            
            if response.status_code == 200:
                result['status'] = 'success'
                self.stats['success'] += 1
            elif 300 <= response.status_code < 400:
                result['status'] = 'redirect'
                self.stats['redirect'] += 1
            else:
                result['status'] = 'http_error'
                result['error'] = f'HTTP {response.status_code}'
                self.stats['failed'] += 1
                self.failed_links.append(result)
            
            return result
            
        except requests.exceptions.Timeout:
            result = {
                'url': link_info['url'],
                'title': link_info['title'],
                'category': link_info['category'],
                'status': 'timeout',
                'status_code': None,
                'response_time': timeout,
                'final_url': None,
                'error': f'Timeout after {timeout}s'
            }
            self.stats['timeout'] += 1
            self.failed_links.append(result)
            return result
            
        except requests.exceptions.SSLError:
            result = {
                'url': link_info['url'],
                'title': link_info['title'],
                'category': link_info['category'],
                'status': 'ssl_error',
                'status_code': None,
                'response_time': time.time() - start_time,
                'final_url': None,
                'error': 'SSL Certificate Error'
            }
            self.stats['ssl_error'] += 1
            self.failed_links.append(result)
            return result
            
        except requests.exceptions.ConnectionError as e:
            error_msg = str(e)
            if 'Name or service not known' in error_msg or 'getaddrinfo failed' in error_msg:
                status = 'dns_error'
                self.stats['dns_error'] += 1
            else:
                status = 'connection_error'
                self.stats['failed'] += 1
            
            result = {
                'url': link_info['url'],
                'title': link_info['title'],
                'category': link_info['category'],
                'status': status,
                'status_code': None,
                'response_time': time.time() - start_time,
                'final_url': None,
                'error': 'Connection failed'
            }
            self.failed_links.append(result)
            return result
            
        except Exception as e:
            result = {
                'url': link_info['url'],
                'title': link_info['title'],
                'category': link_info['category'],
                'status': 'unknown_error',
                'status_code': None,
                'response_time': time.time() - start_time,
                'final_url': None,
                'error': str(e)
            }
            self.stats['unknown_error'] += 1
            self.failed_links.append(result)
            return result
    
    def check_links_batch(self, links, max_workers=3, verbose=True):
        """批量检查链接"""
        if verbose:
            print(f"🔍 开始检查 {len(links)} 个链接...")
            print(f"⚙️  使用 {max_workers} 个并行线程\n")
        
        self.stats['total'] = len(links)
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_link = {
                executor.submit(self.check_single_link, link): link 
                for link in links
            }
            
            # 处理完成的任务
            for i, future in enumerate(as_completed(future_to_link), 1):
                link = future_to_link[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if verbose:
                        status_emoji = self.get_status_emoji(result['status'])
                        time_info = f" ({result['response_time']}s)" if result['response_time'] else ""
                        print(f"  [{i:3d}/{len(links)}] {status_emoji} {result['title'][:40]}{time_info}")
                    
                except Exception as e:
                    if verbose:
                        print(f"  [{i:3d}/{len(links)}] ❌ 检查失败: {e}")
                    self.stats['unknown_error'] += 1
                
                # 添加小延迟避免过于频繁的请求
                time.sleep(0.1)
        
        return results
    
    def get_status_emoji(self, status):
        """根据状态返回对应的表情符号"""
        emoji_map = {
            'success': '✅',
            'redirect': '🔄',
            'timeout': '⏰',
            'ssl_error': '🔒',
            'dns_error': '🌐',
            'http_error': '❌',
            'connection_error': '🔌',
            'invalid_url': '🚫',
            'unknown_error': '❓'
        }
        return emoji_map.get(status, '❓')
    
    def generate_report(self, results, format='markdown'):
        """生成检测报告"""
        timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        iso_timestamp = datetime.now().isoformat()
        
        if format == 'markdown':
            return self.generate_markdown_report(results, timestamp, iso_timestamp)
        elif format == 'json':
            return self.generate_json_report(results, timestamp, iso_timestamp)
        else:
            return self.generate_text_report(results, timestamp)
    
    def generate_markdown_report(self, results, timestamp, iso_timestamp):
        """生成Markdown格式报告"""
        report = [
            "# 网站链接检测报告",
            "",
            f"**生成时间**: {timestamp}",
            f"**ISO时间**: {iso_timestamp}",
            "",
            "## 📊 检测统计",
            "",
            f"- **总链接数**: {self.stats['total']}",
            f"- **成功访问**: {self.stats['success']} ({self.stats['success']/self.stats['total']*100:.1f}%)",
            f"- **重定向**: {self.stats['redirect']}",
            f"- **超时**: {self.stats['timeout']}",
            f"- **SSL错误**: {self.stats['ssl_error']}",
            f"- **DNS错误**: {self.stats['dns_error']}",
            f"- **HTTP错误**: {self.stats['failed']}",
            f"- **其他错误**: {self.stats['unknown_error']}",
            "",
            f"**总成功率**: {(self.stats['success'] + self.stats['redirect'])/self.stats['total']*100:.1f}%",
            ""
        ]
        
        if self.failed_links:
            report.extend([
                "## ❌ 失败链接详情",
                "",
                "| 网站 | 分类 | URL | 错误类型 | 详细信息 |",
                "|------|------|-----|----------|----------|"
            ])
            
            for link in self.failed_links:
                error_info = link.get('error', '未知错误')
                status_code = f" (HTTP {link['status_code']})" if link['status_code'] else ""
                report.append(
                    f"| {link['title']} | {link['category']} | {link['url']} | {link['status']}{status_code} | {error_info} |"
                )
            
            report.append("")
        
        # 按分类显示所有结果
        report.extend([
            "## 📋 详细结果",
            ""
        ])
        
        # 按分类分组
        by_category = {}
        for result in results:
            category = result['category'] or '未分类'
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(result)
        
        for category, links in by_category.items():
            report.extend([
                f"### {category}",
                ""
            ])
            
            for link in links:
                status_emoji = self.get_status_emoji(link['status'])
                time_info = f" ({link['response_time']}s)" if link['response_time'] else ""
                
                if link['final_url'] and link['final_url'] != link['url']:
                    redirect_info = f" → [{link['final_url']}]({link['final_url']})"
                else:
                    redirect_info = ""
                
                report.append(f"- {status_emoji} **{link['title']}** - [{link['url']}]({link['url']}){time_info}{redirect_info}")
                
                if link['error']:
                    report.append(f"  - ❌ {link['error']}")
            
            report.append("")
        
        return "\n".join(report)
    
    def generate_json_report(self, results, timestamp, iso_timestamp):
        """生成JSON格式报告"""
        report_data = {
            'metadata': {
                'generated_at': timestamp,
                'iso_timestamp': iso_timestamp,
                'total_links': self.stats['total'],
                'success_rate': round((self.stats['success'] + self.stats['redirect'])/self.stats['total']*100, 1)
            },
            'statistics': self.stats,
            'results': results,
            'failed_links': self.failed_links
        }
        
        return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    def generate_text_report(self, results, timestamp):
        """生成纯文本格式报告"""
        report = [
            "=" * 60,
            "网站链接检测报告",
            "=" * 60,
            f"生成时间: {timestamp}",
            "",
            "📊 统计信息:",
            f"  总链接数: {self.stats['total']}",
            f"  成功访问: {self.stats['success']} ({self.stats['success']/self.stats['total']*100:.1f}%)",
            f"  重定向: {self.stats['redirect']}",
            f"  失败链接: {len(self.failed_links)}",
            f"  总成功率: {(self.stats['success'] + self.stats['redirect'])/self.stats['total']*100:.1f}%",
            ""
        ]
        
        if self.failed_links:
            report.extend([
                "❌ 失败链接:",
                "-" * 40
            ])
            
            for link in self.failed_links:
                report.append(f"• {link['title']} ({link['url']})")
                report.append(f"  错误: {link['status']} - {link.get('error', '未知错误')}")
                report.append("")
        
        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description='网站链接检测工具')
    parser.add_argument('--webstack', default='../data/webstack.yml',
                       help='webstack.yml文件路径')
    parser.add_argument('--threads', type=int, default=3,
                       help='并行线程数 (默认3)')
    parser.add_argument('--format', choices=['markdown', 'json', 'text'], default='markdown',
                       help='报告格式 (默认markdown)')
    parser.add_argument('--output', '-o', 
                       help='输出文件路径 (默认: link_check_report.md/json/txt)')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='静默模式，只显示最终结果')
    parser.add_argument('--failed-only', action='store_true',
                       help='只显示失败的链接')
    
    args = parser.parse_args()
    
    # 确定webstack文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    webstack_file = os.path.join(script_dir, args.webstack)
    
    checker = LinkChecker(webstack_file)
    
    if not args.quiet:
        print("🔗 网站链接检测工具 v1.0\n")
    
    # 加载数据并提取链接
    data = checker.load_webstack_data()
    links = checker.extract_all_links(data)
    
    if not links:
        print("❌ 未找到任何链接")
        sys.exit(1)
    
    # 执行检测
    results = checker.check_links_batch(links, max_workers=args.threads, verbose=not args.quiet)
    
    # 生成报告
    report = checker.generate_report(results, format=args.format)
    
    # 确定输出文件
    if args.output:
        output_file = args.output
    else:
        results_dir = os.path.join(script_dir, 'results')
        os.makedirs(results_dir, exist_ok=True)
        file_extensions = {'markdown': '.md', 'json': '.json', 'text': '.txt'}
        output_file = os.path.join(results_dir, f'link_check_report{file_extensions[args.format]}')
    
    # 保存报告
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 显示结果
    if not args.quiet:
        print(f"\n📊 检测完成!")
        print(f"  总链接数: {checker.stats['total']}")
        print(f"  成功访问: {checker.stats['success']} ({checker.stats['success']/checker.stats['total']*100:.1f}%)")
        print(f"  重定向: {checker.stats['redirect']}")
        print(f"  失败链接: {len(checker.failed_links)}")
        print(f"  总成功率: {(checker.stats['success'] + checker.stats['redirect'])/checker.stats['total']*100:.1f}%")
        print(f"📄 报告已保存到: {output_file}")
    
    # 只显示失败链接
    if args.failed_only and checker.failed_links:
        print(f"\n❌ 失败链接 ({len(checker.failed_links)}个):")
        for link in checker.failed_links:
            print(f"  • {link['title']} - {link['url']}")
            print(f"    错误: {link['status']} - {link.get('error', '未知错误')}")
    
    # 设置退出码
    sys.exit(0 if not checker.failed_links else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
统一的网站Logo自动获取和更新工具
合并所有logo获取功能，支持批量处理和单个查询
"""

import yaml
import requests
import os
import sys
import time
import argparse
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Optional, Tuple
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

class UnifiedLogoTool:
    def __init__(self, webstack_file: str = None):
        self.webstack_file = webstack_file
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
        })
        
        # 多种favicon获取API (按可靠性排序，优先使用高质量大尺寸图标)
        self.favicon_apis = [
            "https://api.iowen.cn/favicon/{domain}.png",
            "https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://{domain}&size=128",
            "https://www.google.com/s2/favicons?sz=128&domain={domain}",
            "https://favicons.githubusercontent.com/{domain}",
            "https://icons.duckduckgo.com/ip3/{domain}.ico",
            "https://favicon.im/{domain}?larger=true",
            "https://api.faviconkit.com/{domain}/128",
        ]
        
        # 针对中国网站的特殊favicon获取方法 (优化尺寸)
        self.china_favicon_apis = [
            "https://statics.dnspod.cn/proxy_favicon/_/favicon?domain={domain}",
            "https://api.iowen.cn/favicon/{domain}.png",
            "https://favicon.link/f/{domain}",
            "https://icon.horse/icon/{domain}?size=large",  # 明确要求大尺寸
            "https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://{domain}&size=128",
            "https://www.google.com/s2/favicons?sz=128&domain={domain}",
            "https://api.faviconkit.com/{domain}/128",
        ]
        
        # 中国域名后缀列表
        self.china_domains = {'.cn', '.com.cn', '.net.cn', '.org.cn', '.gov.cn', '.edu.cn'}
    
    def extract_domain(self, url: str) -> str:
        """从URL中提取域名"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            if domain.startswith('www.'):
                domain = domain[4:]
                
            return domain
        except Exception as e:
            print(f"❌ 域名解析失败: {url} - {e}")
            return ""
    
    def is_china_domain(self, domain: str) -> bool:
        """判断是否为中国域名"""
        domain = domain.lower()
        return any(domain.endswith(suffix) for suffix in self.china_domains)
    
    def test_favicon_url(self, favicon_url: str, timeout: int = 10) -> bool:
        """测试favicon URL是否有效，改进检测逻辑"""
        try:
            response = self.session.head(favicon_url, timeout=timeout)
            if response.status_code != 200:
                return False
            
            # 检查Content-Type是否为图片
            content_type = response.headers.get('content-type', '').lower()
            if any(img_type in content_type for img_type in ['image/', 'application/octet-stream']):
                return True
            
            # 如果不是图片类型，做进一步检查
            if 'json' in content_type or 'html' in content_type:
                # 对于可能返回错误页面的API，做GET请求验证
                get_response = self.session.get(favicon_url, timeout=timeout)
                if get_response.status_code == 200:
                    content = get_response.text.lower()
                    # 检查是否包含错误信息
                    error_indicators = [
                        '404', 'not found', '页面不存在', '资源不存在', 
                        'error', '错误', 'exception', '异常'
                    ]
                    if any(indicator in content for indicator in error_indicators):
                        return False
                    
                    # 检查响应大小，错误页面通常较大
                    if len(content) > 10000:  # 大于10KB可能是错误页面
                        return False
                
                return True
            
            return True
            
        except Exception:
            return False
    
    def get_favicon_for_domain(self, domain: str, verbose: bool = True) -> Optional[str]:
        """为指定域名获取最佳的favicon URL，针对中国网站使用特殊策略"""
        if not domain:
            return None
        
        if verbose:
            print(f"🔍 正在为 {domain} 查找favicon...")
        
        # 根据域名类型选择API列表
        if self.is_china_domain(domain):
            if verbose:
                print(f"  🇨🇳 检测到中国域名，使用优化策略...")
            apis_to_use = self.china_favicon_apis
            timeout = 15  # 中国网站使用更长的超时时间
        else:
            apis_to_use = self.favicon_apis
            timeout = 10
        
        for i, api_template in enumerate(apis_to_use, 1):
            favicon_url = api_template.format(domain=domain)
            
            if verbose:
                print(f"  [{i}/{len(apis_to_use)}] 测试: {favicon_url[:60]}...")
            
            if self.test_favicon_url(favicon_url, timeout=timeout):
                if verbose:
                    print(f"  ✅ 找到可用favicon: {favicon_url}")
                return favicon_url
            else:
                if verbose:
                    print(f"  ❌ 不可用")
            
            time.sleep(0.2)  # 中国网站需要更长的间隔
        
        # 如果是中国域名且上述方法都失败，尝试直接访问网站获取favicon
        if self.is_china_domain(domain):
            if verbose:
                print(f"  🔄 尝试直接从网站获取favicon...")
            direct_favicon = self.get_favicon_from_website(domain, verbose)
            if direct_favicon:
                return direct_favicon
        
        if verbose:
            print(f"  ❌ 未找到可用的favicon")
        return None
    
    def check_logo_quality(self, logo_url: str) -> dict:
        """检查logo的质量信息（尺寸、文件大小等）"""
        try:
            response = self.session.head(logo_url, timeout=10)
            if response.status_code != 200:
                return {"valid": False, "error": "HTTP error"}
            
            content_length = response.headers.get('content-length')
            content_type = response.headers.get('content-type', '')
            
            info = {
                "valid": True,
                "content_type": content_type,
                "file_size": int(content_length) if content_length else None,
                "url": logo_url
            }
            
            # 如果文件很小，可能是低质量图标
            if info["file_size"] and info["file_size"] < 500:  # 小于500字节
                info["quality"] = "low"
                info["warning"] = "文件过小，可能是低质量图标"
            elif info["file_size"] and info["file_size"] > 50000:  # 大于50KB
                info["quality"] = "high"
            else:
                info["quality"] = "medium"
            
            return info
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def get_best_quality_favicon(self, domain: str, verbose: bool = True) -> Optional[str]:
        """获取最佳质量的favicon，优先选择大尺寸高质量的"""
        if not domain:
            return None
        
        if verbose:
            print(f"🔍 正在为 {domain} 查找高质量favicon...")
        
        # 根据域名类型选择API列表
        if self.is_china_domain(domain):
            if verbose:
                print(f"  🇨🇳 检测到中国域名，使用优化策略...")
            apis_to_use = self.china_favicon_apis
            timeout = 15
        else:
            apis_to_use = self.favicon_apis
            timeout = 10
        
        best_favicon = None
        best_quality_score = 0
        
        for i, api_template in enumerate(apis_to_use, 1):
            favicon_url = api_template.format(domain=domain)
            
            if verbose:
                print(f"  [{i}/{len(apis_to_use)}] 测试: {favicon_url[:60]}...")
            
            if self.test_favicon_url(favicon_url, timeout=timeout):
                # 检查质量
                quality_info = self.check_logo_quality(favicon_url)
                
                if quality_info["valid"]:
                    # 计算质量分数
                    score = 0
                    if quality_info.get("file_size"):
                        # 文件大小评分 (1KB-20KB为最佳范围)
                        size = quality_info["file_size"]
                        if 1000 <= size <= 20000:
                            score += 50
                        elif 500 <= size <= 50000:
                            score += 30
                        else:
                            score += 10
                    
                    # API优先级评分 (排在前面的API优先级更高)
                    score += (len(apis_to_use) - i) * 5
                    
                    # 特定API加分
                    if "faviconkit" in favicon_url or "icon.horse" in favicon_url:
                        score += 20  # 专业favicon服务加分
                    if "size=128" in favicon_url or "larger=true" in favicon_url:
                        score += 15  # 明确要求大尺寸加分
                    
                    if verbose:
                        size_info = f" ({quality_info.get('file_size', 'unknown')}B)" if quality_info.get('file_size') else ""
                        print(f"    ✅ 可用 (分数: {score}{size_info})")
                    
                    if score > best_quality_score:
                        best_favicon = favicon_url
                        best_quality_score = score
                        if verbose:
                            print(f"    🏆 当前最佳选择")
                else:
                    if verbose:
                        print(f"    ❌ 质量检查失败")
            else:
                if verbose:
                    print(f"    ❌ 不可用")
            
            time.sleep(0.2)
        
        if best_favicon:
            if verbose:
                print(f"  🎉 最终选择: {best_favicon} (分数: {best_quality_score})")
            return best_favicon
        
        # 如果没找到高质量的，使用原来的方法作为备用
        if verbose:
            print(f"  🔄 未找到高质量favicon，尝试标准方法...")
        return self.get_favicon_for_domain(domain, verbose=False)
    
    def get_favicon_from_website(self, domain: str, verbose: bool = True) -> Optional[str]:
        """直接从网站首页获取favicon链接"""
        try:
            # 尝试常见的favicon路径
            common_paths = [
                f"https://{domain}/favicon.ico",
                f"https://{domain}/favicon.png", 
                f"http://{domain}/favicon.ico",
                f"http://{domain}/favicon.png"
            ]
            
            for path in common_paths:
                if verbose:
                    print(f"    检测: {path}")
                if self.test_favicon_url(path, timeout=15):
                    if verbose:
                        print(f"    ✅ 直接路径可用: {path}")
                    return path
            
            # 尝试解析HTML获取favicon链接
            for protocol in ['https', 'http']:
                try:
                    response = self.session.get(f"{protocol}://{domain}", timeout=15)
                    if response.status_code == 200:
                        # 简单的favicon链接提取
                        content = response.text.lower()
                        
                        # 查找link标签中的favicon
                        import re
                        favicon_patterns = [
                            r'<link[^>]*rel=["\'](?:shortcut\s+)?icon["\'][^>]*href=["\']([^"\']+)["\']',
                            r'<link[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\'](?:shortcut\s+)?icon["\']'
                        ]
                        
                        for pattern in favicon_patterns:
                            matches = re.findall(pattern, content)
                            for match in matches:
                                if match.startswith('//'):
                                    favicon_url = f"{protocol}:{match}"
                                elif match.startswith('/'):
                                    favicon_url = f"{protocol}://{domain}{match}"
                                elif not match.startswith('http'):
                                    favicon_url = f"{protocol}://{domain}/{match}"
                                else:
                                    favicon_url = match
                                
                                if verbose:
                                    print(f"    检测HTML中的favicon: {favicon_url}")
                                
                                if self.test_favicon_url(favicon_url, timeout=10):
                                    if verbose:
                                        print(f"    ✅ HTML中找到可用favicon: {favicon_url}")
                                    return favicon_url
                        break
                except:
                    continue
                    
        except Exception as e:
            if verbose:
                print(f"    ❌ 直接获取失败: {e}")
        
        return None
    
    def get_single_favicon_with_quality(self, url_or_domain: str) -> Optional[str]:
        """获取单个网站的高质量favicon"""
        domain = self.extract_domain(url_or_domain)
        if not domain:
            print(f"❌ 无法解析域名: {url_or_domain}")
            return None
        
        favicon_url = self.get_best_quality_favicon(domain)
        
        if favicon_url:
            # 显示质量信息
            quality_info = self.check_logo_quality(favicon_url)
            print(f"\n🎉 成功找到favicon: {favicon_url}")
            
            if quality_info["valid"]:
                size_info = f" ({quality_info.get('file_size', 'unknown')}B)" if quality_info.get('file_size') else ""
                print(f"📊 质量信息: {quality_info.get('content_type', 'unknown')}{size_info}")
                if quality_info.get('warning'):
                    print(f"⚠️  {quality_info['warning']}")
            
            # 尝试复制到剪贴板
            try:
                import subprocess
                subprocess.run(['xclip', '-selection', 'clipboard'], 
                             input=favicon_url.encode(), check=True)
                print("📋 已复制到剪贴板!")
            except:
                print("💡 提示: 安装xclip可自动复制到剪贴板")
        
        return favicon_url

    def get_single_favicon(self, url_or_domain: str) -> Optional[str]:
        """获取单个网站的favicon (命令行工具模式)"""
        domain = self.extract_domain(url_or_domain)
        if not domain:
            print(f"❌ 无法解析域名: {url_or_domain}")
            return None
        
        favicon_url = self.get_favicon_for_domain(domain)
        
        if favicon_url:
            print(f"\n🎉 成功找到favicon: {favicon_url}")
            
            # 尝试复制到剪贴板
            try:
                import subprocess
                subprocess.run(['xclip', '-selection', 'clipboard'], 
                             input=favicon_url.encode(), check=True)
                print("📋 已复制到剪贴板!")
            except:
                print("💡 提示: 安装xclip可自动复制到剪贴板")
        
        return favicon_url
    
    def load_webstack_data(self) -> List[Dict]:
        """加载webstack.yml数据"""
        try:
            with open(self.webstack_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            sys.exit(1)
    
    def save_webstack_data(self, data: List[Dict]):
        """保存webstack.yml数据"""
        try:
            with open(self.webstack_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False, indent=2)
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")
            sys.exit(1)
    
    def scan_missing_logos(self) -> List[Tuple[str, str, str]]:
        """扫描缺失logo的网站"""
        data = self.load_webstack_data()
        missing_logos = []
        
        for taxonomy in data:
            if 'list' not in taxonomy:
                continue
                
            taxonomy_name = taxonomy.get('taxonomy', 'Unknown')
            
            for term_group in taxonomy['list']:
                if 'links' not in term_group:
                    continue
                    
                term_name = term_group.get('term', 'Unknown')
                
                for link in term_group['links']:
                    title = link.get('title', 'Unknown')
                    url = link.get('url', '')
                    logo = link.get('logo', '')
                    
                    # 检查是否缺失logo或为空
                    if not logo or logo.strip() == '':
                        domain = self.extract_domain(url)
                        if domain:
                            missing_logos.append((title, url, domain))
        
        return missing_logos
    
    def update_missing_logos_batch(self, dry_run: bool = True, max_workers: int = 3) -> Dict[str, int]:
        """批量更新缺失的logo"""
        print("🔍 扫描缺失logo的网站...")
        missing_logos = self.scan_missing_logos()
        
        stats = {
            "total_scanned": len(missing_logos),
            "updated": 0,
            "failed": 0
        }
        
        if not missing_logos:
            print("✅ 所有网站都已有logo!")
            return stats
        
        print(f"📋 发现 {len(missing_logos)} 个网站缺失logo")
        
        if dry_run:
            print("\n🔍 预览模式 - 以下网站将被处理:")
            for i, (title, url, domain) in enumerate(missing_logos, 1):
                print(f"  {i:2d}. {title} ({domain})")
            
            response = input(f"\n是否继续更新这 {len(missing_logos)} 个网站的logo? (y/n): ")
            if response.lower() != 'y':
                print("❌ 用户取消操作")
                return stats
        
        # 加载数据准备更新
        data = self.load_webstack_data()
        updated_count = 0
        
        print(f"\n🚀 开始批量获取logo (使用 {max_workers} 个线程)...")
        
        # 创建域名到favicon的映射
        domain_to_favicon = {}
        
        def fetch_favicon_for_domain(domain):
            return domain, self.get_favicon_for_domain(domain, verbose=False)
        
        # 并行获取favicon
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_domain = {
                executor.submit(fetch_favicon_for_domain, domain): domain 
                for _, _, domain in missing_logos
            }
            
            for i, future in enumerate(as_completed(future_to_domain), 1):
                domain = future_to_domain[future]
                try:
                    _, favicon_url = future.result()
                    domain_to_favicon[domain] = favicon_url
                    
                    status = "✅" if favicon_url else "❌"
                    print(f"  [{i:2d}/{len(missing_logos)}] {status} {domain}")
                    
                except Exception as e:
                    print(f"  [{i:2d}/{len(missing_logos)}] ❌ {domain} - 错误: {e}")
                    domain_to_favicon[domain] = None
        
        # 更新数据结构
        print(f"\n📝 更新配置文件...")
        for taxonomy in data:
            if 'list' not in taxonomy:
                continue
                
            for term_group in taxonomy['list']:
                if 'links' not in term_group:
                    continue
                    
                for link in term_group['links']:
                    url = link.get('url', '')
                    logo = link.get('logo', '')
                    
                    if not logo or logo.strip() == '':
                        domain = self.extract_domain(url)
                        if domain in domain_to_favicon and domain_to_favicon[domain]:
                            link['logo'] = domain_to_favicon[domain]
                            updated_count += 1
                            stats["updated"] += 1
                        else:
                            stats["failed"] += 1
        
        # 保存更新后的数据
        if updated_count > 0:
            self.save_webstack_data(data)
            print(f"✅ 已更新 {updated_count} 个网站的logo")
        else:
            print("❌ 没有找到任何可用的logo")
        
        print(f"\n📊 统计结果:")
        print(f"  扫描网站: {stats['total_scanned']}")
        print(f"  成功更新: {stats['updated']}")
        print(f"  获取失败: {stats['failed']}")
        
        return stats
    
    def verify_existing_logos(self, max_workers: int = 3) -> Dict[str, int]:
        """验证现有logo的有效性"""
        print("🔍 验证现有logo的有效性...")
        data = self.load_webstack_data()
        
        logos_to_check = []
        stats = {"total": 0, "valid": 0, "invalid": 0, "checked": 0}
        
        # 收集所有现有的logo
        for taxonomy in data:
            if 'list' not in taxonomy:
                continue
                
            for term_group in taxonomy['list']:
                if 'links' not in term_group:
                    continue
                    
                for link in term_group['links']:
                    logo = link.get('logo', '')
                    if logo and logo.strip():
                        title = link.get('title', 'Unknown')
                        url = link.get('url', '')
                        logos_to_check.append((title, url, logo, link))
        
        stats["total"] = len(logos_to_check)
        print(f"📋 发现 {len(logos_to_check)} 个现有logo需要验证")
        
        if not logos_to_check:
            return stats
        
        def verify_logo(item):
            title, url, logo, link_ref = item
            return title, url, logo, self.test_favicon_url(logo, timeout=10), link_ref
        
        print(f"\n🚀 开始验证logo (使用 {max_workers} 个线程)...")
        
        # 并行验证logo
        invalid_logos = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {
                executor.submit(verify_logo, item): item 
                for item in logos_to_check
            }
            
            for i, future in enumerate(as_completed(future_to_item), 1):
                try:
                    title, url, logo, is_valid, link_ref = future.result()
                    stats["checked"] += 1
                    
                    if is_valid:
                        stats["valid"] += 1
                        status = "✅"
                    else:
                        stats["invalid"] += 1
                        status = "❌"
                        invalid_logos.append((title, url, logo, link_ref))
                    
                    print(f"  [{i:3d}/{len(logos_to_check)}] {status} {title[:40]}")
                    
                except Exception as e:
                    print(f"  [{i:3d}/{len(logos_to_check)}] ❌ 验证失败: {e}")
                    stats["invalid"] += 1
        
        # 清理无效logo
        if invalid_logos:
            print(f"\n🧹 清理 {len(invalid_logos)} 个无效logo...")
            for title, url, logo, link_ref in invalid_logos:
                link_ref['logo'] = ''  # 清空无效logo
            
            self.save_webstack_data(data)
            print("✅ 已清理无效logo")
        
        print(f"\n📊 验证结果:")
        print(f"  总logo数: {stats['total']}")
        print(f"  有效logo: {stats['valid']}")
        print(f"  无效logo: {stats['invalid']}")
        print(f"  有效率: {stats['valid']/stats['total']*100:.1f}%")
        
        return stats
    
    def generate_report(self) -> str:
        """生成logo状态报告"""
        data = self.load_webstack_data()
        
        # 生成时间戳
        from datetime import datetime
        now = datetime.now()
        timestamp = now.strftime("%Y年%m月%d日 %H:%M:%S")
        iso_timestamp = now.isoformat()
        
        report = [
            "# 网站Logo状态报告",
            "",
            f"**生成时间**: {timestamp}",
            f"**ISO时间**: {iso_timestamp}",
            ""
        ]
        
        total_sites = 0
        sites_with_logo = 0
        sites_without_logo = 0
        
        for taxonomy in data:
            if 'list' not in taxonomy:
                continue
                
            taxonomy_name = taxonomy.get('taxonomy', 'Unknown')
            report.append(f"## {taxonomy_name}\n")
            
            for term_group in taxonomy['list']:
                if 'links' not in term_group:
                    continue
                    
                term_name = term_group.get('term', 'Unknown')
                report.append(f"### {term_name}\n")
                
                for link in term_group['links']:
                    total_sites += 1
                    title = link.get('title', 'Unknown')
                    url = link.get('url', '')
                    logo = link.get('logo', '')
                    
                    if logo and logo.strip():
                        sites_with_logo += 1
                        status = "✅"
                    else:
                        sites_without_logo += 1
                        status = "❌"
                    
                    report.append(f"- {status} **{title}** - {url}")
                    if logo and logo.strip():
                        report.append(f"  - Logo: {logo}")
                    report.append("")
        
        # 添加统计信息
        report.append("**统计信息:**")
        report.append("")
        report.append(f"- 总网站数: {total_sites}")
        report.append(f"- 有Logo: {sites_with_logo} ({sites_with_logo/total_sites*100:.1f}%)")
        report.append(f"- 缺失Logo: {sites_without_logo} ({sites_without_logo/total_sites*100:.1f}%)")
        report.append("")
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='统一的网站Logo获取工具')
    parser.add_argument('command', choices=['get', 'get-hq', 'check', 'scan', 'update', 'verify', 'report'], 
                       help='操作命令')
    parser.add_argument('target', nargs='?', 
                       help='目标URL或域名 (用于get, get-hq, check命令)')
    parser.add_argument('--webstack', default='../data/webstack.yml',
                       help='webstack.yml文件路径')
    parser.add_argument('--dry-run', action='store_true',
                       help='预览模式，不实际更新文件')
    parser.add_argument('--threads', type=int, default=3,
                       help='并行线程数 (默认3)')
    
    args = parser.parse_args()
    
    # 确定webstack文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    webstack_file = os.path.join(script_dir, args.webstack)
    
    tool = UnifiedLogoTool(webstack_file)
    
    print("🔧 统一Logo获取工具 v1.1\n")
    
    if args.command == 'get':
        if not args.target:
            print("❌ get命令需要指定目标URL或域名")
            print("用法: python logo_tool.py get example.com")
            sys.exit(1)
        
        tool.get_single_favicon(args.target)
    
    elif args.command == 'get-hq':
        if not args.target:
            print("❌ get-hq命令需要指定目标URL或域名")
            print("用法: python logo_tool.py get-hq example.com")
            sys.exit(1)
        
        tool.get_single_favicon_with_quality(args.target)
    
    elif args.command == 'check':
        if not args.target:
            print("❌ check命令需要指定目标URL")
            print("用法: python logo_tool.py check https://example.com/favicon.ico")
            sys.exit(1)
        
        quality_info = tool.check_logo_quality(args.target)
        if quality_info["valid"]:
            size_info = f" ({quality_info.get('file_size', 'unknown')}B)" if quality_info.get('file_size') else ""
            print(f"✅ Logo可用: {args.target}")
            print(f"📊 类型: {quality_info.get('content_type', 'unknown')}{size_info}")
            print(f"🏆 质量: {quality_info.get('quality', 'unknown')}")
            if quality_info.get('warning'):
                print(f"⚠️  {quality_info['warning']}")
        else:
            print(f"❌ Logo不可用: {quality_info.get('error', '未知错误')}")
    
    elif args.command == 'scan':
        missing = tool.scan_missing_logos()
        print(f"📋 发现 {len(missing)} 个网站缺失logo:")
        for i, (title, url, domain) in enumerate(missing, 1):
            print(f"  {i:2d}. {title} ({domain})")
    
    elif args.command == 'update':
        tool.update_missing_logos_batch(dry_run=args.dry_run, max_workers=args.threads)
    
    elif args.command == 'verify':
        tool.verify_existing_logos(max_workers=args.threads)
    
    elif args.command == 'report':
        report = tool.generate_report()
        results_dir = os.path.join(script_dir, 'results')
        os.makedirs(results_dir, exist_ok=True)
        report_file = os.path.join(results_dir, 'logo_status_report.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 报告已保存到: {report_file}")

if __name__ == "__main__":
    main()

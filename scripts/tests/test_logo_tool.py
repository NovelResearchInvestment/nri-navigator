#!/usr/bin/env python3
"""
Logo工具测试脚本
测试logo_tool.py的各项功能
"""

import os
import sys
import subprocess
import tempfile
import yaml
from pathlib import Path

# 添加上级目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

def test_logo_tool_commands():
    """测试logo_tool.py的各个命令"""
    tool_path = os.path.join(parent_dir, 'logo_tool.py')
    
    tests = [
        {
            'name': '测试单个logo获取',
            'command': ['python3', tool_path, 'get', 'github.com'],
            'expected_keywords': ['成功找到favicon', 'github.com']
        },
        {
            'name': '测试高质量logo获取',
            'command': ['python3', tool_path, 'get-hq', 'baidu.com'],
            'expected_keywords': ['查找高质量favicon', '质量信息']
        },
        {
            'name': '测试logo质量检查',
            'command': ['python3', tool_path, 'check', 'https://github.com/favicon.ico'],
            'expected_keywords': ['Logo', '类型']
        },
        {
            'name': '测试扫描功能',
            'command': ['python3', tool_path, 'scan'],
            'expected_keywords': ['发现', '个网站缺失logo']
        },
        {
            'name': '测试报告生成',
            'command': ['python3', tool_path, 'report'],
            'expected_keywords': ['报告已保存到', 'results']
        }
    ]
    
    results = []
    for test in tests:
        print(f"\n🔧 {test['name']}...")
        try:
            result = subprocess.run(
                test['command'], 
                capture_output=True, 
                text=True, 
                timeout=30,
                cwd=parent_dir
            )
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            # 检查预期关键词
            keywords_found = all(keyword in output for keyword in test['expected_keywords'])
            
            if success and keywords_found:
                print(f"  ✅ 通过")
                results.append(('✅', test['name']))
            else:
                print(f"  ❌ 失败")
                print(f"  返回码: {result.returncode}")
                print(f"  输出: {output[:200]}...")
                results.append(('❌', test['name']))
                
        except subprocess.TimeoutExpired:
            print(f"  ⏰ 超时")
            results.append(('⏰', test['name']))
        except Exception as e:
            print(f"  💥 异常: {e}")
            results.append(('💥', test['name']))
    
    return results

def test_results_directory():
    """测试results目录是否正确创建和使用"""
    results_dir = os.path.join(parent_dir, 'results')
    
    print(f"\n📁 测试results目录...")
    
    # 清理可能存在的旧文件
    report_file = os.path.join(results_dir, 'logo_status_report.md')
    if os.path.exists(report_file):
        os.remove(report_file)
    
    # 运行报告生成命令
    tool_path = os.path.join(parent_dir, 'logo_tool.py')
    try:
        result = subprocess.run(
            ['python3', tool_path, 'report'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=parent_dir
        )
        
        if os.path.exists(report_file):
            print(f"  ✅ 报告文件已正确保存到results目录")
            # 检查文件内容
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if '网站Logo状态报告' in content:
                    print(f"  ✅ 报告内容格式正确")
                    return True
                else:
                    print(f"  ❌ 报告内容格式异常")
                    return False
        else:
            print(f"  ❌ 报告文件未在results目录中找到")
            return False
            
    except Exception as e:
        print(f"  💥 测试异常: {e}")
        return False

def main():
    """运行所有测试"""
    print("🧪 Logo工具测试套件")
    print("=" * 50)
    
    # 检查工具是否存在
    tool_path = os.path.join(parent_dir, 'logo_tool.py')
    if not os.path.exists(tool_path):
        print(f"❌ 找不到logo_tool.py: {tool_path}")
        sys.exit(1)
    
    # 运行功能测试
    test_results = test_logo_tool_commands()
    
    # 测试输出目录
    results_dir_ok = test_results_directory()
    
    # 汇总结果
    print(f"\n📊 测试结果汇总:")
    print("=" * 50)
    
    passed = sum(1 for status, _ in test_results if status == '✅')
    total = len(test_results)
    
    for status, test_name in test_results:
        print(f"  {status} {test_name}")
    
    if results_dir_ok:
        print(f"  ✅ results目录功能正常")
    else:
        print(f"  ❌ results目录功能异常")
    
    print(f"\n🎯 总体结果: {passed}/{total} 个功能测试通过")
    
    if passed == total and results_dir_ok:
        print("🎉 所有测试通过!")
        sys.exit(0)
    else:
        print("⚠️  部分测试失败，请检查问题")
        sys.exit(1)

if __name__ == "__main__":
    main()

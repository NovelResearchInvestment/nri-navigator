#!/usr/bin/env python3
"""
链接检查工具测试套件
"""

import os
import sys
import subprocess
import tempfile

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

class LinkCheckerTest:
    def __init__(self):
        self.script_dir = parent_dir
        self.success_count = 0
        self.total_tests = 0
        
    def test_basic_check(self):
        """测试基础检查模式"""
        print("🔗 测试基础检查模式...")
        result = subprocess.run([
            'python3', 'link_checker.py', 
            '--format', 'markdown',
            '--output', 'results/test_basic_check.md',
            '--quiet',
            '--failed-only'
        ], capture_output=True, text=True, cwd=self.script_dir, timeout=60)
        
        if result.returncode == 0:
            print("  ✅ 通过")
            self.success_count += 1
        else:
            print("  ❌ 失败")
            print(f"  返回码: {result.returncode}")
            print(f"  输出: {result.stdout[:200]}...")
            if result.stderr:
                print(f"  错误: {result.stderr[:200]}...")
                
    def test_json_output(self):
        """测试JSON格式输出"""
        print("🔗 测试JSON格式输出...")
        result = subprocess.run([
            'python3', 'link_checker.py',
            '--format', 'json',
            '--output', 'results/test_json_output.json',
            '--quiet',
            '--failed-only'
        ], capture_output=True, text=True, cwd=self.script_dir, timeout=60)
        
        if result.returncode == 0:
            print("  ✅ 通过")
            self.success_count += 1
        else:
            print("  ❌ 失败")
            print(f"  返回码: {result.returncode}")
            print(f"  输出: {result.stdout[:200]}...")
            
    def test_text_output(self):
        """测试文本格式输出"""
        print("🔗 测试文本格式输出...")
        result = subprocess.run([
            'python3', 'link_checker.py',
            '--format', 'text',
            '--output', 'results/test_text_output.txt',
            '--quiet',
            '--failed-only'
        ], capture_output=True, text=True, cwd=self.script_dir, timeout=60)
        
        if result.returncode == 0:
            print("  ✅ 通过")
            self.success_count += 1
        else:
            print("  ❌ 失败")
            print(f"  返回码: {result.returncode}")
            print(f"  输出: {result.stdout[:200]}...")
            
    def test_threads_option(self):
        """测试线程数选项"""
        print("🔗 测试线程数选项...")
        result = subprocess.run([
            'python3', 'link_checker.py',
            '--threads', '2',
            '--format', 'json',
            '--output', 'results/test_threads.json',
            '--quiet',
            '--failed-only'
        ], capture_output=True, text=True, cwd=self.script_dir, timeout=60)
        
        if result.returncode == 0:
            print("  ✅ 通过")
            self.success_count += 1
        else:
            print("  ❌ 失败")
            print(f"  返回码: {result.returncode}")
            print(f"  输出: {result.stdout[:200]}...")
            
    def test_output_files(self):
        """测试输出文件格式"""
        print("📄 测试输出格式...")
        formats = ['markdown', 'json', 'text']
        extensions = ['.md', '.json', '.txt']
        
        for fmt, ext in zip(formats, extensions):
            test_file = f'results/test_format{ext}'
            if os.path.exists(test_file):
                print(f"  ✅ {fmt}格式文件生成成功")
            else:
                print(f"  ❌ {fmt}格式文件生成失败")
                
    def test_results_directory(self):
        """测试results目录功能"""
        print("📁 测试results目录...")
        results_dir = os.path.join(self.script_dir, 'results')
        if os.path.exists(results_dir):
            # 检查是否有链接检查报告
            report_files = [f for f in os.listdir(results_dir) if 'link_check' in f or 'test_' in f]
            if report_files:
                print("  ✅ 报告文件已正确保存到results目录")
            else:
                print("  ❌ 报告文件未在results目录中找到")
        else:
            print("  ❌ results目录不存在")
            
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 链接检查工具测试套件")
        print("=" * 50)
        
        tests = [
            self.test_basic_check,
            self.test_json_output, 
            self.test_text_output,
            self.test_threads_option
        ]
        
        self.total_tests = len(tests)
        
        # 确保results目录存在
        results_dir = os.path.join(self.script_dir, 'results')
        os.makedirs(results_dir, exist_ok=True)
        
        for test in tests:
            try:
                test()
            except subprocess.TimeoutExpired:
                print("  ⏰ 测试超时")
            except Exception as e:
                print(f"  💥 测试异常: {e}")
                
        # 额外测试
        self.test_output_files()
        self.test_results_directory()
        
        # 总结
        print("\n📊 测试结果汇总:")
        print("=" * 50)
        test_names = [
            "测试基础检查模式",
            "测试JSON格式输出", 
            "测试文本格式输出",
            "测试线程数选项",
            "输出格式功能正常",
            "results目录功能正常"
        ]
        
        for i, name in enumerate(test_names):
            if i < self.success_count:
                print(f"  ✅ {name}")
            else:
                print(f"  ❌ {name}")
                
        print(f"\n🎯 总体结果: {self.success_count}/{self.total_tests} 个功能测试通过")
        
        if self.success_count == self.total_tests:
            print("🎉 所有测试通过!")
            return True
        else:
            print("⚠️  部分测试失败，请检查问题")
            return False

if __name__ == "__main__":
    tester = LinkCheckerTest()
    tester.run_all_tests()

#!/usr/bin/env python3
"""
描述生成工具测试套件
"""

import os
import sys
import subprocess
import tempfile
import yaml

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

class DescriptionGeneratorTest:
    def __init__(self):
        self.script_dir = parent_dir
        self.success_count = 0
        self.total_tests = 0
        
    def create_test_webstack(self):
        """创建测试用的webstack.yml文件"""
        test_data = {
            'webstack': {
                '测试分类': [
                    {
                        'title': 'GitHub',
                        'url': 'https://github.com',
                        'logo': '',
                        'description': None
                    },
                    {
                        'title': 'Stack Overflow',
                        'url': 'https://stackoverflow.com',
                        'logo': '',
                        'description': ''
                    }
                ]
            }
        }
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False, encoding='utf-8')
        yaml.dump(test_data, temp_file, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
        temp_file.close()
        
        return temp_file.name
        
    def test_single_url(self):
        """测试单个URL描述生成"""
        print("📝 测试单个URL描述生成...")
        result = subprocess.run([
            'python3', 'description_generator.py',
            '--test-url', 'https://github.com'
        ], capture_output=True, text=True, cwd=self.script_dir, timeout=30)
        
        if result.returncode == 0 and ('GitHub' in result.stdout or 'github' in result.stdout.lower()):
            print("  ✅ 通过")
            self.success_count += 1
        else:
            print("  ❌ 失败")
            print(f"  返回码: {result.returncode}")
            print(f"  输出: {result.stdout[:200]}...")
            if result.stderr:
                print(f"  错误: {result.stderr[:200]}...")
                
    def test_batch_processing(self):
        """测试批量处理"""
        print("📝 测试批量处理...")
        test_file = self.create_test_webstack()
        
        try:
            result = subprocess.run([
                'python3', 'description_generator.py',
                '--file', test_file,
                '--workers', '2',
                '--timeout', '10'
            ], capture_output=True, text=True, cwd=self.script_dir, timeout=60)
            
            if result.returncode == 0:
                print("  ✅ 通过")
                self.success_count += 1
            else:
                print("  ❌ 失败")
                print(f"  返回码: {result.returncode}")
                print(f"  输出: {result.stdout[:200]}...")
                
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
                
    def test_all_option(self):
        """测试--all选项"""
        print("📝 测试--all选项...")
        test_file = self.create_test_webstack()
        
        try:
            result = subprocess.run([
                'python3', 'description_generator.py',
                '--file', test_file,
                '--all',
                '--workers', '1',
                '--timeout', '5'
            ], capture_output=True, text=True, cwd=self.script_dir, timeout=60)
            
            if result.returncode == 0:
                print("  ✅ 通过")
                self.success_count += 1
            else:
                print("  ❌ 失败")
                print(f"  返回码: {result.returncode}")
                print(f"  输出: {result.stdout[:200]}...")
                
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
                
    def test_webstack_processing(self):
        """测试webstack文件处理"""
        print("📄 测试webstack文件处理...")
        test_file = self.create_test_webstack()
        
        try:
            # 检查文件是否正确创建
            with open(test_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if 'webstack' in data and '测试分类' in data['webstack']:
                    print("  ✅ webstack文件格式正确")
                else:
                    print("  ❌ webstack文件格式错误")
                    
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
                
    def test_error_handling(self):
        """测试错误处理"""
        print("🚨 测试错误处理...")
        
        # 测试无效URL
        result1 = subprocess.run([
            'python3', 'description_generator.py',
            '--test-url', 'invalid-url'
        ], capture_output=True, text=True, cwd=self.script_dir, timeout=10)
        
        if result1.returncode == 0:  # 工具应该能处理无效URL
            print("  ✅ 无效URL处理 - 正确处理错误")
        else:
            print("  ❌ 无效URL处理 - 处理异常")
            
        # 测试不存在的文件
        result2 = subprocess.run([
            'python3', 'description_generator.py',
            '--file', '/nonexistent/file.yml'
        ], capture_output=True, text=True, cwd=self.script_dir, timeout=10)
        
        if result2.returncode != 0:  # 应该失败
            print("  ✅ 不存在的webstack文件 - 正确处理错误")
        else:
            print("  ❌ 不存在的webstack文件 - 应该报错但没有")
            
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 描述生成工具测试套件")
        print("=" * 50)
        
        tests = [
            self.test_single_url,
            self.test_batch_processing,
            self.test_all_option
        ]
        
        self.total_tests = len(tests)
        
        for test in tests:
            try:
                test()
            except subprocess.TimeoutExpired:
                print("  ⏰ 测试超时")
            except Exception as e:
                print(f"  💥 测试异常: {e}")
                
        # 额外测试
        self.test_webstack_processing()
        self.test_error_handling()
        
        # 总结
        print("\n📊 测试结果汇总:")
        print("=" * 50)
        test_names = [
            "测试单个URL描述生成",
            "测试批量处理",
            "测试--all选项",
            "webstack文件处理功能正常",
            "错误处理功能正常"
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
    tester = DescriptionGeneratorTest()
    tester.run_all_tests()

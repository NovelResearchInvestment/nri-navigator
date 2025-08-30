#!/usr/bin/env python3
"""
NRI Navigator 工具测试套件主运行器
"""

import os
import sys
import subprocess

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def run_test_script(script_name, tool_name):
    """运行单个测试脚本"""
    print(f"🔧 测试 {tool_name}...")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            'python3', script_name
        ], cwd=current_dir, capture_output=False, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {tool_name} 测试通过\n")
            return True
        else:
            print(f"❌ {tool_name} 测试失败\n")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {tool_name} 测试超时\n")
        return False
    except Exception as e:
        print(f"💥 {tool_name} 测试异常: {e}\n")
        return False

def main():
    """主函数"""
    print("🧪 NRI Navigator 工具测试套件")
    print("=" * 60)
    print()
    
    # 确保results目录存在
    results_dir = os.path.join(parent_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    # 测试项目
    tests = [
        ('test_logo_tool.py', 'Logo Tool'),
        ('test_link_checker.py', 'Link Checker'),
        ('test_description_generator.py', 'Description Generator')
    ]
    
    passed = 0
    total = len(tests)
    
    for script, tool in tests:
        if run_test_script(script, tool):
            passed += 1
    
    # 总结
    print("📊 总体测试结果:")
    print("=" * 60)
    
    test_results = [
        ('Logo Tool', passed >= 1),
        ('Link Checker', passed >= 2),
        ('Description Generator', passed >= 3)
    ]
    
    for tool, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {tool}: {status}")
    
    print(f"\n🎯 测试通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有工具测试通过!")
        return 0
    else:
        print("⚠️  部分工具测试失败，请检查问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())

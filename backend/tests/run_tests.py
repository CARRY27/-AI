"""
测试运行脚本
自动化运行所有测试并生成报告
"""

import subprocess
import sys
import os
import time
from datetime import datetime


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None
    
    def print_header(self, title):
        """打印标题"""
        print("\n" + "="*80)
        print(f"  {title}")
        print("="*80 + "\n")
    
    def run_command(self, cmd, description):
        """运行命令并记录结果"""
        self.print_header(description)
        print(f"执行命令: {cmd}\n")
        
        start = time.time()
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            elapsed = time.time() - start
            
            # 输出结果
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            success = result.returncode == 0
            
            self.results.append({
                "description": description,
                "command": cmd,
                "success": success,
                "elapsed": elapsed,
                "returncode": result.returncode
            })
            
            if success:
                print(f"\n✅ 测试通过 ({elapsed:.2f}秒)")
            else:
                print(f"\n❌ 测试失败 (返回码: {result.returncode})")
            
            return success
            
        except subprocess.TimeoutExpired:
            print("\n⏱️ 测试超时")
            self.results.append({
                "description": description,
                "command": cmd,
                "success": False,
                "elapsed": 300,
                "returncode": -1,
                "error": "Timeout"
            })
            return False
        except Exception as e:
            print(f"\n❌ 执行错误: {e}")
            self.results.append({
                "description": description,
                "command": cmd,
                "success": False,
                "elapsed": 0,
                "error": str(e)
            })
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        self.start_time = time.time()
        
        print("\n" + "🚀"*40)
        print("  DocAgent 自动化测试套件")
        print(f"  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🚀"*40)
        
        # 1. 单元测试（白盒测试）
        self.run_command(
            "pytest tests/test_unit_feedback.py -v --tb=short",
            "1. 单元测试 - 反馈系统"
        )
        
        # 2. API 测试（黑盒测试）
        self.run_command(
            "pytest tests/test_api_feedback.py -v --tb=short",
            "2. API 测试 - 反馈端点"
        )
        
        # 3. 集成测试（链路测试）
        self.run_command(
            "pytest tests/test_integration_e2e.py -v --tb=short",
            "3. 集成测试 - 端到端流程"
        )
        
        # 4. 边缘测试
        self.run_command(
            "pytest tests/test_edge_cases.py -v --tb=short",
            "4. 边缘测试 - 边界条件"
        )
        
        # 5. 压力测试
        self.run_command(
            "pytest tests/test_stress_load.py -v --tb=short -x",
            "5. 压力测试 - 负载测试"
        )
        
        # 6. 代码覆盖率测试
        self.run_command(
            "pytest tests/ --cov=app --cov-report=html --cov-report=term",
            "6. 代码覆盖率测试"
        )
        
        self.end_time = time.time()
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        self.print_header("📊 测试结果汇总")
        
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total_tests - passed
        total_time = self.end_time - self.start_time
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌")
        print(f"通过率: {passed/total_tests*100:.2f}%")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"\n{'测试项':<40} {'状态':<10} {'耗时':<10}")
        print("-"*80)
        
        for result in self.results:
            status = "✅ 通过" if result["success"] else "❌ 失败"
            elapsed = f"{result['elapsed']:.2f}s"
            print(f"{result['description']:<40} {status:<10} {elapsed:<10}")
        
        print("\n" + "="*80)
        
        # 保存报告到文件
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("DocAgent 测试报告\n")
            f.write("="*80 + "\n\n")
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总测试数: {total_tests}\n")
            f.write(f"通过: {passed}\n")
            f.write(f"失败: {failed}\n")
            f.write(f"通过率: {passed/total_tests*100:.2f}%\n")
            f.write(f"总耗时: {total_time:.2f}秒\n\n")
            
            for result in self.results:
                f.write(f"\n{result['description']}\n")
                f.write(f"  命令: {result['command']}\n")
                f.write(f"  状态: {'通过' if result['success'] else '失败'}\n")
                f.write(f"  耗时: {result['elapsed']:.2f}秒\n")
                if 'error' in result:
                    f.write(f"  错误: {result['error']}\n")
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        # 返回退出码
        return 0 if failed == 0 else 1


def main():
    """主函数"""
    runner = TestRunner()
    exit_code = runner.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()


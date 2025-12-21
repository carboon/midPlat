#!/usr/bin/env python3
"""
AI 游戏平台 - 完整测试套件
包含环境清理、验证、单元测试和集成测试
"""
import subprocess
import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class TestResult:
    """测试结果数据类"""
    name: str
    status: str  # PASS, FAIL, SKIP, ERROR
    duration: float
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    reason: str = ""


class TestRunner:
    """测试运行器"""
    
    def __init__(self, verbose: bool = False, timeout: int = 300):
        self.verbose = verbose
        self.timeout = timeout
        self.results: List[TestResult] = []
        self.workspace_root = Path.cwd()
        self.log_dir = self.workspace_root / ".kiro_workspace" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def run_command(
        self, 
        cmd: str, 
        cwd: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Tuple[int, str, str]:
        """运行命令并返回结果"""
        try:
            if timeout is None:
                timeout = self.timeout
                
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"命令超时 (>{timeout}s)"
        except Exception as e:
            return -1, "", str(e)
    
    def log_message(self, message: str, level: str = "INFO"):
        """记录消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        # 写入日志文件
        log_file = self.log_dir / "test_execution.log"
        with open(log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def section(self, title: str):
        """打印分隔符"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    
    # ========== 第一阶段：环境清理 ==========
    
    def clean_docker_environment(self) -> bool:
        """清理 Docker 环境"""
        self.log_message("清理 Docker 环境...")
        
        commands = [
            ("停止容器", "docker-compose down -v 2>/dev/null || true"),
            ("清理系统", "docker system prune -f 2>/dev/null || true"),
            ("清理卷", "docker volume prune -f 2>/dev/null || true"),
            ("删除网络", "docker network rm game-network 2>/dev/null || true"),
        ]
        
        for desc, cmd in commands:
            self.log_message(f"  - {desc}...", "DEBUG")
            returncode, _, stderr = self.run_command(cmd)
            if returncode != 0 and "not found" not in stderr.lower():
                self.log_message(f"    警告: {stderr[:100]}", "WARN")
        
        return True
    
    def clean_python_environment(self) -> bool:
        """清理 Python 环境"""
        self.log_message("清理 Python 环境...")
        
        # 清理缓存目录
        patterns = [
            "**/__pycache__",
            "**/.pytest_cache",
            "**/*.pyc",
        ]
        
        for pattern in patterns:
            for path in self.workspace_root.glob(pattern):
                try:
                    if path.is_dir():
                        import shutil
                        shutil.rmtree(path)
                        self.log_message(f"  - 删除 {path}", "DEBUG")
                    else:
                        path.unlink()
                except Exception as e:
                    self.log_message(f"  - 删除失败 {path}: {e}", "WARN")
        
        return True
    
    def clean_nodejs_environment(self) -> bool:
        """清理 Node.js 环境"""
        self.log_message("清理 Node.js 环境...")
        
        node_dirs = [
            "game_server_template/node_modules",
            "game_server_template/package-lock.json",
        ]
        
        for dir_path in node_dirs:
            full_path = self.workspace_root / dir_path
            if full_path.exists():
                try:
                    if full_path.is_dir():
                        import shutil
                        shutil.rmtree(full_path)
                    else:
                        full_path.unlink()
                    self.log_message(f"  - 删除 {dir_path}", "DEBUG")
                except Exception as e:
                    self.log_message(f"  - 删除失败 {dir_path}: {e}", "WARN")
        
        # 清理 npm 缓存
        self.run_command("npm cache clean --force 2>/dev/null || true")
        
        return True
    
    def clean_flutter_environment(self) -> bool:
        """清理 Flutter 环境"""
        self.log_message("清理 Flutter 环境...")
        
        flutter_dirs = [
            "mobile_app/universal_game_client/.dart_tool",
            "mobile_app/universal_game_client/build",
        ]
        
        for dir_path in flutter_dirs:
            full_path = self.workspace_root / dir_path
            if full_path.exists():
                try:
                    import shutil
                    shutil.rmtree(full_path)
                    self.log_message(f"  - 删除 {dir_path}", "DEBUG")
                except Exception as e:
                    self.log_message(f"  - 删除失败 {dir_path}: {e}", "WARN")
        
        # 运行 flutter clean
        returncode, _, _ = self.run_command("flutter clean 2>/dev/null || true")
        
        return True
    
    # ========== 第二阶段：环境搭建 ==========
    
    def setup_env_file(self) -> bool:
        """设置环境文件"""
        self.log_message("设置环境文件...")
        
        env_file = self.workspace_root / ".env"
        env_example = self.workspace_root / ".env.example"
        
        if not env_file.exists() and env_example.exists():
            try:
                import shutil
                shutil.copy(env_example, env_file)
                self.log_message("  - 已从 .env.example 创建 .env", "DEBUG")
            except Exception as e:
                self.log_message(f"  - 创建 .env 失败: {e}", "ERROR")
                return False
        
        return True
    
    def setup_docker_network(self) -> bool:
        """设置 Docker 网络"""
        self.log_message("设置 Docker 网络...")
        
        returncode, stdout, stderr = self.run_command(
            "docker network create game-network 2>/dev/null || true"
        )
        
        if returncode == 0:
            self.log_message("  - game-network 已创建或已存在", "DEBUG")
            return True
        else:
            self.log_message(f"  - 创建网络失败: {stderr[:100]}", "ERROR")
            return False
    
    def setup_python_dependencies(self) -> bool:
        """安装 Python 依赖"""
        self.log_message("安装 Python 依赖...")
        
        # Game Server Factory
        factory_dir = self.workspace_root / "game_server_factory"
        if factory_dir.exists():
            self.log_message("  - 安装 Game Server Factory 依赖...", "DEBUG")
            for req_file in ["requirements.txt", "requirements-test.txt"]:
                req_path = factory_dir / req_file
                if req_path.exists():
                    returncode, _, stderr = self.run_command(
                        f"pip3 install -q -r {req_file}",
                        cwd=str(factory_dir)
                    )
                    if returncode != 0:
                        self.log_message(f"    警告: 安装 {req_file} 失败", "WARN")
        
        # Matchmaker Service
        matchmaker_dir = self.workspace_root / "matchmaker_service" / "matchmaker"
        if matchmaker_dir.exists():
            self.log_message("  - 安装 Matchmaker Service 依赖...", "DEBUG")
            req_path = matchmaker_dir / "requirements.txt"
            if req_path.exists():
                returncode, _, stderr = self.run_command(
                    "pip3 install -q -r requirements.txt",
                    cwd=str(matchmaker_dir)
                )
                if returncode != 0:
                    self.log_message(f"    警告: 安装依赖失败", "WARN")
        
        return True
    
    def setup_nodejs_dependencies(self) -> bool:
        """安装 Node.js 依赖"""
        self.log_message("安装 Node.js 依赖...")
        
        template_dir = self.workspace_root / "game_server_template"
        if template_dir.exists():
            self.log_message("  - 安装 Game Server Template 依赖...", "DEBUG")
            returncode, _, stderr = self.run_command(
                "npm install --legacy-peer-deps",
                cwd=str(template_dir)
            )
            if returncode != 0:
                self.log_message(f"    警告: npm install 失败", "WARN")
                return False
        
        return True
    
    def setup_flutter_dependencies(self) -> bool:
        """安装 Flutter 依赖"""
        self.log_message("安装 Flutter 依赖...")
        
        flutter_dir = self.workspace_root / "mobile_app" / "universal_game_client"
        if flutter_dir.exists():
            self.log_message("  - 安装 Flutter 依赖...", "DEBUG")
            returncode, _, stderr = self.run_command(
                "flutter pub get",
                cwd=str(flutter_dir)
            )
            if returncode != 0:
                self.log_message(f"    警告: flutter pub get 失败", "WARN")
                return False
        
        return True
    
    # ========== 第三阶段：环境验证 ==========
    
    def verify_python_environment(self) -> bool:
        """验证 Python 环境"""
        self.log_message("验证 Python 环境...")
        
        checks = [
            ("pytest", "python3 -m pytest --version"),
            ("hypothesis", "python3 -c 'import hypothesis; print(hypothesis.__version__)'"),
            ("fastapi", "python3 -c 'import fastapi; print(fastapi.__version__)'"),
        ]
        
        all_ok = True
        for name, cmd in checks:
            returncode, stdout, _ = self.run_command(cmd)
            if returncode == 0:
                self.log_message(f"  ✓ {name}: {stdout.strip()}", "DEBUG")
            else:
                self.log_message(f"  ✗ {name} 未安装", "WARN")
                all_ok = False
        
        return all_ok
    
    def verify_nodejs_environment(self) -> bool:
        """验证 Node.js 环境"""
        self.log_message("验证 Node.js 环境...")
        
        checks = [
            ("node", "node --version"),
            ("npm", "npm --version"),
        ]
        
        all_ok = True
        for name, cmd in checks:
            returncode, stdout, _ = self.run_command(cmd)
            if returncode == 0:
                self.log_message(f"  ✓ {name}: {stdout.strip()}", "DEBUG")
            else:
                self.log_message(f"  ✗ {name} 未安装", "WARN")
                all_ok = False
        
        return all_ok
    
    def verify_flutter_environment(self) -> bool:
        """验证 Flutter 环境"""
        self.log_message("验证 Flutter 环境...")
        
        returncode, stdout, _ = self.run_command("flutter --version")
        if returncode == 0:
            self.log_message(f"  ✓ Flutter: {stdout.split()[1] if len(stdout.split()) > 1 else 'OK'}", "DEBUG")
            return True
        else:
            self.log_message("  ✗ Flutter 未安装", "WARN")
            return False
    
    def verify_docker_environment(self) -> bool:
        """验证 Docker 环境"""
        self.log_message("验证 Docker 环境...")
        
        checks = [
            ("docker", "docker ps"),
            ("docker-compose", "docker-compose --version"),
            ("game-network", "docker network inspect game-network"),
        ]
        
        all_ok = True
        for name, cmd in checks:
            returncode, stdout, _ = self.run_command(cmd)
            if returncode == 0:
                self.log_message(f"  ✓ {name}", "DEBUG")
            else:
                self.log_message(f"  ✗ {name} 检查失败", "WARN")
                all_ok = False
        
        return all_ok
    
    # ========== 第四阶段：单元测试 ==========
    
    def test_game_server_factory(self) -> TestResult:
        """测试 Game Server Factory"""
        self.log_message("运行 Game Server Factory 测试...")
        
        start_time = time.time()
        factory_dir = self.workspace_root / "TEST" / "game_server_factory"
        
        if not factory_dir.exists():
            return TestResult(
                name="Game Server Factory",
                status="SKIP",
                duration=0,
                reason="目录不存在"
            )
        
        cmd = "python3 -m pytest . -v --tb=short --timeout=120"
        returncode, stdout, stderr = self.run_command(cmd, cwd=str(factory_dir))
        duration = time.time() - start_time
        
        status = "PASS" if returncode == 0 else "FAIL"
        
        result = TestResult(
            name="Game Server Factory",
            status=status,
            duration=duration,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr
        )
        
        self.results.append(result)
        self.log_message(f"  {status} ({duration:.1f}s)", "DEBUG")
        
        return result
    
    def test_matchmaker_service(self) -> TestResult:
        """测试 Matchmaker Service"""
        self.log_message("运行 Matchmaker Service 测试...")
        
        start_time = time.time()
        matchmaker_dir = self.workspace_root / "TEST" / "matchmaker_service"
        
        if not matchmaker_dir.exists():
            return TestResult(
                name="Matchmaker Service",
                status="SKIP",
                duration=0,
                reason="目录不存在"
            )
        
        cmd = "python3 -m pytest . -v --tb=short -W ignore::DeprecationWarning"
        returncode, stdout, stderr = self.run_command(cmd, cwd=str(matchmaker_dir))
        duration = time.time() - start_time
        
        status = "PASS" if returncode == 0 else "FAIL"
        
        result = TestResult(
            name="Matchmaker Service",
            status=status,
            duration=duration,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr
        )
        
        self.results.append(result)
        self.log_message(f"  {status} ({duration:.1f}s)", "DEBUG")
        
        return result
    
    def test_game_server_template(self) -> TestResult:
        """测试 Game Server Template"""
        self.log_message("运行 Game Server Template 测试...")
        
        start_time = time.time()
        # 对于 Node.js 项目，从原始目录运行测试
        template_dir = self.workspace_root / "game_server_template"
        
        if not template_dir.exists():
            return TestResult(
                name="Game Server Template",
                status="SKIP",
                duration=0,
                reason="目录不存在"
            )
        
        cmd = "npm test -- --runInBand --testTimeout=30000"
        returncode, stdout, stderr = self.run_command(cmd, cwd=str(template_dir))
        duration = time.time() - start_time
        
        status = "PASS" if returncode == 0 else "FAIL"
        
        result = TestResult(
            name="Game Server Template",
            status=status,
            duration=duration,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr
        )
        
        self.results.append(result)
        self.log_message(f"  {status} ({duration:.1f}s)", "DEBUG")
        
        return result
    
    def test_flutter_client(self) -> TestResult:
        """测试 Flutter Client"""
        self.log_message("运行 Flutter Client 测试...")
        
        start_time = time.time()
        # 对于 Flutter 项目，从原始目录运行测试
        flutter_dir = self.workspace_root / "mobile_app" / "universal_game_client"
        
        if not flutter_dir.exists():
            return TestResult(
                name="Flutter Client",
                status="SKIP",
                duration=0,
                reason="目录不存在"
            )
        
        cmd = "flutter test --no-pub 2>&1"
        returncode, stdout, stderr = self.run_command(cmd, cwd=str(flutter_dir), timeout=180)
        duration = time.time() - start_time
        
        status = "PASS" if returncode == 0 else "FAIL"
        
        result = TestResult(
            name="Flutter Client",
            status=status,
            duration=duration,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr
        )
        
        self.results.append(result)
        self.log_message(f"  {status} ({duration:.1f}s)", "DEBUG")
        
        return result
    
    # ========== 报告生成 ==========
    
    def print_summary(self):
        """打印测试总结"""
        self.section("测试结果汇总")
        
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        total_duration = sum(r.duration for r in self.results)
        
        for result in self.results:
            icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "ERROR": "⚠️"}.get(result.status, "❓")
            print(f"{icon} {result.name}: {result.status} ({result.duration:.1f}s)")
            if result.reason:
                print(f"   原因: {result.reason}")
        
        print(f"\n总计: {passed} 通过, {failed} 失败, {skipped} 跳过")
        print(f"总耗时: {total_duration:.1f}s")
        
        # 保存结果到 JSON
        self.save_results_json()
        
        return failed == 0
    
    def print_failures(self):
        """打印失败详情"""
        failures = [r for r in self.results if r.status == "FAIL"]
        
        if not failures:
            return
        
        self.section("失败测试详情")
        
        for result in failures:
            print(f"\n--- {result.name} ---")
            print(f"返回码: {result.returncode}")
            
            if result.stderr:
                print("\n错误输出:")
                print(result.stderr[:1000])
                if len(result.stderr) > 1000:
                    print("... (截断)")
            
            if result.stdout:
                print("\n标准输出 (最后 500 字符):")
                print(result.stdout[-500:])
    
    def save_results_json(self):
        """保存结果为 JSON"""
        results_file = self.log_dir / "test_results.json"
        
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": sum(r.duration for r in self.results),
            "summary": {
                "passed": sum(1 for r in self.results if r.status == "PASS"),
                "failed": sum(1 for r in self.results if r.status == "FAIL"),
                "skipped": sum(1 for r in self.results if r.status == "SKIP"),
            },
            "results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "duration": r.duration,
                    "returncode": r.returncode,
                    "reason": r.reason,
                }
                for r in self.results
            ]
        }
        
        with open(results_file, "w") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        self.log_message(f"结果已保存到 {results_file}", "INFO")
    
    # ========== 主执行流程 ==========
    
    def run_all(self) -> bool:
        """运行完整测试流程"""
        try:
            # 第一阶段：环境清理
            self.section("第一阶段：环境清理")
            self.clean_docker_environment()
            self.clean_python_environment()
            self.clean_nodejs_environment()
            self.clean_flutter_environment()
            
            # 第二阶段：环境搭建
            self.section("第二阶段：环境搭建")
            self.setup_env_file()
            self.setup_docker_network()
            self.setup_python_dependencies()
            self.setup_nodejs_dependencies()
            self.setup_flutter_dependencies()
            
            # 第三阶段：环境验证
            self.section("第三阶段：环境验证")
            self.verify_python_environment()
            self.verify_nodejs_environment()
            self.verify_flutter_environment()
            self.verify_docker_environment()
            
            # 第四阶段：单元测试
            self.section("第四阶段：单元测试")
            self.test_game_server_factory()
            self.test_matchmaker_service()
            self.test_game_server_template()
            self.test_flutter_client()
            
            # 打印结果
            success = self.print_summary()
            self.print_failures()
            
            return success
            
        except KeyboardInterrupt:
            self.log_message("测试被用户中断", "WARN")
            return False
        except Exception as e:
            self.log_message(f"测试执行出错: {e}", "ERROR")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI 游戏平台测试套件")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("-t", "--timeout", type=int, default=300, help="单个测试超时时间（秒）")
    
    args = parser.parse_args()
    
    runner = TestRunner(verbose=args.verbose, timeout=args.timeout)
    success = runner.run_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

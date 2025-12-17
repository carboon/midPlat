"""
JavaScript代码分析和安全检查模块
使用AST解析JavaScript代码，检测潜在的恶意操作
"""

import ast
import re
import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SecurityIssue:
    """安全问题数据类"""
    severity: str  # "high", "medium", "low"
    message: str
    line: int
    code_snippet: str

@dataclass
class AnalysisResult:
    """代码分析结果"""
    is_valid: bool
    syntax_errors: List[str]
    security_issues: List[SecurityIssue]
    warnings: List[str]
    suggestions: List[str]

class JavaScriptCodeAnalyzer:
    """JavaScript代码分析器"""
    
    def __init__(self):
        # 危险的JavaScript模式
        self.dangerous_patterns = [
            # 文件系统访问
            (r'require\s*\(\s*[\'"]fs[\'"]', "high", "检测到文件系统访问"),
            (r'require\s*\(\s*[\'"]path[\'"]', "medium", "检测到路径操作"),
            (r'require\s*\(\s*[\'"]child_process[\'"]', "high", "检测到子进程执行"),
            
            # 网络请求
            (r'require\s*\(\s*[\'"]http[\'"]', "medium", "检测到HTTP模块使用"),
            (r'require\s*\(\s*[\'"]https[\'"]', "medium", "检测到HTTPS模块使用"),
            (r'require\s*\(\s*[\'"]net[\'"]', "medium", "检测到网络模块使用"),
            
            # 危险函数
            (r'eval\s*\(', "high", "检测到eval函数使用"),
            (r'(?<!\w)Function\s*\(', "high", "检测到Function构造函数"),
            (r'setTimeout\s*\(\s*[\'"]', "medium", "检测到字符串形式的setTimeout"),
            (r'setInterval\s*\(\s*[\'"]', "medium", "检测到字符串形式的setInterval"),
            
            # 系统操作
            (r'process\.exit', "medium", "检测到进程退出操作"),
            (r'process\.env', "low", "检测到环境变量访问"),
            (r'__dirname', "low", "检测到目录路径访问"),
            (r'__filename', "low", "检测到文件路径访问"),
            
            # 危险的全局对象
            (r'global\s*\.', "medium", "检测到全局对象操作"),
            (r'Buffer\s*\.', "medium", "检测到Buffer操作"),
        ]
        
        # 必需的游戏服务器结构
        self.required_patterns = [
            (r'module\.exports\s*=', "导出游戏逻辑"),
            (r'function.*handleConnection', "处理连接的函数"),
        ]
    
    def analyze_code(self, code: str) -> AnalysisResult:
        """分析JavaScript代码"""
        try:
            logger.info("开始分析JavaScript代码")
            
            # 基础语法检查
            syntax_errors = self._check_syntax(code)
            
            # 安全检查
            security_issues = self._security_scan(code)
            
            # 结构检查
            warnings = self._check_structure(code)
            
            # 生成建议
            suggestions = self._generate_suggestions(code, security_issues, warnings)
            
            is_valid = len(syntax_errors) == 0 and not any(
                issue.severity == "high" for issue in security_issues
            )
            
            result = AnalysisResult(
                is_valid=is_valid,
                syntax_errors=syntax_errors,
                security_issues=security_issues,
                warnings=warnings,
                suggestions=suggestions
            )
            
            logger.info(f"代码分析完成: valid={is_valid}, errors={len(syntax_errors)}, issues={len(security_issues)}")
            return result
            
        except Exception as e:
            logger.error(f"代码分析失败: {str(e)}")
            return AnalysisResult(
                is_valid=False,
                syntax_errors=[f"分析过程中发生错误: {str(e)}"],
                security_issues=[],
                warnings=[],
                suggestions=[]
            )
    
    def _check_syntax(self, code: str) -> List[str]:
        """检查JavaScript语法"""
        errors = []
        
        try:
            # 基础的JavaScript语法检查
            lines = code.split('\n')
            
            # 检查括号匹配
            bracket_stack = []
            bracket_pairs = {'(': ')', '[': ']', '{': '}'}
            
            for line_num, line in enumerate(lines, 1):
                for char in line:
                    if char in bracket_pairs:
                        bracket_stack.append((char, line_num))
                    elif char in bracket_pairs.values():
                        if not bracket_stack:
                            errors.append(f"第{line_num}行: 未匹配的闭合括号 '{char}'")
                        else:
                            open_char, open_line = bracket_stack.pop()
                            if bracket_pairs[open_char] != char:
                                errors.append(f"第{line_num}行: 括号不匹配，期望 '{bracket_pairs[open_char]}' 但找到 '{char}'")
            
            # 检查未闭合的括号
            for open_char, line_num in bracket_stack:
                errors.append(f"第{line_num}行: 未闭合的括号 '{open_char}'")
            
            # 检查基本的JavaScript结构
            if 'module.exports' not in code and 'export' not in code:
                errors.append("缺少模块导出语句 (module.exports 或 export)")
            
        except Exception as e:
            errors.append(f"语法检查过程中发生错误: {str(e)}")
        
        return errors
    
    def _security_scan(self, code: str) -> List[SecurityIssue]:
        """安全扫描"""
        issues = []
        lines = code.split('\n')
        
        for pattern, severity, message in self.dangerous_patterns:
            for line_num, line in enumerate(lines, 1):
                # Function constructor pattern should be case-sensitive
                if "Function构造函数" in message:
                    match = re.search(pattern, line)  # Case-sensitive for Function
                else:
                    match = re.search(pattern, line, re.IGNORECASE)  # Case-insensitive for others
                
                if match:
                    issues.append(SecurityIssue(
                        severity=severity,
                        message=message,
                        line=line_num,
                        code_snippet=line.strip()
                    ))
        
        return issues
    
    def _check_structure(self, code: str) -> List[str]:
        """检查代码结构"""
        warnings = []
        
        # 检查是否包含必要的游戏服务器结构
        if 'socket' not in code.lower():
            warnings.append("建议包含WebSocket处理逻辑")
        
        if 'gameState' not in code and 'game_state' not in code:
            warnings.append("建议定义游戏状态管理")
        
        if 'handleConnection' not in code and 'onConnection' not in code:
            warnings.append("建议实现连接处理函数")
        
        # 检查代码长度
        lines = code.split('\n')
        if len(lines) > 1000:
            warnings.append("代码行数过多，建议拆分为多个模块")
        
        return warnings
    
    def _generate_suggestions(self, code: str, security_issues: List[SecurityIssue], warnings: List[str]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 基于安全问题的建议
        high_severity_count = sum(1 for issue in security_issues if issue.severity == "high")
        if high_severity_count > 0:
            suggestions.append(f"发现{high_severity_count}个高风险安全问题，请移除危险的系统调用")
        
        medium_severity_count = sum(1 for issue in security_issues if issue.severity == "medium")
        if medium_severity_count > 0:
            suggestions.append(f"发现{medium_severity_count}个中等风险问题，建议使用更安全的替代方案")
        
        # 基于代码结构的建议
        if 'console.log' in code:
            suggestions.append("建议使用结构化日志记录替代console.log")
        
        if 'var ' in code:
            suggestions.append("建议使用let或const替代var声明变量")
        
        # 性能建议
        if code.count('setInterval') > 3:
            suggestions.append("检测到多个定时器，注意性能影响")
        
        return suggestions

def validate_file_upload(file_content: bytes, filename: str) -> Tuple[bool, str]:
    """验证上传的文件"""
    try:
        # 检查文件大小
        max_size = 1024 * 1024  # 1MB
        if len(file_content) > max_size:
            return False, f"文件大小超过限制 ({len(file_content)} > {max_size} bytes)"
        
        # 检查文件扩展名
        allowed_extensions = ['.js', '.mjs']
        if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
            return False, f"不支持的文件类型，仅支持: {', '.join(allowed_extensions)}"
        
        # 检查文件内容是否为有效的文本
        try:
            code = file_content.decode('utf-8')
        except UnicodeDecodeError:
            return False, "文件编码无效，请使用UTF-8编码"
        
        # 基础内容检查
        if len(code.strip()) == 0:
            return False, "文件内容为空"
        
        return True, "文件验证通过"
        
    except Exception as e:
        return False, f"文件验证过程中发生错误: {str(e)}"
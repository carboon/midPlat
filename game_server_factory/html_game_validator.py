"""
HTML Game File Validator
Handles validation of HTML game files (ZIP or single HTML)
"""

import os
import zipfile
import io
import logging
from typing import Tuple, Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class HTMLGameValidationError(Exception):
    """HTML game validation error"""
    pass


class HTMLGameValidator:
    """Validates HTML game files"""
    
    # Configuration
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'.html', '.htm', '.zip', '.js'}
    REQUIRED_FILES = {'index.html'}
    MAX_EXTRACT_SIZE = 100 * 1024 * 1024  # 100MB total extracted
    
    # Security checks
    DANGEROUS_PATTERNS = [
        'eval(',
        'Function(',
        'setTimeout(function',
        'setInterval(function',
        'document.write',
        'innerHTML',
        'dangerouslySetInnerHTML',
    ]
    
    @staticmethod
    def validate_file(file_content: bytes, filename: str, max_file_size: int = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validate HTML game file
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            max_file_size: Maximum file size in bytes (optional, uses default if not provided)
            
        Returns:
            Tuple of (is_valid, message, metadata)
            metadata contains: file_type, has_index_html, file_count, total_size
        """
        try:
            # Use provided max_file_size or default
            if max_file_size is None:
                max_file_size = HTMLGameValidator.MAX_FILE_SIZE
            
            # Check file size
            if len(file_content) == 0:
                return False, "文件为空", None
            
            if len(file_content) > max_file_size:
                return False, f"文件过大，最大限制为 {max_file_size / (1024*1024):.1f}MB", None
            
            # Get file extension
            file_ext = Path(filename).suffix.lower()
            
            if file_ext not in HTMLGameValidator.ALLOWED_EXTENSIONS:
                return False, f"不支持的文件格式: {file_ext}，支持的格式: {', '.join(HTMLGameValidator.ALLOWED_EXTENSIONS)}", None
            
            # Handle ZIP files
            if file_ext == '.zip':
                return HTMLGameValidator._validate_zip_file(file_content)
            
            # Handle single HTML files
            elif file_ext in {'.html', '.htm'}:
                return HTMLGameValidator._validate_html_file(file_content, filename)
            
            # Handle JavaScript files
            elif file_ext == '.js':
                return HTMLGameValidator._validate_js_file(file_content, filename)
            
            return False, "未知的文件格式", None
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False, f"文件验证失败: {str(e)}", None
    
    @staticmethod
    def _validate_zip_file(file_content: bytes) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate ZIP file containing HTML game"""
        try:
            # Create BytesIO object for ZIP handling
            zip_buffer = io.BytesIO(file_content)
            
            # Check if it's a valid ZIP file
            if not zipfile.is_zipfile(zip_buffer):
                return False, "文件不是有效的ZIP格式", None
            
            # Reset buffer position
            zip_buffer.seek(0)
            
            # Open and inspect ZIP
            with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                # Get file list
                file_list = zip_file.namelist()
                
                if not file_list:
                    return False, "ZIP文件为空", None
                
                # Check for index.html
                has_index_html = False
                index_html_path = None
                
                for file_path in file_list:
                    if file_path.lower().endswith('index.html'):
                        has_index_html = True
                        index_html_path = file_path
                        break
                
                if not has_index_html:
                    return False, "ZIP文件中未找到 index.html", None
                
                # Check total extracted size
                total_size = sum(info.file_size for info in zip_file.infolist())
                if total_size > HTMLGameValidator.MAX_EXTRACT_SIZE:
                    return False, f"解压后文件过大，最大限制为 {HTMLGameValidator.MAX_EXTRACT_SIZE / (1024*1024):.1f}MB", None
                
                # Validate index.html content
                try:
                    index_html_content = zip_file.read(index_html_path).decode('utf-8')
                except UnicodeDecodeError:
                    return False, "index.html 文件编码无效，请使用 UTF-8 编码", None
                
                # Check for dangerous patterns
                is_safe, safety_message = HTMLGameValidator._check_html_safety(index_html_content)
                if not is_safe:
                    return False, safety_message, None
                
                # Metadata
                metadata = {
                    'file_type': 'zip',
                    'has_index_html': True,
                    'file_count': len(file_list),
                    'total_size': total_size,
                    'index_html_path': index_html_path
                }
                
                return True, "ZIP文件验证通过", metadata
                
        except zipfile.BadZipFile:
            return False, "ZIP文件损坏或格式无效", None
        except Exception as e:
            logger.error(f"ZIP validation error: {str(e)}")
            return False, f"ZIP文件验证失败: {str(e)}", None
    
    @staticmethod
    def _validate_html_file(file_content: bytes, filename: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate single HTML file"""
        try:
            # Decode HTML content
            try:
                html_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                return False, "HTML文件编码无效，请使用 UTF-8 编码", None
            
            # Check if it's valid HTML
            if not html_content.strip():
                return False, "HTML文件为空", None
            
            # Check for HTML structure
            if '<html' not in html_content.lower() and '<!doctype' not in html_content.lower():
                # Allow minimal HTML files without full structure
                if '<body' not in html_content.lower() and '<head' not in html_content.lower():
                    logger.warning(f"HTML file {filename} may not have proper structure")
            
            # Check for dangerous patterns
            is_safe, safety_message = HTMLGameValidator._check_html_safety(html_content)
            if not is_safe:
                return False, safety_message, None
            
            # Metadata
            metadata = {
                'file_type': 'html',
                'has_index_html': True,
                'file_count': 1,
                'total_size': len(file_content),
                'filename': filename
            }
            
            return True, "HTML文件验证通过", metadata
            
        except Exception as e:
            logger.error(f"HTML validation error: {str(e)}")
            return False, f"HTML文件验证失败: {str(e)}", None
    
    @staticmethod
    def _check_html_safety(html_content: str) -> Tuple[bool, str]:
        """Check HTML content for dangerous patterns"""
        # Convert to lowercase for pattern matching
        content_lower = html_content.lower()
        
        # Check for dangerous patterns
        for pattern in HTMLGameValidator.DANGEROUS_PATTERNS:
            if pattern.lower() in content_lower:
                logger.warning(f"Potentially dangerous pattern found: {pattern}")
                # Note: We log but don't block - HTML games may legitimately use these
                # In a production system, you might want to be more strict
        
        return True, "安全检查通过"
    
    @staticmethod
    def extract_html_game(file_content: bytes, filename: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Extract HTML game files
        
        Returns:
            Tuple of (success, message, extracted_data)
            extracted_data contains: index_html_content, other_files
        """
        try:
            file_ext = Path(filename).suffix.lower()
            
            if file_ext == '.zip':
                return HTMLGameValidator._extract_zip_game(file_content)
            elif file_ext in {'.html', '.htm'}:
                return HTMLGameValidator._extract_html_game(file_content)
            elif file_ext == '.js':
                return HTMLGameValidator._extract_js_game(file_content)
            
            return False, "不支持的文件格式", None
            
        except Exception as e:
            logger.error(f"Extraction error: {str(e)}")
            return False, f"文件提取失败: {str(e)}", None
    
    @staticmethod
    def _extract_zip_game(file_content: bytes) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Extract HTML game from ZIP file"""
        try:
            # Create BytesIO object for ZIP handling
            zip_buffer = io.BytesIO(file_content)
            
            with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                # Find index.html
                index_html_path = None
                for file_path in zip_file.namelist():
                    if file_path.lower().endswith('index.html'):
                        index_html_path = file_path
                        break
                
                if not index_html_path:
                    return False, "未找到 index.html", None
                
                # Extract index.html
                index_html_content = zip_file.read(index_html_path).decode('utf-8')
                
                # Extract other files
                other_files = {}
                for file_path in zip_file.namelist():
                    if file_path != index_html_path and not file_path.endswith('/'):
                        try:
                            other_files[file_path] = zip_file.read(file_path)
                        except Exception as e:
                            logger.warning(f"Failed to extract {file_path}: {e}")
                
                extracted_data = {
                    'index_html_content': index_html_content,
                    'other_files': other_files,
                    'file_count': len(zip_file.namelist())
                }
                
                return True, "ZIP文件提取成功", extracted_data
                
        except Exception as e:
            logger.error(f"ZIP extraction error: {str(e)}")
            return False, f"ZIP文件提取失败: {str(e)}", None
    
    @staticmethod
    def _extract_html_game(file_content: bytes) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Extract HTML game from single HTML file"""
        try:
            index_html_content = file_content.decode('utf-8')
            
            extracted_data = {
                'index_html_content': index_html_content,
                'other_files': {},
                'file_count': 1
            }
            
            return True, "HTML文件提取成功", extracted_data
            
        except Exception as e:
            logger.error(f"HTML extraction error: {str(e)}")
            return False, f"HTML文件提取失败: {str(e)}", None
    @staticmethod
    def _validate_js_file(file_content: bytes, filename: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate JavaScript file"""
        try:
            # Decode content
            try:
                content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                return False, "JavaScript文件编码错误，请使用UTF-8编码", None
            
            # Basic validation
            if len(content.strip()) == 0:
                return False, "JavaScript文件内容为空", None
            
            # Security check
            security_issues = HTMLGameValidator._check_js_security(content)
            
            # 基础metadata
            metadata = {
                'file_type': 'javascript',
                'file_size': len(file_content),
                'line_count': len(content.split('\n')),
                'file_count': 1,
                'total_size': len(file_content)
            }
            
            if security_issues:
                metadata['security_issues'] = security_issues
                return False, "JavaScript文件包含安全风险", metadata
            
            # Validation passed
            metadata['security_issues'] = []
            
            return True, "JavaScript文件验证通过", metadata
            
        except Exception as e:
            logger.error(f"JavaScript validation error: {str(e)}")
            return False, f"JavaScript文件验证失败: {str(e)}", None
    
    @staticmethod
    def _check_js_security(content: str) -> List[Dict[str, Any]]:
        """Check JavaScript content for security issues"""
        security_issues = []
        lines = content.split('\n')
        
        # Define security patterns and their severity
        security_patterns = [
            {
                'pattern': 'require("fs")',
                'severity': 'high',
                'message': '检测到文件系统访问：require("fs")',
                'type': 'fs_access'
            },
            {
                'pattern': 'require(\'fs\')',
                'severity': 'high', 
                'message': '检测到文件系统访问：require(\'fs\')',
                'type': 'fs_access'
            },
            {
                'pattern': 'require("child_process")',
                'severity': 'high',
                'message': '检测到子进程执行：require("child_process")',
                'type': 'child_process'
            },
            {
                'pattern': 'require(\'child_process\')',
                'severity': 'high',
                'message': '检测到子进程执行：require(\'child_process\')',
                'type': 'child_process'
            },
            {
                'pattern': 'eval(',
                'severity': 'high',
                'message': '检测到eval函数调用，存在代码注入风险',
                'type': 'eval'
            },
            {
                'pattern': 'new Function(',
                'severity': 'high',
                'message': '检测到Function构造函数，存在代码注入风险',
                'type': 'function_constructor'
            },
            {
                'pattern': 'Function("',
                'severity': 'high',
                'message': '检测到Function构造函数，存在代码注入风险',
                'type': 'function_constructor'
            },
            {
                'pattern': "Function('",
                'severity': 'high',
                'message': '检测到Function构造函数，存在代码注入风险',
                'type': 'function_constructor'
            },
            {
                'pattern': 'process.exit',
                'severity': 'medium',
                'message': '检测到进程退出调用：process.exit',
                'type': 'process_exit'
            },
            {
                'pattern': 'process.kill',
                'severity': 'high',
                'message': '检测到进程终止调用：process.kill',
                'type': 'process_kill'
            },
            {
                'pattern': 'fs.readFile',
                'severity': 'high',
                'message': '检测到文件系统读取操作',
                'type': 'fs_access'
            },
            {
                'pattern': 'fs.writeFile',
                'severity': 'high',
                'message': '检测到文件系统写入操作',
                'type': 'fs_access'
            },
            {
                'pattern': 'exec(',
                'severity': 'high',
                'message': '检测到命令执行：exec',
                'type': 'command_execution'
            },
            {
                'pattern': 'spawn(',
                'severity': 'high',
                'message': '检测到进程生成：spawn',
                'type': 'process_spawn'
            }
        ]
        
        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower().strip()
            
            for pattern_info in security_patterns:
                if pattern_info['pattern'].lower() in line_lower:
                    security_issues.append({
                        'severity': pattern_info['severity'],
                        'message': pattern_info['message'],
                        'line': line_num,
                        'code_snippet': line.strip(),
                        'type': pattern_info['type']
                    })
        
        return security_issues
    
    @staticmethod
    def _extract_js_game(file_content: bytes) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Extract JavaScript game file"""
        try:
            js_content = file_content.decode('utf-8')
            
            extracted_data = {
                'js_content': js_content,
                'other_files': {},
                'file_count': 1,
                'file_type': 'javascript'
            }
            
            return True, "JavaScript文件提取成功", extracted_data
            
        except Exception as e:
            logger.error(f"JavaScript extraction error: {str(e)}")
            return False, f"JavaScript文件提取失败: {str(e)}", None
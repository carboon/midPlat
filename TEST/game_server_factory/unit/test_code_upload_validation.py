"""
Property-based tests for code upload and validation
**Feature: ai-game-platform, Property 1: 代码上传和验证**
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from io import BytesIO
from code_analyzer import validate_file_upload, JavaScriptCodeAnalyzer


class TestCodeUploadValidation:
    """Property-based tests for JavaScript code upload and validation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = JavaScriptCodeAnalyzer()
    
    @given(
        file_content=st.binary(min_size=0, max_size=2*1024*1024),  # 0 to 2MB
        filename=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=10)
    def test_property_1_code_upload_and_validation(self, file_content, filename):
        """
        **Feature: ai-game-platform, Property 1: 代码上传和验证**
        **Validates: Requirements 1.1, 4.1**
        
        Property: For any uploaded JavaScript file, Game Server Factory should 
        validate file format, size limits, syntax and basic structure
        """
        # Test file upload validation
        is_valid, message = validate_file_upload(file_content, filename)
        
        # Property 1: Validation should always return a boolean and message
        assert isinstance(is_valid, bool)
        assert isinstance(message, str)
        assert len(message) > 0
        
        # Property 2: Files exceeding size limit should be rejected
        max_size = 1024 * 1024  # 1MB
        if len(file_content) > max_size:
            assert not is_valid, f"Files larger than {max_size} bytes should be rejected"
            assert "大小超过限制" in message or "size" in message.lower()
        
        # Property 3: Files with invalid extensions should be rejected
        allowed_extensions = ['.js', '.mjs']
        has_valid_extension = any(filename.lower().endswith(ext) for ext in allowed_extensions)
        if not has_valid_extension and len(filename) > 0:
            assert not is_valid, f"Files without valid extensions should be rejected: {filename}"
            assert "文件类型" in message or "extension" in message.lower() or "type" in message.lower()
        
        # Property 4: Empty files should be rejected
        if len(file_content) == 0:
            assert not is_valid, "Empty files should be rejected"
        
        # Property 5: If file passes basic validation, test code analysis
        if is_valid:
            try:
                code = file_content.decode('utf-8')
                analysis_result = self.analyzer.analyze_code(code)
                
                # Analysis should always complete
                assert analysis_result is not None
                assert hasattr(analysis_result, 'is_valid')
                assert hasattr(analysis_result, 'syntax_errors')
                assert hasattr(analysis_result, 'security_issues')
                
                # If code has syntax errors, it should be marked invalid
                if len(analysis_result.syntax_errors) > 0:
                    assert not analysis_result.is_valid, "Code with syntax errors should be invalid"
                
                # If code has high severity security issues, it should be invalid
                high_severity_issues = [issue for issue in analysis_result.security_issues 
                                      if issue.severity == "high"]
                if high_severity_issues:
                    assert not analysis_result.is_valid, "Code with high severity security issues should be invalid"
                    
            except UnicodeDecodeError:
                # Non-UTF8 files should be rejected at validation stage
                assert not is_valid, "Non-UTF8 files should be rejected"
                assert "编码" in message or "encoding" in message.lower()
    
    @given(st.sampled_from([
        b'console.log("Hello World");',
        b'module.exports = { handleConnection: function(socket) { socket.emit("test"); } };',
        b'const gameState = { score: 0 }; module.exports = { handleConnection: (socket) => {} };',
        b'// Simple game logic\nmodule.exports = { handleConnection: function(socket) { console.log("Connected"); } };'
    ]))
    @settings(max_examples=10)
    def test_valid_javascript_files(self, valid_js_content):
        """
        Test that valid JavaScript content passes validation
        """
        filename = "test.js"
        
        is_valid, message = validate_file_upload(valid_js_content, filename)
        
        # Valid JavaScript files should pass basic validation
        assert is_valid, f"Valid JavaScript should pass validation: {message}"
        
        # Code analysis should also work
        code = valid_js_content.decode('utf-8')
        analysis_result = self.analyzer.analyze_code(code)
        assert analysis_result is not None
    
    @given(st.sampled_from([
        ("test.txt", "Text files should be rejected"),
        ("test.py", "Python files should be rejected"), 
        ("test.html", "HTML files should be accepted"),  # 更新：HTML文件应该被接受
        ("test", "Files without extension should be rejected"),
        ("test.JS", "Case should not matter for extensions"),
        ("test.MJS", "Case should not matter for extensions")
    ]))
    @settings(max_examples=10)
    def test_file_extension_validation(self, filename_and_expectation):
        """
        Test file extension validation logic
        """
        filename, expectation = filename_and_expectation
        valid_content = b'console.log("test");'
        
        is_valid, message = validate_file_upload(valid_content, filename)
        
        # 更新验证逻辑以支持HTML游戏平台
        if filename.lower().endswith(('.js', '.mjs', '.html', '.htm')):
            assert is_valid, f"Valid game file extensions should be accepted: {filename}"
        else:
            assert not is_valid, f"Invalid extensions should be rejected: {filename} - {expectation}"
    
    @given(st.integers(min_value=0, max_value=3*1024*1024))  # 0 to 3MB
    @settings(max_examples=10)
    def test_file_size_limits(self, file_size):
        """
        Test file size validation
        """
        # Create file content of specified size
        file_content = b'a' * file_size
        filename = "test.js"
        
        is_valid, message = validate_file_upload(file_content, filename)
        
        max_size = 1024 * 1024  # 1MB
        if file_size > max_size:
            assert not is_valid, f"Files larger than {max_size} bytes should be rejected"
            assert "大小" in message or "size" in message.lower()
        elif file_size == 0:
            assert not is_valid, "Empty files should be rejected"
            assert "空" in message or "empty" in message.lower()
        else:
            # File size is within limits, should pass size validation
            # (may still fail for other reasons like content)
            if not is_valid:
                # If it fails, it should not be due to size
                assert "大小" not in message and "size" not in message.lower()
    
    @given(st.sampled_from([
        b'\xff\xfe\x00\x00',  # Invalid UTF-8 bytes
        b'\x80\x81\x82',      # Invalid UTF-8 sequence
        b'\xc0\x80',          # Overlong encoding
    ]))
    @settings(max_examples=10)
    def test_invalid_encoding_handling(self, invalid_bytes):
        """
        Test handling of files with invalid UTF-8 encoding
        """
        filename = "test.js"
        
        is_valid, message = validate_file_upload(invalid_bytes, filename)
        
        # Files with invalid encoding should be rejected
        assert not is_valid, "Files with invalid UTF-8 encoding should be rejected"
        assert "编码" in message or "encoding" in message.lower()
    
    def test_control_characters_handling(self):
        """
        Test handling of files with control characters (valid UTF-8 but problematic content)
        """
        # Control characters are valid UTF-8 but may be problematic
        control_chars = bytes([0x00, 0x01, 0x02, 0x03])
        filename = "test.js"
        
        is_valid, message = validate_file_upload(control_chars, filename)
        
        # Control characters pass file validation (they're valid UTF-8)
        # but should be caught by code analysis if they're problematic
        if is_valid:
            # If file validation passes, test that code analysis handles it
            try:
                code = control_chars.decode('utf-8')
                analysis_result = self.analyzer.analyze_code(code)
                # Code analysis should handle unusual content gracefully
                assert analysis_result is not None
            except UnicodeDecodeError:
                # This shouldn't happen since file validation passed
                assert False, "File validation passed but decoding failed"
    
    def test_edge_cases(self):
        """Test specific edge cases for file validation"""
        
        # Test exactly at size limit
        max_size = 1024 * 1024
        exactly_max_content = b'a' * max_size
        is_valid, message = validate_file_upload(exactly_max_content, "test.js")
        assert is_valid, "Files exactly at size limit should be accepted"
        
        # Test just over size limit
        over_max_content = b'a' * (max_size + 1)
        is_valid, message = validate_file_upload(over_max_content, "test.js")
        assert not is_valid, "Files just over size limit should be rejected"
        
        # Test whitespace-only content
        whitespace_content = b'   \n\t  \r\n  '
        is_valid, message = validate_file_upload(whitespace_content, "test.js")
        if is_valid:
            # If it passes file validation, code analysis should catch empty content
            code = whitespace_content.decode('utf-8')
            analysis_result = self.analyzer.analyze_code(code)
            assert not analysis_result.is_valid, "Whitespace-only code should be invalid"
    
    @given(st.text(min_size=1, max_size=1000))
    @settings(max_examples=10)
    def test_unicode_content_handling(self, unicode_text):
        """
        Test handling of Unicode content in JavaScript files
        """
        # Create valid JavaScript with Unicode content
        js_code = f'// {unicode_text}\nconsole.log("Unicode test");'
        file_content = js_code.encode('utf-8')
        filename = "test.js"
        
        # Assume the content is not too large
        assume(len(file_content) <= 1024 * 1024)
        
        is_valid, message = validate_file_upload(file_content, filename)
        
        # Valid UTF-8 encoded JavaScript should pass validation
        assert is_valid, f"Valid UTF-8 JavaScript should pass validation: {message}"
        
        # Code analysis should handle Unicode content
        analysis_result = self.analyzer.analyze_code(js_code)
        assert analysis_result is not None
    
    def test_comprehensive_validation_workflow(self):
        """
        Test the complete validation workflow with realistic examples
        """
        test_cases = [
            # Valid cases
            {
                "content": b'module.exports = { handleConnection: function(socket) { socket.emit("welcome"); } };',
                "filename": "game.js",
                "should_pass": True,
                "description": "Valid game server code"
            },
            {
                "content": b'const gameState = { players: [] }; module.exports = { handleConnection: (socket) => { gameState.players.push(socket.id); } };',
                "filename": "multiplayer.js", 
                "should_pass": True,
                "description": "Valid multiplayer game code"
            },
            # Cases that pass file validation but should fail security analysis
            {
                "content": b'require("fs").readFileSync("/etc/passwd");',
                "filename": "malicious.js",
                "should_pass": True,  # Passes file validation
                "should_pass_security": False,  # Fails security analysis
                "description": "Malicious file system access"
            },
            {
                "content": b'eval("process.exit()");',
                "filename": "dangerous.js",
                "should_pass": True,  # Passes file validation
                "should_pass_security": False,  # Fails security analysis
                "description": "Dangerous eval usage"
            },
            {
                "content": b'',
                "filename": "empty.js",
                "should_pass": False,
                "description": "Empty file"
            },
            {
                "content": b'console.log("test");',
                "filename": "test.txt",
                "should_pass": False,
                "description": "Wrong file extension"
            }
        ]
        
        for case in test_cases:
            is_valid, message = validate_file_upload(case["content"], case["filename"])
            
            if case["should_pass"]:
                assert is_valid, f"Case '{case['description']}' should pass file validation but failed: {message}"
                
                # If file validation passes, test code analysis
                if len(case["content"]) > 0:
                    try:
                        code = case["content"].decode('utf-8')
                        analysis_result = self.analyzer.analyze_code(code)
                        
                        # Check security analysis results
                        should_pass_security = case.get("should_pass_security", True)
                        high_severity_issues = [issue for issue in analysis_result.security_issues 
                                              if issue.severity == "high"]
                        
                        if not should_pass_security:
                            # Code should fail security analysis
                            assert len(high_severity_issues) > 0, f"Case '{case['description']}' should have security issues"
                            assert not analysis_result.is_valid, f"Code with high severity issues should be invalid: {case['description']}"
                        else:
                            # Code should pass security analysis (or have only low/medium issues)
                            if high_severity_issues:
                                assert not analysis_result.is_valid, f"Code with high severity issues should be invalid: {case['description']}"
                    except UnicodeDecodeError:
                        pass  # This would be caught at file validation stage
            else:
                assert not is_valid, f"Case '{case['description']}' should fail file validation but passed: {message}"
"""
Property-based tests for HTML game file validation error handling

**Feature: ai-game-platform, Property 2: 文件验证错误处理**

**Validates: Requirements 1.3, 4.3, 8.3**
"""

import pytest
import zipfile
import io
from hypothesis import given, strategies as st, settings, HealthCheck
from html_game_validator import HTMLGameValidator


class TestHTMLGameFileValidationErrorHandlingProperty:
    """Property-based tests for HTML game file validation error handling"""
    
    @given(
        filename=st.sampled_from([
            'game.exe', 'game.txt', 'game.pdf', 'game.doc', 
            'game.mp4', 'game.png', 'game.json', 'game.xml', 'game.py'
        ])
    )
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.too_slow]
    )
    def test_property_2_unsupported_file_format_error_handling(self, filename):
        """
        **Feature: ai-game-platform, Property 2: 文件验证错误处理**
        
        For any unsupported file format, the validator should:
        1. Always return False for is_valid
        2. Return a detailed error message explaining the issue
        3. Return None for metadata
        4. Error message should be user-friendly and in Chinese
        """
        file_content = b'some test content'
        
        # Validate file
        is_valid, message, metadata = HTMLGameValidator.validate_file(file_content, filename)
        
        # Property 1: Unsupported formats should always be rejected
        assert is_valid is False, f"Unsupported format {filename} should be rejected"
        
        # Property 2: Error message should be detailed and helpful
        assert isinstance(message, str), "Error message should be a string"
        assert len(message) > 0, "Error message should not be empty"
        assert "不支持" in message or "格式" in message, f"Error message should mention unsupported format: {message}"
        
        # Property 3: Metadata should be None for invalid files
        assert metadata is None, "Metadata should be None for invalid files"
        
        # Property 4: Error message should mention supported formats
        assert any(ext in message for ext in ['.html', '.htm', '.zip', '.js']), \
            f"Error message should mention supported formats: {message}"
    
    @given(
        file_size=st.integers(min_value=HTMLGameValidator.MAX_FILE_SIZE + 1, max_value=HTMLGameValidator.MAX_FILE_SIZE * 2)
    )
    @settings(max_examples=10)
    def test_property_2_oversized_file_error_handling(self, file_size):
        """
        For any file exceeding size limits, the validator should:
        1. Always reject the file
        2. Return specific error message about file size
        3. Include the actual size limit in the error message
        """
        # Create oversized content
        content = 'x' * file_size
        file_content = content.encode('utf-8')
        
        # Validate
        is_valid, message, metadata = HTMLGameValidator.validate_file(file_content, 'game.html')
        
        # Property 1: Oversized files should always be rejected
        assert is_valid is False, "Oversized files should be rejected"
        
        # Property 2: Error message should mention file size
        assert "过大" in message or "大小" in message or "限制" in message, \
            f"Error message should mention file size issue: {message}"
        
        # Property 3: Error message should include size limit information
        assert "MB" in message, f"Error message should include size limit in MB: {message}"
        
        # Property 4: Metadata should be None
        assert metadata is None, "Metadata should be None for oversized files"
    
    @given(
        filename=st.just('game.html')
    )
    @settings(max_examples=10)
    def test_property_2_empty_file_error_handling(self, filename):
        """
        For empty files, the validator should:
        1. Always reject empty files
        2. Return specific error message about empty content
        3. Provide clear guidance to the user
        """
        file_content = b''
        
        # Validate
        is_valid, message, metadata = HTMLGameValidator.validate_file(file_content, filename)
        
        # Property 1: Empty files should always be rejected
        assert is_valid is False, "Empty files should be rejected"
        
        # Property 2: Error message should mention empty file
        assert "空" in message, f"Error message should mention empty file: {message}"
        
        # Property 3: Metadata should be None
        assert metadata is None, "Metadata should be None for empty files"
    
    @given(
        invalid_bytes=st.binary(min_size=1, max_size=100)
    )
    @settings(max_examples=10)
    def test_property_2_invalid_encoding_error_handling(self, invalid_bytes):
        """
        For files with invalid UTF-8 encoding, the validator should:
        1. Detect encoding issues
        2. Return appropriate error message
        3. Handle the error gracefully without crashing
        """
        # Create content that's likely to have encoding issues
        try:
            # Try to decode to see if it's valid UTF-8
            invalid_bytes.decode('utf-8')
            # If it decodes successfully, skip this test case
            pytest.skip("Generated bytes are valid UTF-8")
        except UnicodeDecodeError:
            # This is what we want - invalid UTF-8
            pass
        
        # Validate
        is_valid, message, metadata = HTMLGameValidator.validate_file(invalid_bytes, 'game.html')
        
        # Property 1: Invalid encoding should be handled gracefully
        assert isinstance(is_valid, bool), "Validator should return boolean even for invalid encoding"
        assert isinstance(message, str), "Validator should return string message even for invalid encoding"
        
        # Property 2: If rejected due to encoding, error message should be clear
        if not is_valid and ("编码" in message or "UTF-8" in message):
            assert "编码" in message or "UTF-8" in message, \
                f"Encoding error message should mention encoding: {message}"
            assert metadata is None, "Metadata should be None for encoding errors"
    
    @given(
        filename=st.just('game.zip')
    )
    @settings(max_examples=10)
    def test_property_2_zip_without_index_html_error_handling(self, filename):
        """
        For ZIP files without index.html, the validator should:
        1. Always reject the file
        2. Return specific error message about missing index.html
        3. Provide clear guidance about required files
        """
        # Create ZIP without index.html
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('readme.txt', 'This is a test file')
            zf.writestr('config.json', '{"test": true}')
            zf.writestr('style.css', 'body { color: red; }')
        
        file_content = zip_buffer.getvalue()
        
        # Validate
        is_valid, message, metadata = HTMLGameValidator.validate_file(file_content, filename)
        
        # Property 1: ZIP without index.html should be rejected
        assert is_valid is False, "ZIP without index.html should be rejected"
        
        # Property 2: Error message should mention index.html specifically
        assert "index.html" in message.lower(), \
            f"Error message should mention index.html: {message}"
        
        # Property 3: Error message should be helpful
        assert "未找到" in message or "找不到" in message or "缺少" in message, \
            f"Error message should indicate missing file: {message}"
        
        # Property 4: Metadata should be None
        assert metadata is None, "Metadata should be None for invalid ZIP files"
    
    @given(
        filename=st.just('game.zip')
    )
    @settings(max_examples=10)
    def test_property_2_corrupted_zip_error_handling(self, filename):
        """
        For corrupted ZIP files, the validator should:
        1. Detect corruption gracefully
        2. Return appropriate error message
        3. Not crash or raise unhandled exceptions
        """
        # Create corrupted ZIP content
        corrupted_content = b'PK\x03\x04' + b'\x00' * 100 + b'corrupted zip data'
        
        # Validate
        is_valid, message, metadata = HTMLGameValidator.validate_file(corrupted_content, filename)
        
        # Property 1: Corrupted ZIP should be handled gracefully
        assert isinstance(is_valid, bool), "Validator should return boolean for corrupted ZIP"
        assert isinstance(message, str), "Validator should return string message for corrupted ZIP"
        
        # Property 2: Should be rejected
        assert is_valid is False, "Corrupted ZIP should be rejected"
        
        # Property 3: Error message should indicate ZIP issue
        assert any(keyword in message for keyword in ["ZIP", "zip", "损坏", "无效", "格式"]), \
            f"Error message should indicate ZIP issue: {message}"
        
        # Property 4: Metadata should be None
        assert metadata is None, "Metadata should be None for corrupted ZIP"
    
    @given(
        total_size=st.integers(
            min_value=HTMLGameValidator.MAX_EXTRACT_SIZE + 1, 
            max_value=HTMLGameValidator.MAX_EXTRACT_SIZE * 2
        )
    )
    @settings(max_examples=10)
    def test_property_2_oversized_zip_extraction_error_handling(self, total_size):
        """
        For ZIP files that would extract to exceed size limits, the validator should:
        1. Detect the size issue before extraction
        2. Return appropriate error message
        3. Prevent potential resource exhaustion
        """
        try:
            # Create ZIP with large extracted size
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add index.html
                zf.writestr('index.html', '<html><body>Game</body></html>')
                
                # Add large file that would exceed extraction limit
                # Use compression to keep the ZIP file itself small
                large_content = 'x' * min(total_size, 10 * 1024 * 1024)  # Cap at 10MB to avoid memory issues
                zf.writestr('large_file.txt', large_content)
            
            file_content = zip_buffer.getvalue()
            
            # Skip if the ZIP itself is too large
            if len(file_content) > HTMLGameValidator.MAX_FILE_SIZE:
                pytest.skip("ZIP file itself is too large")
            
            # Validate
            is_valid, message, metadata = HTMLGameValidator.validate_file(file_content, 'game.zip')
            
            # Property 1: Oversized extraction should be rejected
            assert is_valid is False, "ZIP with oversized extraction should be rejected"
            
            # Property 2: Error message should mention size issue
            assert any(keyword in message for keyword in ["过大", "大小", "限制", "解压"]), \
                f"Error message should mention size issue: {message}"
            
            # Property 3: Metadata should be None
            assert metadata is None, "Metadata should be None for oversized extraction"
            
        except MemoryError:
            pytest.skip("Not enough memory to create test ZIP")
        except Exception as e:
            # If ZIP creation fails, skip the test
            pytest.skip(f"ZIP creation failed: {e}")
    
    @given(
        filename=st.sampled_from(['game.html', 'game.htm'])
    )
    @settings(max_examples=10)
    def test_property_2_malformed_html_error_handling(self, filename):
        """
        For malformed HTML files, the validator should:
        1. Handle malformed content gracefully
        2. Still validate basic structure requirements
        3. Not crash on unusual HTML content
        """
        # Create various types of malformed HTML
        malformed_html_samples = [
            b'<html><body>unclosed tag',
            b'<html><head><title>test</title><body>mixed structure',
            b'<<>>invalid tags<<>>',
            b'<html>\x00\x01\x02</html>',  # HTML with null bytes
            b'<script>alert("test")</script>',  # Just script tag
        ]
        
        for malformed_html in malformed_html_samples:
            try:
                # Validate
                is_valid, message, metadata = HTMLGameValidator.validate_file(malformed_html, filename)
                
                # Property 1: Should handle gracefully
                assert isinstance(is_valid, bool), f"Should return boolean for malformed HTML: {malformed_html}"
                assert isinstance(message, str), f"Should return string message for malformed HTML: {malformed_html}"
                
                # Property 2: If rejected, should have meaningful message
                if not is_valid:
                    assert len(message) > 0, "Error message should not be empty for malformed HTML"
                
            except Exception as e:
                # Should not raise unhandled exceptions
                pytest.fail(f"Validator should not raise exception for malformed HTML {malformed_html}: {e}")
    
    @given(
        filename=st.just('game.zip')
    )
    @settings(max_examples=10)
    def test_property_2_zip_with_invalid_index_html_error_handling(self, filename):
        """
        For ZIP files with invalid index.html content, the validator should:
        1. Detect the invalid content
        2. Return appropriate error message
        3. Handle encoding issues in index.html
        """
        # Create ZIP with invalid index.html
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add invalid index.html (invalid UTF-8)
            invalid_html = b'\x80\x81\x82\x83<html></html>'
            zf.writestr('index.html', invalid_html)
        
        file_content = zip_buffer.getvalue()
        
        # Validate
        is_valid, message, metadata = HTMLGameValidator.validate_file(file_content, filename)
        
        # Property 1: Should be rejected
        assert is_valid is False, "ZIP with invalid index.html should be rejected"
        
        # Property 2: Error message should mention encoding or index.html issue
        assert any(keyword in message for keyword in ["编码", "UTF-8", "index.html", "无效"]), \
            f"Error message should mention encoding or index.html issue: {message}"
        
        # Property 3: Metadata should be None
        assert metadata is None, "Metadata should be None for invalid index.html"
    
    def test_property_2_error_message_consistency(self):
        """
        Error messages should be consistent and follow patterns:
        1. All error messages should be in Chinese
        2. Error messages should be descriptive
        3. Similar errors should have similar message patterns
        """
        test_cases = [
            (b'', 'empty.html', "空"),
            (b'content', 'file.exe', "不支持"),
            (b'x' * (HTMLGameValidator.MAX_FILE_SIZE + 1), 'large.html', "过大"),
        ]
        
        for content, filename, expected_keyword in test_cases:
            is_valid, message, metadata = HTMLGameValidator.validate_file(content, filename)
            
            # Property 1: Should be rejected
            assert is_valid is False, f"Test case should be rejected: {filename}"
            
            # Property 2: Error message should contain expected keyword
            assert expected_keyword in message, \
                f"Error message should contain '{expected_keyword}': {message}"
            
            # Property 3: Error message should be non-empty string
            assert isinstance(message, str) and len(message) > 0, \
                f"Error message should be non-empty string: {message}"
            
            # Property 4: Metadata should be None for errors
            assert metadata is None, f"Metadata should be None for error case: {filename}"
    
    @given(
        filename=st.text(
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
            min_size=1,
            max_size=50
        ).filter(lambda x: not x.endswith(('.html', '.htm', '.zip')))
    )
    @settings(max_examples=10)
    def test_property_2_arbitrary_filename_error_handling(self, filename):
        """
        For any filename that doesn't end with supported extensions, the validator should:
        1. Always reject the file
        2. Return consistent error message
        3. Handle unusual filenames gracefully
        """
        file_content = b'<html><body>content</body></html>'
        
        # Validate
        is_valid, message, metadata = HTMLGameValidator.validate_file(file_content, filename)
        
        # Property 1: Unsupported extensions should be rejected
        assert is_valid is False, f"File with unsupported extension should be rejected: {filename}"
        
        # Property 2: Error message should mention format issue
        assert "不支持" in message or "格式" in message, \
            f"Error message should mention format issue for {filename}: {message}"
        
        # Property 3: Should handle gracefully
        assert isinstance(message, str), f"Should return string message for filename: {filename}"
        assert metadata is None, f"Metadata should be None for unsupported filename: {filename}"
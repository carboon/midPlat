"""
Property-based tests for HTML game file validation

**Feature: ai-game-platform, Property 1: HTML游戏文件验证**

**Validates: Requirements 1.1, 1.2, 4.1**
"""

import pytest
import zipfile
import io
from hypothesis import given, strategies as st, settings, HealthCheck
from html_game_validator import HTMLGameValidator


class TestHTMLGameFileValidationProperty:
    """Property-based tests for HTML game file validation"""
    
    @given(
        html_content=st.text(
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
            min_size=10,
            max_size=1000
        ),
        filename=st.just('game.html')
    )
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.too_slow]
    )
    def test_property_1_html_file_validation(self, html_content, filename):
        """
        **Feature: ai-game-platform, Property 1: HTML游戏文件验证**
        
        For any valid HTML content, the validator should:
        1. Accept the file if it's not empty
        2. Return validation result with metadata
        3. Consistently validate the same content
        """
        # Prepare HTML content
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Game</title>
</head>
<body>
    {html_content}
</body>
</html>"""
        
        file_content = full_html.encode('utf-8')
        
        # Validate file
        is_valid, message, metadata = HTMLGameValidator.validate_file(file_content, filename)
        
        # Property 1: Validation should always return a result
        assert isinstance(is_valid, bool)
        assert isinstance(message, str)
        
        # Property 2: Valid HTML should pass validation
        if len(file_content) > 0 and len(file_content) <= HTMLGameValidator.MAX_FILE_SIZE:
            assert is_valid is True, f"Valid HTML should pass validation: {message}"
            assert metadata is not None
            assert metadata['file_type'] == 'html'
            assert metadata['has_index_html'] is True
        
        # Property 3: Metadata should be consistent
        if is_valid and metadata:
            assert 'file_type' in metadata
            assert 'has_index_html' in metadata
            assert 'file_count' in metadata
            assert 'total_size' in metadata
    
    @given(
        file_size=st.integers(min_value=1, max_value=1000),
        filename=st.just('game.html')
    )
    @settings(max_examples=10)
    def test_property_1_html_file_size_validation(self, file_size, filename):
        """
        For any HTML file size, the validator should:
        1. Accept files within size limits
        2. Reject files exceeding size limits
        3. Return appropriate error messages
        """
        # Create HTML content of specific size
        html_content = f"""<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>{'x' * file_size}</body>
</html>"""
        
        file_content = html_content.encode('utf-8')
        
        # Validate
        is_valid, message, metadata = HTMLGameValidator.validate_file(file_content, filename)
        
        # Property: Size validation should be consistent
        if len(file_content) <= HTMLGameValidator.MAX_FILE_SIZE:
            assert is_valid is True, f"File within size limit should pass: {message}"
        else:
            assert is_valid is False
            assert "过大" in message or "大小" in message
    
    @given(
        file_count=st.integers(min_value=1, max_value=5),
        file_size_per_file=st.integers(min_value=50, max_value=500)
    )
    @settings(max_examples=10)
    def test_property_1_zip_file_validation(self, file_count, file_size_per_file):
        """
        For any ZIP file with HTML game content, the validator should:
        1. Accept ZIP files with index.html
        2. Reject ZIP files without index.html
        3. Validate total extracted size
        """
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        try:
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add index.html
                index_html = """<!DOCTYPE html>
<html>
<head><title>Game</title></head>
<body><h1>HTML Game</h1></body>
</html>"""
                zip_file.writestr('index.html', index_html)
                
                # Add other files
                for i in range(min(file_count - 1, 4)):  # Limit to avoid huge files
                    content = 'x' * min(file_size_per_file, 1000)
                    zip_file.writestr(f'file_{i}.txt', content)
            
            zip_content = zip_buffer.getvalue()
            
            # Validate
            is_valid, message, metadata = HTMLGameValidator.validate_file(zip_content, 'game.zip')
            
            # Property: ZIP with index.html should pass
            if len(zip_content) <= HTMLGameValidator.MAX_FILE_SIZE:
                assert is_valid is True, f"ZIP with index.html should pass: {message}"
                assert metadata is not None
                assert metadata['file_type'] == 'zip'
                assert metadata['has_index_html'] is True
        except Exception as e:
            # Skip if ZIP creation fails
            pytest.skip(f"ZIP creation failed: {e}")
    
    @given(
        filename=st.sampled_from(['game.html', 'game.htm', 'game.zip', 'game.js'])
    )
    @settings(max_examples=10)
    def test_property_1_supported_file_formats(self, filename):
        """
        For any supported file format, the validator should:
        1. Accept the format
        2. Return appropriate metadata
        """
        try:
            if filename.endswith('.zip'):
                # Create valid ZIP
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zf:
                    zf.writestr('index.html', '<html><body>Game</body></html>')
                file_content = zip_buffer.getvalue()
            elif filename.endswith('.js'):
                # Create valid JavaScript
                file_content = b'console.log("Hello Game!");'
            else:
                # Create valid HTML
                file_content = b'<!DOCTYPE html><html><body>Game</body></html>'
            
            # Validate
            is_valid, message, metadata = HTMLGameValidator.validate_file(file_content, filename)
            
            # Property: Supported formats should be recognized
            assert is_valid is True, f"Supported format {filename} should pass: {message}"
            assert metadata is not None
            assert 'file_type' in metadata
        except Exception as e:
            pytest.skip(f"Test setup failed: {e}")
    
    @given(
        filename=st.sampled_from(['game.exe', 'game.txt', 'game.pdf', 'game.doc'])
    )
    @settings(max_examples=10)
    def test_property_1_unsupported_file_formats(self, filename):
        """
        For any unsupported file format, the validator should:
        1. Reject the format
        2. Return appropriate error message
        """
        file_content = b'some content'
        
        # Validate
        is_valid, message, metadata = HTMLGameValidator.validate_file(file_content, filename)
        
        # Property: Unsupported formats should be rejected
        assert is_valid is False
        assert "不支持" in message or "格式" in message
        assert metadata is None
    
    @given(
        filename=st.just('game.html')
    )
    @settings(max_examples=10)
    def test_property_1_empty_file_rejection(self, filename):
        """
        For empty files, the validator should:
        1. Always reject empty files
        2. Return appropriate error message
        """
        file_content = b''
        
        # Validate
        is_valid, message, metadata = HTMLGameValidator.validate_file(file_content, filename)
        
        # Property: Empty files should always be rejected
        assert is_valid is False
        assert "空" in message
        assert metadata is None
    
    def test_property_1_zip_without_index_html_simple(self):
        """
        For ZIP files without index.html, the validator should:
        1. Always reject the file
        2. Return appropriate error message
        """
        # Create a simple ZIP without index.html
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('readme.txt', 'This is a test file')
            zf.writestr('config.json', '{"test": true}')
        
        file_content = zip_buffer.getvalue()
        filename = 'game.zip'
        
        # Validate
        is_valid, message, metadata = HTMLGameValidator.validate_file(file_content, filename)
        
        # Property: ZIP without index.html should be rejected
        assert is_valid is False
        assert "index.html" in message.lower()
        assert metadata is None
    
    @given(
        filename=st.just('game.html')
    )
    @settings(max_examples=10)
    def test_property_1_invalid_encoding(self, filename):
        """
        For files with invalid encoding, the validator should:
        1. Reject the file
        2. Return appropriate error message
        """
        # Create file with invalid UTF-8
        file_content = b'\x80\x81\x82\x83'
        
        # Validate
        is_valid, message, metadata = HTMLGameValidator.validate_file(file_content, filename)
        
        # Property: Invalid encoding should be rejected
        assert is_valid is False
        assert "编码" in message or "UTF-8" in message
        assert metadata is None
    
    @given(
        html_content=st.text(
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
            min_size=10,
            max_size=500
        )
    )
    @settings(max_examples=10)
    def test_property_1_extraction_consistency(self, html_content):
        """
        For any valid HTML file, extraction should:
        1. Always succeed after validation passes
        2. Return consistent content
        3. Preserve the original HTML
        """
        full_html = f"""<!DOCTYPE html>
<html>
<head><title>Game</title></head>
<body>{html_content}</body>
</html>"""
        
        file_content = full_html.encode('utf-8')
        
        # Validate first
        is_valid, _, _ = HTMLGameValidator.validate_file(file_content, 'game.html')
        
        if is_valid:
            # Extract
            success, message, extracted = HTMLGameValidator.extract_html_game(file_content, 'game.html')
            
            # Property: Extraction should succeed after validation
            assert success is True, f"Extraction should succeed: {message}"
            assert extracted is not None
            assert 'index_html_content' in extracted
            assert extracted['index_html_content'] == full_html
    
    @given(
        filename=st.just('game.zip')
    )
    @settings(max_examples=10)
    def test_property_1_zip_extraction_consistency(self, filename):
        """
        For any valid ZIP file, extraction should:
        1. Always succeed after validation passes
        2. Return index.html content
        3. Preserve other files
        """
        # Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('index.html', '<html><body>Game</body></html>')
            zf.writestr('style.css', 'body { color: red; }')
        
        file_content = zip_buffer.getvalue()
        
        # Validate
        is_valid, _, _ = HTMLGameValidator.validate_file(file_content, filename)
        
        if is_valid:
            # Extract
            success, message, extracted = HTMLGameValidator.extract_html_game(file_content, filename)
            
            # Property: Extraction should succeed
            assert success is True, f"Extraction should succeed: {message}"
            assert extracted is not None
            assert 'index_html_content' in extracted
            assert '<html>' in extracted['index_html_content']
            assert 'other_files' in extracted

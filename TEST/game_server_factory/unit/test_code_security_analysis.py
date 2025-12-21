"""
Property-based tests for code security analysis
**Feature: ai-game-platform, Property 2: 代码安全分析**
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from code_analyzer import JavaScriptCodeAnalyzer, SecurityIssue


class TestCodeSecurityAnalysis:
    """Property-based tests for JavaScript code security analysis"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = JavaScriptCodeAnalyzer()
    
    @given(st.text())
    @settings(max_examples=10)
    def test_property_2_code_security_analysis(self, code):
        """
        **Feature: ai-game-platform, Property 2: 代码安全分析**
        **Validates: Requirements 1.2, 4.2, 4.3**
        
        Property: For any JavaScript code, Game Server Factory should scan 
        potential malicious operations and reject code when security risks are found
        """
        # Analyze the code
        result = self.analyzer.analyze_code(code)
        
        # Property 1: Security analysis should always complete without crashing
        assert result is not None
        assert hasattr(result, 'security_issues')
        assert hasattr(result, 'is_valid')
        
        # Property 2: High severity security issues should make code invalid
        high_severity_issues = [issue for issue in result.security_issues 
                              if issue.severity == "high"]
        if high_severity_issues:
            assert not result.is_valid, f"Code with high severity issues should be invalid: {high_severity_issues}"
        
        # Property 3: All security issues should have required fields
        for issue in result.security_issues:
            assert isinstance(issue, SecurityIssue)
            assert issue.severity in ["high", "medium", "low"]
            assert isinstance(issue.message, str)
            assert len(issue.message) > 0
            assert isinstance(issue.line, int)
            assert issue.line > 0
            assert isinstance(issue.code_snippet, str)
    
    @given(st.sampled_from([
        'require("fs")',
        'require("child_process")',
        'eval("malicious code")',
        'Function("return process")()',
        'require("http")',
        'require("https")',
        'process.exit()',
        'global.something = "bad"'
    ]))
    @settings(max_examples=10)
    def test_dangerous_patterns_detected(self, dangerous_code):
        """
        Test that known dangerous patterns are always detected
        """
        # Create a minimal valid JavaScript structure with dangerous code
        full_code = f"""
        module.exports = {{
            handleConnection: function(socket) {{
                {dangerous_code};
                socket.emit('test');
            }}
        }};
        """
        
        result = self.analyzer.analyze_code(full_code)
        
        # Should detect security issues
        assert len(result.security_issues) > 0, f"Should detect security issue in: {dangerous_code}"
        
        # Should find the specific dangerous pattern
        found_issue = any(dangerous_code.split('(')[0] in issue.code_snippet or 
                         dangerous_code.split('(')[0] in issue.message.lower()
                         for issue in result.security_issues)
        assert found_issue, f"Should specifically detect pattern: {dangerous_code}"
    
    @given(st.sampled_from([
        '''
        module.exports = {
            handleConnection: function(socket) {
                socket.emit('welcome', 'Hello player!');
                socket.on('click', function() {
                    console.log('Player clicked');
                });
            }
        };
        ''',
        '''
        const gameState = { score: 0 };
        module.exports = {
            handleConnection: function(socket) {
                socket.emit('gameState', gameState);
            }
        };
        ''',
        '''
        module.exports = {
            handleConnection: function(socket) {
                let playerCount = 0;
                socket.on('join', () => playerCount++);
                socket.on('leave', () => playerCount--);
            }
        };
        '''
    ]))
    @settings(max_examples=10)
    def test_safe_code_patterns(self, safe_code):
        """
        Test that safe code patterns don't trigger false positives
        """
        result = self.analyzer.analyze_code(safe_code)
        
        # Safe code should not have high severity issues
        high_severity_issues = [issue for issue in result.security_issues 
                              if issue.severity == "high"]
        assert len(high_severity_issues) == 0, f"Safe code should not have high severity issues: {high_severity_issues}"
    
    def test_empty_code_handling(self):
        """Test handling of empty or whitespace-only code"""
        test_cases = ["", "   ", "\n\n\t  \n", "\r\n"]
        
        for empty_code in test_cases:
            result = self.analyzer.analyze_code(empty_code)
            assert result is not None
            # Empty code should have syntax errors but analysis should not crash
            assert len(result.syntax_errors) > 0 or not result.is_valid
    
    def test_malformed_code_handling(self):
        """Test handling of malformed JavaScript code"""
        malformed_codes = [
            "function unclosed() { console.log('test');",  # Unclosed brace
            "if (true { console.log('test'); }",  # Missing parenthesis
            "const x = ;",  # Invalid syntax
            "function() { return 'anonymous'; }",  # Anonymous function without assignment
        ]
        
        for malformed_code in malformed_codes:
            result = self.analyzer.analyze_code(malformed_code)
            assert result is not None
            # Malformed code should either have syntax errors or be marked invalid
            assert len(result.syntax_errors) > 0 or not result.is_valid
    
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=10)
    def test_multiple_security_issues_detection(self, num_issues):
        """
        Test that multiple security issues in the same code are all detected
        """
        dangerous_patterns = [
            'require("fs")',
            'eval("code")',
            'require("child_process")',
            'process.exit()',
            'global.hack = true',
            'require("http")',
            'Function("return this")()',
            'require("net")',
            'Buffer.from("data")',
            'process.env.SECRET'
        ]
        
        # Select a subset of dangerous patterns
        selected_patterns = dangerous_patterns[:min(num_issues, len(dangerous_patterns))]
        
        # Create code with multiple security issues
        code_lines = ['module.exports = {', '  handleConnection: function(socket) {']
        for i, pattern in enumerate(selected_patterns):
            code_lines.append(f'    {pattern}; // Issue {i+1}')
        code_lines.extend(['  }', '};'])
        
        full_code = '\n'.join(code_lines)
        result = self.analyzer.analyze_code(full_code)
        
        # Should detect at least as many issues as we inserted
        assert len(result.security_issues) >= len(selected_patterns), \
            f"Should detect at least {len(selected_patterns)} issues, found {len(result.security_issues)}"
        
        # Code with multiple high-severity issues should be invalid
        high_severity_count = sum(1 for issue in result.security_issues if issue.severity == "high")
        if high_severity_count > 0:
            assert not result.is_valid, "Code with high severity issues should be invalid"
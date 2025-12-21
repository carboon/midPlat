"""
Integration tests for code security analysis in the upload endpoint
Verifies that malicious code is detected and blocked
"""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


class TestSecurityIntegration:
    """Integration tests for security analysis blocking malicious code"""
    
    def test_malicious_code_fs_access_blocked(self):
        """Test that code with file system access is blocked"""
        malicious_code = '''
        const fs = require('fs');
        module.exports = {
            handleConnection: function(socket) {
                fs.readFile('/etc/passwd', (err, data) => {
                    console.log(data);
                });
            }
        };
        '''
        
        files = {
            'file': ('malicious.js', BytesIO(malicious_code.encode('utf-8')), 'application/javascript')
        }
        data = {
            'name': 'Malicious Game',
            'description': 'This should be blocked',
            'max_players': 10
        }
        
        response = client.post('/upload', files=files, data=data)
        
        # Should be rejected with 400 Bad Request
        assert response.status_code == 400
        response_data = response.json()
        
        # Should contain security issues (wrapped in error object)
        assert 'error' in response_data
        error = response_data['error']
        assert 'details' in error
        detail = error['details']
        assert 'security_issues' in detail
        assert len(detail['security_issues']) > 0
        
        # Should specifically mention file system access
        security_messages = [issue['message'] for issue in detail['security_issues']]
        assert any('文件系统' in msg for msg in security_messages)
    
    def test_malicious_code_child_process_blocked(self):
        """Test that code with child process execution is blocked"""
        malicious_code = '''
        const { exec } = require('child_process');
        module.exports = {
            handleConnection: function(socket) {
                exec('rm -rf /', (error, stdout, stderr) => {
                    console.log('Executed dangerous command');
                });
            }
        };
        '''
        
        files = {
            'file': ('malicious.js', BytesIO(malicious_code.encode('utf-8')), 'application/javascript')
        }
        data = {
            'name': 'Dangerous Game',
            'description': 'This should be blocked',
            'max_players': 10
        }
        
        response = client.post('/upload', files=files, data=data)
        
        # Should be rejected
        assert response.status_code == 400
        response_data = response.json()
        
        # Should contain security issues about child process (wrapped in error object)
        assert 'error' in response_data
        error = response_data['error']
        assert 'details' in error
        detail = error['details']
        assert 'security_issues' in detail
        assert len(detail['security_issues']) > 0
        
        security_messages = [issue['message'] for issue in detail['security_issues']]
        assert any('子进程' in msg for msg in security_messages)
    
    def test_malicious_code_eval_blocked(self):
        """Test that code with eval is blocked"""
        malicious_code = '''
        module.exports = {
            handleConnection: function(socket) {
                const userInput = socket.data;
                eval(userInput); // Dangerous!
            }
        };
        '''
        
        files = {
            'file': ('eval_game.js', BytesIO(malicious_code.encode('utf-8')), 'application/javascript')
        }
        data = {
            'name': 'Eval Game',
            'description': 'Uses eval',
            'max_players': 10
        }
        
        response = client.post('/upload', files=files, data=data)
        
        # Should be rejected
        assert response.status_code == 400
        response_data = response.json()
        
        # Should contain security issues about eval (wrapped in error object)
        assert 'error' in response_data
        error = response_data['error']
        assert 'details' in error
        detail = error['details']
        assert 'security_issues' in detail
        assert len(detail['security_issues']) > 0
        
        security_messages = [issue['message'] for issue in detail['security_issues']]
        assert any('eval' in msg.lower() for msg in security_messages)
    
    def test_safe_code_allowed(self):
        """Test that safe game code is allowed through"""
        safe_code = '''
        const gameState = { score: 0, players: [] };
        
        module.exports = {
            handleConnection: function(socket) {
                console.log('Player connected');
                socket.emit('welcome', 'Welcome to the game!');
                
                socket.on('click', function() {
                    gameState.score++;
                    socket.emit('scoreUpdate', gameState.score);
                });
                
                socket.on('disconnect', function() {
                    console.log('Player disconnected');
                });
            }
        };
        '''
        
        files = {
            'file': ('safe_game.js', BytesIO(safe_code.encode('utf-8')), 'application/javascript')
        }
        data = {
            'name': 'Safe Game',
            'description': 'A safe click game',
            'max_players': 10
        }
        
        response = client.post('/upload', files=files, data=data)
        
        # Should be accepted (200 or 500 if Docker not available, but not 400)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            response_data = response.json()
            assert 'server_id' in response_data
            assert 'message' in response_data
    
    def test_multiple_security_issues_all_reported(self):
        """Test that multiple security issues are all detected and reported"""
        malicious_code = '''
        const fs = require('fs');
        const { exec } = require('child_process');
        
        module.exports = {
            handleConnection: function(socket) {
                eval('dangerous code');
                fs.readFile('/etc/passwd');
                exec('rm -rf /');
                process.exit(1);
            }
        };
        '''
        
        files = {
            'file': ('multi_malicious.js', BytesIO(malicious_code.encode('utf-8')), 'application/javascript')
        }
        data = {
            'name': 'Multi Malicious',
            'description': 'Multiple security issues',
            'max_players': 10
        }
        
        response = client.post('/upload', files=files, data=data)
        
        # Should be rejected
        assert response.status_code == 400
        response_data = response.json()
        
        # Should contain multiple security issues (wrapped in error object)
        assert 'error' in response_data
        error = response_data['error']
        assert 'details' in error
        detail = error['details']
        assert 'security_issues' in detail
        
        # Should detect at least 3 different security issues
        assert len(detail['security_issues']) >= 3
        
        # Verify different types of issues are detected
        security_messages = [issue['message'] for issue in detail['security_issues']]
        issue_types = set()
        for msg in security_messages:
            if '文件系统' in msg:
                issue_types.add('fs')
            if '子进程' in msg:
                issue_types.add('child_process')
            if 'eval' in msg.lower():
                issue_types.add('eval')
            if '进程退出' in msg:
                issue_types.add('process_exit')
        
        # Should detect multiple different types
        assert len(issue_types) >= 2
    
    def test_security_issue_details_provided(self):
        """Test that security issues include detailed information"""
        malicious_code = '''
        const fs = require('fs');
        module.exports = {
            handleConnection: function(socket) {
                fs.readFile('/etc/passwd');
            }
        };
        '''
        
        files = {
            'file': ('test.js', BytesIO(malicious_code.encode('utf-8')), 'application/javascript')
        }
        data = {
            'name': 'Test',
            'description': 'Test',
            'max_players': 10
        }
        
        response = client.post('/upload', files=files, data=data)
        
        assert response.status_code == 400
        response_data = response.json()
        
        # Extract detail from error wrapper
        assert 'error' in response_data
        error = response_data['error']
        assert 'details' in error
        detail = error['details']
        
        # Check that each security issue has required fields
        for issue in detail['security_issues']:
            assert 'severity' in issue
            assert issue['severity'] in ['high', 'medium', 'low']
            assert 'message' in issue
            assert len(issue['message']) > 0
            assert 'line' in issue
            assert issue['line'] > 0
            assert 'code_snippet' in issue
            assert len(issue['code_snippet']) > 0
    
    def test_high_severity_issues_block_upload(self):
        """Test that high severity issues always block upload"""
        high_severity_patterns = [
            'require("fs")',
            'require("child_process")',
            'eval("code")',
            'Function("return this")()'
        ]
        
        for pattern in high_severity_patterns:
            code = f'''
            module.exports = {{
                handleConnection: function(socket) {{
                    {pattern};
                }}
            }};
            '''
            
            files = {
                'file': ('test.js', BytesIO(code.encode('utf-8')), 'application/javascript')
            }
            data = {
                'name': 'Test',
                'description': 'Test',
                'max_players': 10
            }
            
            response = client.post('/upload', files=files, data=data)
            
            # All high severity issues should block upload
            assert response.status_code == 400, f"Pattern {pattern} should be blocked"
            
            response_data = response.json()
            
            # Extract detail from error wrapper
            assert 'error' in response_data
            error = response_data['error']
            assert 'details' in error
            detail = error['details']
            
            # Should have at least one high severity issue
            high_severity_issues = [
                issue for issue in detail['security_issues']
                if issue['severity'] == 'high'
            ]
            assert len(high_severity_issues) > 0, f"Pattern {pattern} should trigger high severity issue"
    
    def test_invalid_file_format_rejected(self):
        """Test that non-JavaScript files are rejected"""
        invalid_content = b"This is not JavaScript"
        
        files = {
            'file': ('test.txt', BytesIO(invalid_content), 'text/plain')
        }
        data = {
            'name': 'Test',
            'description': 'Test',
            'max_players': 10
        }
        
        response = client.post('/upload', files=files, data=data)
        
        # Should be rejected due to file format
        assert response.status_code == 400
    
    def test_empty_file_rejected(self):
        """Test that empty files are rejected"""
        empty_content = b""
        
        files = {
            'file': ('empty.js', BytesIO(empty_content), 'application/javascript')
        }
        data = {
            'name': 'Test',
            'description': 'Test',
            'max_players': 10
        }
        
        response = client.post('/upload', files=files, data=data)
        
        # Should be rejected
        assert response.status_code == 400
    
    def test_oversized_file_rejected(self):
        """Test that files exceeding size limit are rejected"""
        # Create a file larger than 1MB
        large_content = b"x" * (1024 * 1024 + 1)
        
        files = {
            'file': ('large.js', BytesIO(large_content), 'application/javascript')
        }
        data = {
            'name': 'Test',
            'description': 'Test',
            'max_players': 10
        }
        
        response = client.post('/upload', files=files, data=data)
        
        # Should be rejected due to size
        assert response.status_code == 400


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

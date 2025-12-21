"""
Configuration Parameters Property Test

**Feature: ai-game-platform, Property 18: 配置参数应用**
**Validates: Requirements 7.3**

对于任何环境变量配置，所有服务应该正确读取并应用配置参数
"""

import os
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import patch
import logging
from typing import Dict, Any

# Import the Config class from main module
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import Config


class TestMatchmakerConfigurationParametersProperty:
    """Property-based tests for matchmaker configuration parameter application"""

    @given(
        port=st.integers(min_value=1024, max_value=65535),
        heartbeat_timeout=st.integers(min_value=5, max_value=300),
        cleanup_interval=st.integers(min_value=5, max_value=600),
        environment=st.sampled_from(['development', 'staging', 'production']),
        log_level=st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
        debug=st.booleans(),
        log_max_size=st.integers(min_value=1024*1024, max_value=100*1024*1024),
        log_backup_count=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=50)
    def test_matchmaker_configuration_parameters_are_correctly_applied(
        self, port, heartbeat_timeout, cleanup_interval, environment, 
        log_level, debug, log_max_size, log_backup_count
    ):
        """
        Property: For any valid configuration values, the Matchmaker Config class 
        should correctly read and apply those values from environment variables.
        """
        # Prepare environment variables
        env_vars = {
            'HOST': '0.0.0.0',
            'PORT': str(port),
            'DEBUG': str(debug).lower(),
            'ENVIRONMENT': environment,
            'HEARTBEAT_TIMEOUT': str(heartbeat_timeout),
            'CLEANUP_INTERVAL': str(cleanup_interval),
            'LOG_LEVEL': log_level,
            'LOG_FILE': 'test_matchmaker_service.log',
            'LOG_MAX_SIZE': str(log_max_size),
            'LOG_BACKUP_COUNT': str(log_backup_count),
            'ALLOWED_ORIGINS': '*'
        }
        
        # Mock environment variables
        with patch.dict(os.environ, env_vars, clear=False):
            # Force reload of Config class
            import importlib
            import main
            importlib.reload(main)
            from main import Config as ReloadedConfig
            
            # Verify: Configuration values should match environment variables
            assert ReloadedConfig.HOST == '0.0.0.0'
            assert ReloadedConfig.PORT == port
            assert ReloadedConfig.DEBUG == debug
            assert ReloadedConfig.ENVIRONMENT == environment
            assert ReloadedConfig.HEARTBEAT_TIMEOUT == heartbeat_timeout
            assert ReloadedConfig.CLEANUP_INTERVAL == cleanup_interval
            assert ReloadedConfig.LOG_LEVEL == log_level
            assert ReloadedConfig.LOG_FILE == 'test_matchmaker_service.log'
            assert ReloadedConfig.LOG_MAX_SIZE == log_max_size
            assert ReloadedConfig.LOG_BACKUP_COUNT == log_backup_count
            assert ReloadedConfig.ALLOWED_ORIGINS == ['*']

    def test_invalid_matchmaker_configuration_values_are_handled_gracefully(self):
        """
        Property: For any invalid configuration values, the Matchmaker Config class 
        should report validation errors appropriately.
        
        Note: We test validation logic directly rather than trying to reload
        the module with invalid values, since the Config class parses values
        during class definition and would crash.
        """
        # Test the validation logic directly with known invalid values
        
        # Save original values
        original_port = Config.PORT
        original_heartbeat = Config.HEARTBEAT_TIMEOUT
        original_cleanup = Config.CLEANUP_INTERVAL
        original_environment = Config.ENVIRONMENT
        
        try:
            # Test invalid port
            Config.PORT = -1
            validation_errors = Config.validate_config()
            port_errors = [e for e in validation_errors if 'PORT' in e]
            assert len(port_errors) > 0, "Expected PORT validation error for negative port"
            
            # Test invalid heartbeat timeout
            Config.PORT = original_port  # Reset
            Config.HEARTBEAT_TIMEOUT = -1
            validation_errors = Config.validate_config()
            heartbeat_errors = [e for e in validation_errors if 'HEARTBEAT_TIMEOUT' in e]
            assert len(heartbeat_errors) > 0, "Expected HEARTBEAT_TIMEOUT validation error for negative timeout"
            
            # Test invalid cleanup interval
            Config.HEARTBEAT_TIMEOUT = original_heartbeat  # Reset
            Config.CLEANUP_INTERVAL = -1
            validation_errors = Config.validate_config()
            cleanup_errors = [e for e in validation_errors if 'CLEANUP_INTERVAL' in e]
            assert len(cleanup_errors) > 0, "Expected CLEANUP_INTERVAL validation error for negative interval"
            
            # Test invalid environment
            Config.CLEANUP_INTERVAL = original_cleanup  # Reset
            Config.ENVIRONMENT = 'invalid'
            validation_errors = Config.validate_config()
            env_errors = [e for e in validation_errors if 'ENVIRONMENT' in e]
            assert len(env_errors) > 0, "Expected ENVIRONMENT validation error for invalid environment"
            
        finally:
            # Restore original values
            Config.PORT = original_port
            Config.HEARTBEAT_TIMEOUT = original_heartbeat
            Config.CLEANUP_INTERVAL = original_cleanup
            Config.ENVIRONMENT = original_environment

    def test_matchmaker_default_configuration_is_valid(self):
        """
        Property: The default matchmaker configuration should always be valid.
        """
        # Clear all relevant environment variables
        env_vars_to_clear = [
            'HOST', 'PORT', 'DEBUG', 'ENVIRONMENT', 'HEARTBEAT_TIMEOUT',
            'CLEANUP_INTERVAL', 'LOG_LEVEL', 'LOG_FILE', 'LOG_MAX_SIZE',
            'LOG_BACKUP_COUNT', 'ALLOWED_ORIGINS'
        ]
        
        # Create clean environment
        clean_env = {k: v for k, v in os.environ.items() 
                    if k not in env_vars_to_clear}
        
        with patch.dict(os.environ, clean_env, clear=True):
            # Import fresh config with defaults
            import importlib
            import main
            importlib.reload(main)
            from main import Config as ReloadedConfig
            
            # Verify: Default configuration should be valid
            validation_errors = ReloadedConfig.validate_config()
            assert len(validation_errors) == 0, f"Default configuration should be valid, but got errors: {validation_errors}"
            
            # Verify: Default values should be reasonable
            assert 1024 <= ReloadedConfig.PORT <= 65535
            assert ReloadedConfig.ENVIRONMENT in ['development', 'staging', 'production']
            assert ReloadedConfig.HEARTBEAT_TIMEOUT > 0
            assert ReloadedConfig.CLEANUP_INTERVAL > 0

    @given(
        environment=st.sampled_from(['development', 'staging', 'production'])
    )
    @settings(max_examples=10)
    def test_matchmaker_environment_specific_configuration_is_consistent(self, environment):
        """
        Property: For any valid environment, the matchmaker configuration should be 
        internally consistent and appropriate for that environment.
        """
        env_vars = {'ENVIRONMENT': environment}
        
        with patch.dict(os.environ, env_vars, clear=False):
            import importlib
            import main
            importlib.reload(main)
            from main import Config as ReloadedConfig
            
            # Verify: Environment-specific behavior
            cors_config = ReloadedConfig.get_cors_config()
            
            if environment == 'production':
                # Production should have stricter CORS settings
                if ReloadedConfig.ALLOWED_ORIGINS == ['*']:
                    assert cors_config['allow_origins'] == []
                else:
                    assert cors_config['allow_origins'] == ReloadedConfig.ALLOWED_ORIGINS
            else:
                # Development/staging should be more permissive
                assert cors_config['allow_origins'] == ['*']

    @given(
        allowed_origins=st.lists(
            st.sampled_from(['*', 'http://localhost:3000', 'https://example.com', 'http://127.0.0.1:8080']),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=15)
    def test_matchmaker_cors_configuration_is_applied_correctly(self, allowed_origins):
        """
        Property: For any list of allowed origins, the matchmaker CORS configuration 
        should be correctly applied based on the environment.
        """
        origins_str = ','.join(allowed_origins)
        env_vars = {
            'ALLOWED_ORIGINS': origins_str,
            'ENVIRONMENT': 'production'  # Test production behavior
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            import importlib
            import main
            importlib.reload(main)
            from main import Config as ReloadedConfig
            
            # Verify: Origins are parsed correctly
            assert ReloadedConfig.ALLOWED_ORIGINS == allowed_origins
            
            # Verify: CORS config respects environment and origins
            cors_config = ReloadedConfig.get_cors_config()
            
            if allowed_origins == ['*']:
                # In production with exactly ['*'], should use empty list for security
                assert cors_config['allow_origins'] == []
            else:
                # Should use the specified origins (even if they contain '*' mixed with others)
                assert cors_config['allow_origins'] == allowed_origins
            
            # Verify: Other CORS settings are appropriate for production
            assert cors_config['allow_credentials'] == True
            assert cors_config['allow_methods'] == ['GET', 'POST', 'DELETE']

    def test_matchmaker_configuration_consistency_across_multiple_calls(self):
        """
        Property: Matchmaker configuration values should be consistent across 
        multiple calls and not change during runtime.
        """
        # Set some environment variables
        env_vars = {
            'PORT': '9000',
            'ENVIRONMENT': 'staging',
            'HEARTBEAT_TIMEOUT': '45',
            'CLEANUP_INTERVAL': '15'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            import importlib
            import main
            importlib.reload(main)
            from main import Config as ReloadedConfig
            
            # Get values multiple times
            port1 = ReloadedConfig.PORT
            port2 = ReloadedConfig.PORT
            env1 = ReloadedConfig.ENVIRONMENT
            env2 = ReloadedConfig.ENVIRONMENT
            heartbeat1 = ReloadedConfig.HEARTBEAT_TIMEOUT
            heartbeat2 = ReloadedConfig.HEARTBEAT_TIMEOUT
            cleanup1 = ReloadedConfig.CLEANUP_INTERVAL
            cleanup2 = ReloadedConfig.CLEANUP_INTERVAL
            
            # Verify: Values should be consistent
            assert port1 == port2 == 9000
            assert env1 == env2 == 'staging'
            assert heartbeat1 == heartbeat2 == 45
            assert cleanup1 == cleanup2 == 15
            
            # Verify: Validation should be consistent
            errors1 = ReloadedConfig.validate_config()
            errors2 = ReloadedConfig.validate_config()
            assert errors1 == errors2

    @given(
        heartbeat_timeout=st.integers(min_value=10, max_value=120),
        cleanup_interval=st.integers(min_value=5, max_value=300)
    )
    @settings(max_examples=20)
    def test_matchmaker_timing_configuration_is_reasonable(self, heartbeat_timeout, cleanup_interval):
        """
        Property: For any valid timing configuration, the values should be reasonable
        and the cleanup interval should be appropriate relative to heartbeat timeout.
        """
        # Assume: cleanup_interval should be reasonable relative to heartbeat_timeout
        from hypothesis import assume
        assume(cleanup_interval <= heartbeat_timeout * 20)
        
        env_vars = {
            'HEARTBEAT_TIMEOUT': str(heartbeat_timeout),
            'CLEANUP_INTERVAL': str(cleanup_interval)
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            import importlib
            import main
            importlib.reload(main)
            from main import Config as ReloadedConfig
            
            # Verify: Configuration values are applied
            assert ReloadedConfig.HEARTBEAT_TIMEOUT == heartbeat_timeout
            assert ReloadedConfig.CLEANUP_INTERVAL == cleanup_interval
            
            # Verify: Values are reasonable
            assert ReloadedConfig.HEARTBEAT_TIMEOUT > 0
            assert ReloadedConfig.CLEANUP_INTERVAL > 0
            
            # Verify: Cleanup interval should be reasonable relative to heartbeat
            # (This is a business logic check - cleanup shouldn't be too frequent)
            # Allow cleanup interval to be up to 20x the heartbeat timeout for flexibility
            assert ReloadedConfig.CLEANUP_INTERVAL <= ReloadedConfig.HEARTBEAT_TIMEOUT * 20
            
            # Verify: No validation errors for valid timing config
            validation_errors = ReloadedConfig.validate_config()
            timing_errors = [e for e in validation_errors 
                           if 'HEARTBEAT_TIMEOUT' in e or 'CLEANUP_INTERVAL' in e]
            assert len(timing_errors) == 0, f"Valid timing config should not produce errors: {timing_errors}"

    @given(
        log_level=st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
        log_max_size=st.integers(min_value=1024*1024, max_value=50*1024*1024),
        log_backup_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=20)
    def test_matchmaker_logging_configuration_is_valid(self, log_level, log_max_size, log_backup_count):
        """
        Property: For any valid logging configuration, the matchmaker log config 
        should be properly formatted and usable by the logging system.
        """
        env_vars = {
            'LOG_LEVEL': log_level,
            'LOG_MAX_SIZE': str(log_max_size),
            'LOG_BACKUP_COUNT': str(log_backup_count),
            'LOG_FILE': 'test_matchmaker.log'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            import importlib
            import main
            importlib.reload(main)
            from main import Config as ReloadedConfig
            
            # Verify: Configuration values are applied
            assert ReloadedConfig.LOG_LEVEL == log_level
            assert ReloadedConfig.LOG_MAX_SIZE == log_max_size
            assert ReloadedConfig.LOG_BACKUP_COUNT == log_backup_count
            
            # Verify: Log level is valid for Python logging
            assert hasattr(logging, log_level)
            log_numeric_level = getattr(logging, log_level)
            assert isinstance(log_numeric_level, int)
            
            # Verify: No validation errors for valid log config
            validation_errors = ReloadedConfig.validate_config()
            log_errors = [e for e in validation_errors if 'LOG_LEVEL' in e]
            assert len(log_errors) == 0, f"Valid log level should not produce errors: {log_errors}"
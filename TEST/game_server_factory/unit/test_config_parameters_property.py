"""
Configuration Parameters Property Test

**Feature: ai-game-platform, Property 18: 配置参数应用**
**Validates: Requirements 7.3**

对于任何环境变量配置，所有服务应该正确读取并应用配置参数
"""

import os
import tempfile
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import patch
import logging
from typing import Dict, Any

# Import the Config class from main module
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import Config


class TestConfigurationParametersProperty:
    """Property-based tests for configuration parameter application"""

    @given(
        port=st.integers(min_value=1024, max_value=65535),
        base_port=st.integers(min_value=1024, max_value=65535),
        max_file_size=st.integers(min_value=1024, max_value=100*1024*1024),  # 1KB to 100MB
        max_containers=st.integers(min_value=1, max_value=1000),
        upload_timeout=st.integers(min_value=30, max_value=3600),  # 30s to 1h
        idle_timeout=st.integers(min_value=300, max_value=7200),  # 5min to 2h
        cleanup_interval=st.integers(min_value=60, max_value=1800),  # 1min to 30min
        environment=st.sampled_from(['development', 'staging', 'production']),
        log_level=st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
        debug=st.booleans(),
        container_memory_limit=st.sampled_from(['128m', '256m', '512m', '1g', '2g']),
        container_cpu_limit=st.floats(min_value=0.1, max_value=4.0),
        heartbeat_timeout=st.integers(min_value=5, max_value=120),
        log_max_size=st.integers(min_value=1024*1024, max_value=100*1024*1024),  # 1MB to 100MB
        log_backup_count=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=10)
    def test_configuration_parameters_are_correctly_applied(
        self, port, base_port, max_file_size, max_containers, upload_timeout,
        idle_timeout, cleanup_interval, environment, log_level, debug,
        container_memory_limit, container_cpu_limit, heartbeat_timeout,
        log_max_size, log_backup_count
    ):
        """
        Property: For any valid configuration values, the Config class should correctly
        read and apply those values from environment variables.
        """
        # Prepare environment variables
        env_vars = {
            'HOST': '0.0.0.0',
            'PORT': str(port),
            'DEBUG': str(debug).lower(),
            'ENVIRONMENT': environment,
            'MAX_FILE_SIZE': str(max_file_size),
            'ALLOWED_EXTENSIONS': '.js,.mjs,.ts',
            'UPLOAD_TIMEOUT': str(upload_timeout),
            'DOCKER_NETWORK': 'test-network',
            'BASE_PORT': str(base_port),
            'MAX_CONTAINERS': str(max_containers),
            'CONTAINER_MEMORY_LIMIT': container_memory_limit,
            'CONTAINER_CPU_LIMIT': str(container_cpu_limit),
            'MATCHMAKER_URL': 'http://localhost:8000',
            'MATCHMAKER_TIMEOUT': str(heartbeat_timeout),
            'IDLE_TIMEOUT_SECONDS': str(idle_timeout),
            'CLEANUP_INTERVAL_SECONDS': str(cleanup_interval),
            'RESOURCE_CHECK_INTERVAL': '60',
            'LOG_LEVEL': log_level,
            'LOG_FILE': 'test_game_server_factory.log',
            'LOG_MAX_SIZE': str(log_max_size),
            'LOG_BACKUP_COUNT': str(log_backup_count),
            'ALLOWED_ORIGINS': '*',
            'API_RATE_LIMIT': '100'
        }
        
        # Mock environment variables
        with patch.dict(os.environ, env_vars, clear=False):
            # Force reload of Config class by creating a new instance
            # Since Config is a class with class variables, we need to reload the module
            import importlib
            import main
            importlib.reload(main)
            from main import Config as ReloadedConfig
            
            # Verify: Configuration values should match environment variables
            assert ReloadedConfig.HOST == '0.0.0.0'
            assert ReloadedConfig.PORT == port
            assert ReloadedConfig.DEBUG == debug
            assert ReloadedConfig.ENVIRONMENT == environment
            assert ReloadedConfig.MAX_FILE_SIZE == max_file_size
            assert ReloadedConfig.ALLOWED_EXTENSIONS == ['.js', '.mjs', '.ts']
            assert ReloadedConfig.UPLOAD_TIMEOUT == upload_timeout
            assert ReloadedConfig.DOCKER_NETWORK == 'test-network'
            assert ReloadedConfig.BASE_PORT == base_port
            assert ReloadedConfig.MAX_CONTAINERS == max_containers
            assert ReloadedConfig.CONTAINER_MEMORY_LIMIT == container_memory_limit
            assert ReloadedConfig.CONTAINER_CPU_LIMIT == container_cpu_limit
            assert ReloadedConfig.MATCHMAKER_URL == 'http://localhost:8000'
            assert ReloadedConfig.MATCHMAKER_TIMEOUT == heartbeat_timeout
            assert ReloadedConfig.IDLE_TIMEOUT_SECONDS == idle_timeout
            assert ReloadedConfig.CLEANUP_INTERVAL_SECONDS == cleanup_interval
            assert ReloadedConfig.LOG_LEVEL == log_level
            assert ReloadedConfig.LOG_FILE == 'test_game_server_factory.log'
            assert ReloadedConfig.LOG_MAX_SIZE == log_max_size
            assert ReloadedConfig.LOG_BACKUP_COUNT == log_backup_count
            assert ReloadedConfig.ALLOWED_ORIGINS == ['*']
            assert ReloadedConfig.API_RATE_LIMIT == 100

    def test_invalid_configuration_values_are_handled_gracefully(self):
        """
        Property: For any invalid configuration values, the Config class should
        report validation errors appropriately.
        
        Note: We test validation logic directly rather than trying to reload
        the module with invalid values, since the Config class parses values
        during class definition and would crash.
        """
        # Test the validation logic directly with known invalid values
        
        # Save original values
        original_port = Config.PORT
        original_file_size = Config.MAX_FILE_SIZE
        original_environment = Config.ENVIRONMENT
        original_log_level = Config.LOG_LEVEL
        
        try:
            # Test invalid port
            Config.PORT = -1
            validation_errors = Config.validate_config()
            port_errors = [e for e in validation_errors if 'PORT' in e]
            assert len(port_errors) > 0, "Expected PORT validation error for negative port"
            
            # Test invalid file size
            Config.PORT = original_port  # Reset
            Config.MAX_FILE_SIZE = -1
            validation_errors = Config.validate_config()
            file_size_errors = [e for e in validation_errors if 'MAX_FILE_SIZE' in e]
            assert len(file_size_errors) > 0, "Expected MAX_FILE_SIZE validation error for negative size"
            
            # Test invalid environment
            Config.MAX_FILE_SIZE = original_file_size  # Reset
            Config.ENVIRONMENT = 'invalid'
            validation_errors = Config.validate_config()
            env_errors = [e for e in validation_errors if 'ENVIRONMENT' in e]
            assert len(env_errors) > 0, "Expected ENVIRONMENT validation error for invalid environment"
            
            # Test invalid log level
            Config.ENVIRONMENT = original_environment  # Reset
            Config.LOG_LEVEL = 'INVALID'
            validation_errors = Config.validate_config()
            log_errors = [e for e in validation_errors if 'LOG_LEVEL' in e]
            assert len(log_errors) > 0, "Expected LOG_LEVEL validation error for invalid log level"
            
        finally:
            # Restore original values
            Config.PORT = original_port
            Config.MAX_FILE_SIZE = original_file_size
            Config.ENVIRONMENT = original_environment
            Config.LOG_LEVEL = original_log_level

    def test_default_configuration_is_valid(self):
        """
        Property: The default configuration (when no environment variables are set)
        should always be valid and pass validation.
        """
        # Clear all relevant environment variables
        env_vars_to_clear = [
            'HOST', 'PORT', 'DEBUG', 'ENVIRONMENT', 'MAX_FILE_SIZE',
            'ALLOWED_EXTENSIONS', 'UPLOAD_TIMEOUT', 'DOCKER_NETWORK',
            'BASE_PORT', 'MAX_CONTAINERS', 'CONTAINER_MEMORY_LIMIT',
            'CONTAINER_CPU_LIMIT', 'MATCHMAKER_URL', 'MATCHMAKER_TIMEOUT',
            'IDLE_TIMEOUT_SECONDS', 'CLEANUP_INTERVAL_SECONDS',
            'RESOURCE_CHECK_INTERVAL', 'LOG_LEVEL', 'LOG_FILE',
            'LOG_MAX_SIZE', 'LOG_BACKUP_COUNT', 'ALLOWED_ORIGINS',
            'API_RATE_LIMIT'
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
            assert ReloadedConfig.MAX_FILE_SIZE > 0
            assert ReloadedConfig.MAX_CONTAINERS > 0
            assert ReloadedConfig.UPLOAD_TIMEOUT > 0
            assert ReloadedConfig.IDLE_TIMEOUT_SECONDS > 0
            assert ReloadedConfig.LOG_LEVEL in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

    @given(
        environment=st.sampled_from(['development', 'staging', 'production'])
    )
    @settings(max_examples=10)
    def test_environment_specific_configuration_is_consistent(self, environment):
        """
        Property: For any valid environment, the configuration should be internally
        consistent and appropriate for that environment.
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
                assert ReloadedConfig.is_production() == True
                # In production, should not allow all origins unless explicitly set to *
                if ReloadedConfig.ALLOWED_ORIGINS == ['*']:
                    assert cors_config['allow_origins'] == []
                else:
                    assert cors_config['allow_origins'] == ReloadedConfig.ALLOWED_ORIGINS
            else:
                # Development/staging should be more permissive
                assert ReloadedConfig.is_production() == False
                assert cors_config['allow_origins'] == ['*']
            
            # Verify: Log configuration is valid
            log_config = ReloadedConfig.get_log_config()
            assert 'level' in log_config
            assert 'format' in log_config
            assert 'handlers' in log_config
            assert hasattr(logging, ReloadedConfig.LOG_LEVEL.upper())

    @given(
        allowed_origins=st.lists(
            st.sampled_from(['*', 'http://localhost:3000', 'https://example.com', 'http://127.0.0.1:8080']),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=10)
    def test_cors_configuration_is_applied_correctly(self, allowed_origins):
        """
        Property: For any list of allowed origins, the CORS configuration should
        be correctly applied based on the environment.
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

    def test_configuration_consistency_across_multiple_calls(self):
        """
        Property: Configuration values should be consistent across multiple calls
        and not change during runtime (unless environment changes).
        """
        # Set some environment variables
        env_vars = {
            'PORT': '9000',
            'ENVIRONMENT': 'staging',
            'MAX_CONTAINERS': '25'
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
            containers1 = ReloadedConfig.MAX_CONTAINERS
            containers2 = ReloadedConfig.MAX_CONTAINERS
            
            # Verify: Values should be consistent
            assert port1 == port2 == 9000
            assert env1 == env2 == 'staging'
            assert containers1 == containers2 == 25
            
            # Verify: Validation should be consistent
            errors1 = ReloadedConfig.validate_config()
            errors2 = ReloadedConfig.validate_config()
            assert errors1 == errors2

    @given(
        log_level=st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
        log_max_size=st.integers(min_value=1024*1024, max_value=50*1024*1024),
        log_backup_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=10)
    def test_logging_configuration_is_valid(self, log_level, log_max_size, log_backup_count):
        """
        Property: For any valid logging configuration, the log config should be
        properly formatted and usable by the logging system.
        """
        env_vars = {
            'LOG_LEVEL': log_level,
            'LOG_MAX_SIZE': str(log_max_size),
            'LOG_BACKUP_COUNT': str(log_backup_count),
            'LOG_FILE': 'test.log'
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
            
            # Verify: Log configuration is valid
            log_config = ReloadedConfig.get_log_config()
            
            # Should have valid logging level
            assert log_config['level'] == getattr(logging, log_level)
            
            # Should have format string
            assert isinstance(log_config['format'], str)
            assert '%(asctime)s' in log_config['format']
            assert '%(levelname)s' in log_config['format']
            
            # Should have handlers configuration
            assert isinstance(log_config['handlers'], list)
            assert len(log_config['handlers']) >= 1
            
            # Verify: No validation errors for valid log config
            validation_errors = ReloadedConfig.validate_config()
            log_errors = [e for e in validation_errors if 'LOG_LEVEL' in e]
            assert len(log_errors) == 0, f"Valid log level should not produce errors: {log_errors}"
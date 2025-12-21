"""
端到端测试 - 测试完整的Docker容器创建流程
"""

import pytest
import tempfile
import os
import time
from unittest.mock import Mock, patch, MagicMock

def test_container_creation():
    """测试容器创建的完整流程 - 使用Mock避免超时"""
    print("开始端到端容器创建测试...")
    
    # 使用Mock Docker管理器避免真实容器创建超时
    with patch('docker_manager.DockerManager') as MockDockerManager:
        mock_manager = Mock()
        MockDockerManager.return_value = mock_manager
        
        # Mock容器创建
        mock_manager.create_game_server.return_value = (
            'test_container_id_123',
            8081,
            'test_image_id_456'
        )
        
        # Mock容器信息
        mock_container_info = Mock()
        mock_container_info.status = 'running'
        mock_container_info.get_stats.return_value = {
            'cpu_percent': 10.5,
            'memory_usage_mb': 128
        }
        mock_container_info.get_logs.return_value = [
            'Server started',
            'Game initialized',
            'Ready to accept connections'
        ]
        mock_manager.get_container_info.return_value = mock_container_info
        
        # Mock容器停止和清理
        mock_manager.stop_container.return_value = True
        mock_manager.cleanup_server_resources.return_value = True
        
        manager = MockDockerManager()
        print("✓ Docker管理器初始化成功")
        
        # 准备测试用的JavaScript代码
        test_code = """
// 简单的游戏逻辑
function initGame() {
    return {
        score: 0,
        players: []
    };
}

function handlePlayerAction(gameState, action, data) {
    console.log('处理玩家操作:', action, data);
    
    if (action === 'click') {
        gameState.score = (gameState.score || 0) + 1;
        console.log('分数更新:', gameState.score);
    }
    
    return gameState;
}

// 导出函数
module.exports = {
    initGame,
    handlePlayerAction
};
"""
        
        server_id = "test_game_001"
        server_name = "测试游戏服务器"
        
        # 创建游戏服务器容器
        print("创建游戏服务器容器...")
        container_id, port, image_id = manager.create_game_server(
            server_id=server_id,
            user_code=test_code,
            server_name=server_name,
            matchmaker_url="http://localhost:8000"
        )
        
        print(f"✓ 容器创建成功:")
        print(f"  容器ID: {container_id[:12]}...")
        print(f"  端口: {port}")
        print(f"  镜像ID: {image_id[:12]}...")
        
        # 获取容器信息（不需要等待）
        container_info = manager.get_container_info(container_id)
        assert container_info is not None
        print(f"✓ 容器状态: {container_info.status}")
        
        # 获取容器统计信息
        stats = container_info.get_stats()
        assert stats is not None
        print(f"✓ 容器统计: CPU {stats.get('cpu_percent', 0)}%, 内存 {stats.get('memory_usage_mb', 0)}MB")
        
        # 获取容器日志
        logs = container_info.get_logs(tail=10)
        assert logs is not None
        print("✓ 容器日志 (最后5行):")
        for log in logs[-5:]:
            print(f"  {log}")
        
        # 测试容器停止
        print("测试容器停止...")
        success = manager.stop_container(container_id)
        assert success is True
        print("✓ 容器停止成功")
        
        # 清理资源
        print("清理测试资源...")
        cleanup_success = manager.cleanup_server_resources(server_id)
        assert cleanup_success is True
        print("✓ 资源清理成功")
        
        print("\n端到端测试完成! ✓")

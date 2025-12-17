"""
端到端测试 - 测试完整的Docker容器创建流程
"""

import tempfile
import os
import time
from docker_manager import DockerManager

def test_container_creation():
    """测试容器创建的完整流程"""
    print("开始端到端容器创建测试...")
    
    # 创建Docker管理器
    manager = DockerManager()
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
    
    try:
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
        
        # 等待容器启动
        print("等待容器启动...")
        time.sleep(5)
        
        # 获取容器信息
        container_info = manager.get_container_info(container_id)
        if container_info:
            container_info.refresh()
            print(f"✓ 容器状态: {container_info.status}")
            
            # 获取容器统计信息
            stats = container_info.get_stats()
            if stats:
                print(f"✓ 容器统计: CPU {stats.get('cpu_percent', 0)}%, 内存 {stats.get('memory_usage_mb', 0)}MB")
            
            # 获取容器日志
            logs = container_info.get_logs(tail=10)
            if logs:
                print("✓ 容器日志 (最后10行):")
                for log in logs[-5:]:  # 显示最后5行
                    print(f"  {log}")
        
        # 测试容器停止
        print("测试容器停止...")
        success = manager.stop_container(container_id)
        if success:
            print("✓ 容器停止成功")
        
        # 清理资源
        print("清理测试资源...")
        cleanup_success = manager.cleanup_server_resources(server_id)
        if cleanup_success:
            print("✓ 资源清理成功")
        
        print("\n端到端测试完成! ✓")
        return True
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 尝试清理
        try:
            manager.cleanup_server_resources(server_id)
            print("✓ 清理完成")
        except:
            pass
        
        return False

if __name__ == "__main__":
    success = test_container_creation()
    if success:
        print("所有测试通过!")
    else:
        print("测试失败!")
        exit(1)
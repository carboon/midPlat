"""
简单的Docker功能测试 - 不构建镜像，只测试管理功能
"""

import time
from docker_manager import DockerManager

def test_docker_basic_functions():
    """测试Docker基本功能"""
    print("开始Docker基本功能测试...")
    
    try:
        # 创建Docker管理器
        manager = DockerManager()
        print("✓ Docker管理器初始化成功")
        
        # 测试系统统计
        stats = manager.get_system_stats()
        print(f"✓ 系统统计获取成功: {stats}")
        
        # 测试容器列表
        containers = manager.list_game_containers()
        print(f"✓ 游戏容器列表获取成功: {len(containers)} 个容器")
        
        # 测试端口查找
        port = manager._find_available_port()
        print(f"✓ 可用端口查找成功: {port}")
        
        # 测试Dockerfile生成
        dockerfile = manager._generate_dockerfile("console.log('test');", "测试游戏")
        print("✓ Dockerfile生成成功")
        print("Dockerfile内容预览:")
        print(dockerfile[:200] + "...")
        
        # 测试服务器模板生成
        server_template = manager._generate_server_template(
            "console.log('test');", 
            "测试游戏", 
            "http://localhost:8000"
        )
        print("✓ 服务器模板生成成功")
        print(f"服务器模板长度: {len(server_template)} 字符")
        
        # 测试用户代码准备
        prepared_code = manager._prepare_user_code("function test() { return 'hello'; }")
        print("✓ 用户代码准备成功")
        print(f"准备后代码长度: {len(prepared_code)} 字符")
        
        print("\n所有基本功能测试通过! ✓")
        return True
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_container():
    """测试简单容器操作（使用现有镜像）"""
    print("\n开始简单容器测试...")
    
    try:
        manager = DockerManager()
        
        # 使用hello-world镜像进行快速测试
        print("创建测试容器...")
        container = manager.client.containers.run(
            "hello-world",
            detach=True,
            remove=True,
            labels={"created_by": "game_server_factory", "test": "true"}
        )
        
        print(f"✓ 测试容器创建成功: {container.id[:12]}")
        
        # 等待容器完成
        time.sleep(2)
        
        # 检查容器状态
        container.reload()
        print(f"✓ 容器状态: {container.status}")
        
        print("简单容器测试完成! ✓")
        return True
        
    except Exception as e:
        print(f"简单容器测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=== Docker管理器功能测试 ===\n")
    
    # 测试基本功能
    basic_success = test_docker_basic_functions()
    
    # 测试简单容器
    container_success = test_simple_container()
    
    if basic_success and container_success:
        print("\n=== 所有测试通过! ===")
        print("Docker容器管理功能已准备就绪")
    else:
        print("\n=== 部分测试失败 ===")
        if basic_success:
            print("✓ 基本功能正常")
        if container_success:
            print("✓ 容器操作正常")
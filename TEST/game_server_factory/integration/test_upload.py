#!/usr/bin/env python3
"""
测试文件上传端点
"""

import io
from fastapi.testclient import TestClient
from main import app

def test_upload_endpoint():
    client = TestClient(app)
    
    # 创建一个简单的HTML游戏文件
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>测试游戏</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        button { padding: 10px 20px; font-size: 16px; cursor: pointer; }
        #score { font-size: 24px; margin: 20px; }
    </style>
</head>
<body>
    <h1>简单点击游戏</h1>
    <div id="score">分数: 0</div>
    <button onclick="increaseScore()">点击我！</button>
    
    <script>
        let score = 0;
        function increaseScore() {
            score++;
            document.getElementById('score').textContent = '分数: ' + score;
        }
    </script>
</body>
</html>'''

    print('测试 POST /upload - HTML游戏文件上传')

    # 创建文件对象
    files = {
        'file': ('test_game.html', html_content, 'text/html')
    }

    # 表单数据
    data = {
        'name': '测试点击游戏',
        'description': '一个简单的点击计分游戏',
        'max_players': 10
    }

    try:
        response = client.post('/upload', files=files, data=data)
        print(f'状态码: {response.status_code}')
        
        if response.status_code == 200:
            result = response.json()
            print(f'上传成功！')
            print(f'服务器ID: {result.get("server_id")}')
            print(f'消息: {result.get("message")}')
            print(f'验证结果: {result.get("validation_result")}')
            
            # 测试获取刚创建的服务器详情
            server_id = result.get('server_id')
            if server_id:
                print(f'\n测试获取服务器详情: {server_id}')
                detail_response = client.get(f'/servers/{server_id}')
                print(f'详情状态码: {detail_response.status_code}')
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    print(f'服务器名称: {detail_data.get("name")}')
                    print(f'服务器状态: {detail_data.get("status")}')
                    print(f'容器ID: {detail_data.get("container_id")}')
                    print(f'端口: {detail_data.get("port")}')
                    
                    # 测试获取服务器列表
                    print(f'\n测试获取服务器列表')
                    list_response = client.get('/servers')
                    print(f'列表状态码: {list_response.status_code}')
                    if list_response.status_code == 200:
                        servers = list_response.json()
                        print(f'服务器数量: {len(servers)}')
                        if servers:
                            print(f'第一个服务器: {servers[0].get("name")} - {servers[0].get("status")}')
        else:
            print(f'上传失败: {response.json()}')
            
    except Exception as e:
        print(f'测试过程中出现错误: {e}')
        import traceback
        traceback.print_exc()

    print('\n文件上传端点测试完成！')

if __name__ == "__main__":
    test_upload_endpoint()
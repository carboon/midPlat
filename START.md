完整启动顺序
1. 启动匹配服务 (第一个启动)
方式一：使用Docker (推荐)

# 进入匹配服务目录
cd matchmaker_service/matchmaker

# 构建并启动匹配服务
docker-compose up -d

# 查看日志
docker-compose logs -f
方式二：本地Python运行

# 进入匹配服务目录
cd matchmaker_service/matchmaker

# 创建虚拟环境（首次运行）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖（首次运行）
pip install -r requirements.txt

# 启动服务
python main.py
2. 启动游戏服务器 (第二个启动)
方式一：使用Docker (推荐)

# 新开终端，进入游戏服务器目录
cd game_server_template

# 构建并启动游戏服务器
docker-compose up --build

# 或者后台运行
docker-compose up -d --build
方式二：本地Node.js运行

# 新开终端，进入游戏服务器目录
cd game_server_template

# 安装依赖（首次运行）
npm install

# 启动服务
npm start
3. 启动Flutter客户端 (第三个启动)
# 新开终端，进入Flutter客户端目录
cd mobile_app/universal_game_client

# 获取依赖（首次运行）
flutter pub get

# 启动应用 - macOS
flutter run -d macos

# 或启动应用 - 其他平台
flutter run  # 会提示选择设备
使用全局Docker Compose (最简单方式)
如果想一次性启动所有服务，可以使用项目根目录的docker-compose.yml：

# 在项目根目录执行
docker-compose up -d

# 查看所有服务状态
docker-compose ps

# 查看所有服务日志
docker-compose logs -f

# 然后单独启动Flutter客户端
cd mobile_app/universal_game_client
flutter run -d macos
验证服务启动
验证匹配服务 (端口 8000)
curl http://localhost:8000/
# 预期响应: {"service":"Game Matchmaker","version":"1.0.0","status":"running","active_servers":1}

curl http://localhost:8000/servers
# 预期响应: 服务器列表JSON
验证游戏服务器 (端口 8080)
curl http://localhost:8080/
# 预期响应: HTML游戏页面

# 或在浏览器中访问
open http://localhost:8080
验证Flutter客户端
应用成功启动并显示主界面
能够加载房间列表
能够连接到游戏服务器
停止服务
停止Docker服务
# 停止特定服务
docker-compose stop matchmaker
docker-compose stop game-server

# 停止所有服务
docker-compose stop

# 停止并删除容器
docker-compose down
停止本地服务
在各个终端中按 Ctrl+C 停止服务
Flutter应用可以直接关闭窗口或在终端按 q 退出
重要注意事项
启动顺序很重要：必须先启动匹配服务，再启动游戏服务器，最后启动客户端
端口检查：确保端口8000和8080没有被其他程序占用
网络配置：确保防火墙允许这些端口的访问
依赖安装：首次运行需要安装各服务的依赖包
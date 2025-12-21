# HTML游戏上传功能 - Bug修复设计文档

## 概述

本文档描述了HTML游戏上传功能中三个关键bug的修复方案。这些修复涉及后端API、Docker容器管理和Dart客户端模型的改进。

## 架构

### 当前架构问题

```
用户上传 → Flutter客户端 → Game_Server_Factory → Docker容器创建
   ↓                              ↓                      ↓
问题1:                      问题2:                   问题3:
Description强制            类型转换错误              容器管理失败
```

### 修复后的架构

```
用户上传 → Flutter客户端 → Game_Server_Factory → Docker容器创建
   ↓                              ↓                      ↓
修复1:                      修复2:                   修复3:
Description可选            类型安全                 容器隔离
```

## 组件和接口

### 1. 后端API修复 (game_server_factory/main.py)

#### 修复 1.1: HTMLGameUploadRequest 模型

**当前问题**:
```python
class HTMLGameUploadRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)  # 强制要求
    max_players: int = Field(default=10, ge=1, le=100)
```

**修复方案**:
```python
class HTMLGameUploadRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)  # 改为可选，默认为空字符串
    max_players: int = Field(default=10, ge=1, le=100)
```

#### 修复 1.2: 上传端点参数处理

**当前问题**:
```python
@app.post("/upload")
async def upload_html_game(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(...),  # 强制要求
    max_players: int = Form(default=10)
):
```

**修复方案**:
```python
@app.post("/upload")
async def upload_html_game(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(default=""),  # 改为可选，默认为空字符串
    max_players: int = Form(default=10)
):
```

#### 修复 1.3: GameServerInstance 模型确保类型安全

**当前问题**:
```python
class GameServerInstance(BaseModel):
    description: str = Field(..., max_length=500)  # 可能为null
```

**修复方案**:
```python
class GameServerInstance(BaseModel):
    description: str = Field(default="", max_length=500)  # 确保始终有值
```

### 2. Docker容器管理修复 (game_server_factory/docker_manager.py)

#### 修复 2.1: 改进端口分配机制

**当前问题**:
- `_find_available_port()` 只检查本地socket绑定，不检查Docker容器已使用的端口
- 可能导致端口冲突

**修复方案**:
```python
def _find_available_port(self) -> int:
    """查找可用端口，考虑Docker容器已使用的端口"""
    import socket
    
    # 获取所有已使用的端口（包括Docker容器）
    used_ports = self._get_used_ports()
    
    port = self.base_port
    while port < self.base_port + 1000:
        if port not in used_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                pass
        port += 1
    
    raise RuntimeError("无法找到可用端口")

def _get_used_ports(self) -> set:
    """获取所有已使用的端口（包括Docker容器）"""
    used_ports = set()
    
    try:
        # 获取所有游戏容器
        containers = self.list_game_containers()
        for container in containers:
            # 从容器端口映射中提取端口
            if container.container.ports:
                for port_mapping in container.container.ports.values():
                    if port_mapping:
                        for mapping in port_mapping:
                            if 'HostPort' in mapping:
                                used_ports.add(int(mapping['HostPort']))
    except Exception as e:
        logger.warning(f"获取已使用端口失败: {e}")
    
    return used_ports
```

#### 修复 2.2: 改进容器创建和错误处理

**当前问题**:
- 容器创建失败时没有正确的清理机制
- 镜像构建失败时没有清理临时镜像

**修复方案**:
```python
def create_html_game_server(
    self, 
    server_id: str, 
    html_content: str,
    other_files: Dict[str, str],
    server_name: str,
    matchmaker_url: str = "http://localhost:8000"
) -> Tuple[str, int, str]:
    """创建HTML游戏服务器容器，带有完整的错误处理和清理"""
    
    container_id = None
    image_tag = None
    
    try:
        logger.info(f"开始创建HTML游戏服务器容器: {server_id}")
        
        # 查找可用端口
        port = self._find_available_port()
        logger.info(f"分配端口: {port}")
        
        # 创建临时目录并构建镜像
        with tempfile.TemporaryDirectory() as temp_dir:
            # ... 文件准备代码 ...
            
            # 构建Docker镜像
            safe_server_id = self._sanitize_docker_tag(server_id)
            image_tag = f"{self.image_name_prefix}:{safe_server_id}"
            
            try:
                image, build_logs = self.client.images.build(
                    path=temp_dir,
                    tag=image_tag,
                    rm=True,
                    forcerm=True
                )
                logger.info(f"Docker镜像构建完成: {image.id}")
            except Exception as build_error:
                logger.error(f"Docker镜像构建失败: {build_error}")
                # 尝试清理镜像
                try:
                    self.client.images.remove(image_tag, force=True)
                except:
                    pass
                raise RuntimeError(f"镜像构建失败: {str(build_error)}")
        
        # 创建并启动容器
        container_name = f"html-game-server-{server_id}"
        
        try:
            container = self.client.containers.run(
                image=image_tag,
                name=container_name,
                ports={'8080/tcp': port},
                environment={
                    'PORT': '8080',
                    'EXTERNAL_PORT': str(port),
                    'ROOM_NAME': server_name,
                    'MATCHMAKER_URL': 'http://host.docker.internal:8000',
                    'NODE_ENV': 'production'
                },
                network=self.network_name,
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                labels={
                    "created_by": "game_server_factory",
                    "server_id": server_id,
                    "server_name": server_name,
                    "game_type": "html"
                }
            )
            
            container_id = container.id
            logger.info(f"HTML游戏容器创建成功: {container_id} (端口: {port})")
            
            # 验证容器是否正常运行
            container.reload()
            if container.status != 'running':
                raise RuntimeError(f"容器创建后状态异常: {container.status}")
            
            return container_id, port, image.id
            
        except Exception as container_error:
            logger.error(f"容器创建或启动失败: {container_error}")
            
            # 清理已创建的容器
            if container_id:
                try:
                    container = self.client.containers.get(container_id)
                    container.stop(timeout=5)
                    container.remove(force=True)
                    logger.info(f"已清理失败的容器: {container_id}")
                except Exception as cleanup_error:
                    logger.error(f"清理容器失败: {cleanup_error}")
            
            # 清理镜像
            if image_tag:
                try:
                    self.client.images.remove(image_tag, force=True)
                    logger.info(f"已清理镜像: {image_tag}")
                except Exception as cleanup_error:
                    logger.error(f"清理镜像失败: {cleanup_error}")
            
            raise RuntimeError(f"容器创建失败: {str(container_error)}")
            
    except Exception as e:
        logger.error(f"创建HTML游戏服务器容器失败: {e}")
        raise
```

### 3. Dart客户端修复 (mobile_app/universal_game_client/lib/models/game_server_instance.dart)

#### 修复 3.1: 改进fromJson方法的类型安全

**当前问题**:
```dart
factory GameServerInstance.fromJson(Map<String, dynamic> json) {
    return GameServerInstance(
      description: json['description'] as String? ?? '',  // 可能为null
      containerId: json['container_id'] as String? ?? '',  // 可能为null
      // ...
    );
}
```

**修复方案**:
```dart
factory GameServerInstance.fromJson(Map<String, dynamic> json) {
    // 安全地提取字段，确保类型正确
    final description = json['description'];
    final containerId = json['container_id'];
    
    return GameServerInstance(
      serverId: (json['server_id'] ?? '').toString(),
      name: (json['name'] ?? '').toString(),
      description: description is String ? description : (description?.toString() ?? ''),
      status: (json['status'] ?? 'unknown').toString(),
      containerId: containerId is String ? containerId : (containerId?.toString() ?? ''),
      port: (json['port'] as int?) ?? 0,
      createdAt: _parseDateTime(json['created_at']),
      updatedAt: _parseDateTime(json['updated_at']),
      resourceUsage: (json['resource_usage'] as Map<String, dynamic>?) ?? {},
      logs: _parseLogsList(json['logs']),
    );
}

static DateTime _parseDateTime(dynamic value) {
    if (value is String) {
      try {
        return DateTime.parse(value);
      } catch (e) {
        return DateTime.now();
      }
    }
    return DateTime.now();
}

static List<String> _parseLogsList(dynamic value) {
    if (value is List) {
      return value.whereType<String>().toList();
    }
    return [];
}
```

## 数据模型

### 修复后的GameServerInstance模型

```python
# 后端 (Python)
class GameServerInstance(BaseModel):
    server_id: str
    name: str
    description: str = Field(default="", max_length=500)  # 可选，默认为空
    status: str
    container_id: Optional[str] = Field(default="")  # 确保不为null
    port: Optional[int] = Field(default=0)  # 确保不为null
    created_at: str
    updated_at: str
    resource_usage: Dict[str, Any] = Field(default_factory=dict)
    logs: List[str] = Field(default_factory=list)
```

```dart
// 前端 (Dart)
class GameServerInstance {
  final String serverId;
  final String name;
  final String description;  // 可以为空字符串，但不为null
  final String status;
  final String containerId;  // 可以为空字符串，但不为null
  final int port;  // 可以为0，但不为null
  // ...
}
```

## 正确性属性

### 属性 1: Description字段类型安全
*对于任何GameServerInstance对象，description字段应该始终是有效的String类型，不为null*

**验证: 需求 1.4, 2.2**

### 属性 2: 端口唯一性
*对于任何两个不同的运行中的容器，它们的端口映射应该不同*

**验证: 需求 3.2, 3.4**

### 属性 3: 容器创建原子性
*如果容器创建失败，所有相关资源（镜像、容器）应该被清理*

**验证: 需求 3.3, 3.6**

### 属性 4: 容器状态一致性
*容器的报告状态应该与Docker实际状态一致*

**验证: 需求 3.5**

## 错误处理

### 后端错误处理

1. **Description为空**: 接受并使用默认值
2. **端口分配失败**: 返回503错误，提示资源不足
3. **镜像构建失败**: 清理镜像，返回400错误
4. **容器启动失败**: 清理容器和镜像，返回500错误

### 前端错误处理

1. **类型转换失败**: 使用默认值而不是抛出异常
2. **null值处理**: 所有字段都有默认值
3. **解析失败**: 记录错误但继续处理

## 测试策略

### 单元测试

1. **Description字段测试**
   - 测试空Description是否被接受
   - 测试Description为null时的处理
   - 测试Description在Dart中的解析

2. **端口分配测试**
   - 测试多次调用_find_available_port返回不同端口
   - 测试端口冲突检测
   - 测试端口范围限制

3. **容器创建测试**
   - 测试成功创建容器
   - 测试创建失败时的清理
   - 测试多个容器的独立性

### 集成测试

1. **完整上传流程**
   - 上传游戏（带Description）
   - 上传游戏（不带Description）
   - 验证容器创建和运行

2. **多次上传测试**
   - 上传第一个游戏
   - 上传第二个游戏
   - 验证两个容器都正常运行
   - 验证端口不同

3. **错误恢复测试**
   - 模拟容器创建失败
   - 验证资源被清理
   - 验证可以继续上传其他游戏

# HTML游戏上传功能 - Bug修复需求文档

## 介绍

本文档定义了HTML游戏上传功能中发现的三个关键问题的修复需求。这些问题影响了用户上传游戏文件、创建容器和管理多个游戏服务器的能力。

## 术语表

- **Description字段**: 游戏描述信息，用户在上传时填写
- **Type_Cast_Error**: Dart中的类型转换错误，通常发生在null值被强制转换为非null类型时
- **Container_Lifecycle**: 容器的完整生命周期，包括创建、启动、运行和清理
- **Port_Allocation**: 为每个新容器分配唯一的端口号
- **Game_Server_Factory**: 负责处理游戏文件上传和容器创建的后端服务

## 需求

### 需求 1: 移除Description字段的强制要求

**用户故事:** 作为游戏开发者，我希望能够在不填写Description的情况下上传游戏，以便快速测试和迭代。

#### 验收标准

1. WHEN 用户上传HTML游戏文件但不填写Description时 THEN Game_Server_Factory SHALL 接受请求并使用默认或空值
2. WHEN Description字段为空时 THEN 系统 SHALL 不返回验证错误
3. WHEN 用户查看服务器详情时 THEN Universal_Client SHALL 正确显示空的Description而不崩溃
4. WHEN 返回GameServerInstance时 THEN description字段 SHALL 始终是有效的String类型（可以为空字符串）

### 需求 2: 修复类型转换错误

**用户故事:** 作为系统用户，我希望上传成功后不会出现类型转换错误，以便能够正常使用上传的游戏。

#### 验收标准

1. WHEN 上传HTML游戏文件成功时 THEN 后端 SHALL 返回有效的JSON响应，所有字段都有正确的类型
2. WHEN 返回GameServerInstance数据时 THEN 所有String类型字段 SHALL 不为null
3. WHEN Dart客户端解析响应时 THEN 类型转换 SHALL 成功，不抛出"type 'Null' is not a subtype of type 'String'"错误
4. WHEN 字段值可能为null时 THEN 后端 SHALL 提供默认值而不是null

### 需求 3: 修复多次上传容器管理问题

**用户故事:** 作为游戏开发者，我希望能够多次上传不同的游戏，每次都能创建新的正常运行的容器，以便管理多个游戏服务器。

#### 验收标准

1. WHEN 用户第一次上传游戏时 THEN Game_Server_Factory SHALL 创建Docker容器并分配唯一的端口
2. WHEN 用户第二次上传游戏时 THEN Game_Server_Factory SHALL 创建新的Docker容器并分配不同的端口（不是8082）
3. WHEN 容器启动失败时 THEN Game_Server_Factory SHALL 自动清理已创建的容器和相关资源
4. WHEN 多个容器同时运行时 THEN 每个容器 SHALL 有唯一的端口映射和正确的运行状态
5. WHEN 查询容器状态时 THEN 系统 SHALL 准确报告每个容器的运行状态（running、stopped、error）
6. WHEN 容器创建过程中发生错误时 THEN 系统 SHALL 记录详细的错误信息并清理部分创建的资源

## 问题分析

### 问题 1: Description字段强制要求
- **位置**: `game_server_factory/main.py` - `HTMLGameUploadRequest` 模型
- **原因**: description字段定义为必填（`...`），但UI标签显示为"(optional)"
- **影响**: 用户无法在不填写Description的情况下上传游戏

### 问题 2: 类型转换错误
- **位置**: `mobile_app/universal_game_client/lib/models/game_server_instance.dart` - `fromJson`方法
- **原因**: 后端返回的某些字段可能为null，但Dart模型期望String类型
- **影响**: 上传成功后应用崩溃，显示"type 'Null' is not a subtype of type 'String' in type cast"

### 问题 3: 多次上传容器管理
- **位置**: `game_server_factory/docker_manager.py` - `_find_available_port`方法和容器创建逻辑
- **原因**: 
  - 端口分配逻辑可能存在竞态条件
  - 容器启动失败时没有正确的清理机制
  - 可能存在端口重用或绑定问题
- **影响**: 第二次及以后的上传创建的容器无法正常运行，所有容器都使用8082:8080端口

## 修复优先级

1. **高优先级**: 问题 1 - 移除Description强制要求（快速修复）
2. **高优先级**: 问题 2 - 修复类型转换错误（影响用户体验）
3. **高优先级**: 问题 3 - 修复容器管理问题（影响核心功能）

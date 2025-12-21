# 实现计划：测试目录重组

## 概述

本实现计划将分散在各个模块中的测试文件集中到 `TEST` 目录，并确保所有测试能够正确执行。计划分为五个主要阶段：验证、路径映射、脚本更新、目录清理和文档更新。

## 任务列表

- [x] 1. 验证 TEST 目录测试执行
  - [x] 1.1 检查 TEST 目录结构完整性
    - 验证 TEST 目录下所有模块的子目录存在
    - 验证 unit/integration/property 目录结构
    - _需求: 1.1_

  - [x] 1.2 运行 game_server_factory 测试
    - 从 TEST/game_server_factory 目录运行所有测试
    - 验证测试执行成功
    - 记录测试结果
    - _需求: 1.1, 1.2, 1.3_

  - [x] 1.3 运行 matchmaker_service 测试
    - 从 TEST/matchmaker_service 目录运行所有测试
    - 验证测试执行成功
    - 记录测试结果
    - _需求: 1.1, 1.2, 1.3_

  - [x] 1.4 运行 game_server_template 测试
    - 从 TEST/game_server_template 目录运行所有测试
    - 验证测试执行成功
    - 记录测试结果
    - _需求: 1.1, 1.2, 1.3_

  - [x] 1.5 运行 mobile_app 测试
    - 从 TEST/mobile_app 目录运行所有测试
    - 验证测试执行成功
    - 记录测试结果
    - _需求: 1.1, 1.2, 1.3_

  - [x] 1.6 编写测试执行验证脚本
    - **属性 1: 测试文件完整性**
    - **验证: 需求 1.1**
    - 创建脚本验证 TEST 目录中的文件数量与原有目录一致

  - [x] 1.7 Checkpoint - 验证所有 TEST 目录测试通过
    - 确保所有测试执行成功，如有问题请提出

- [x] 2. 验证路径映射正确性
  - [x] 2.1 分析 game_server_factory 测试的导入路径
    - 检查所有 import 语句
    - 验证相对路径是否正确
    - 记录需要调整的路径
    - _需求: 2.1, 2.2_

  - [x] 2.2 分析 matchmaker_service 测试的导入路径
    - 检查所有 import 语句
    - 验证相对路径是否正确
    - 记录需要调整的路径
    - _需求: 2.1, 2.2_

  - [x] 2.3 分析 game_server_template 测试的导入路径
    - 检查所有 import 语句
    - 验证相对路径是否正确
    - 记录需要调整的路径
    - _需求: 2.1, 2.2_

  - [x] 2.4 分析 mobile_app 测试的导入路径
    - 检查所有 import 语句
    - 验证相对路径是否正确
    - 记录需要调整的路径
    - _需求: 2.1, 2.2_

  - [x] 2.5 创建或更新 conftest.py 配置
    - 为 Python 测试配置 Python path
    - 支持从 TEST 目录运行测试
    - _需求: 2.1, 2.3_

  - [x] 2.6 编写路径映射验证脚本
    - **属性 3: 路径映射正确性**
    - **验证: 需求 2.1, 2.2, 2.3, 2.4**
    - 创建脚本验证所有导入都能正确解析

  - [x] 2.7 Checkpoint - 验证所有路径映射正确
    - 确保所有测试文件能够正确访问源代码，如有问题请提出

- [x] 3. 更新测试执行脚本
  - [x] 3.1 更新 run_all_tests.py 脚本
    - 修改测试路径以指向 TEST 目录
    - 更新 game_server_factory 测试命令
    - 更新 matchmaker_service 测试命令
    - 更新 game_server_template 测试命令
    - 更新 flutter_client 测试命令
    - _需求: 4.1, 4.2_

  - [x] 3.2 更新 TEST/scripts/run_all_tests.sh 脚本
    - 修改脚本以从 TEST 目录运行测试
    - 更新日志输出路径
    - _需求: 4.1, 4.2_

  - [x] 3.3 更新 TEST/scripts/run_component_tests.sh 脚本
    - 修改脚本以支持模块特定的测试
    - 支持 unit/integration/property 测试类型
    - _需求: 4.1, 4.2_

  - [x] 3.4 编写脚本执行一致性测试
    - **属性 5: 脚本执行一致性**
    - **验证: 需求 4.1, 4.2, 4.3, 4.4**
    - 创建脚本验证不同测试脚本的结果一致

  - [x] 3.5 Checkpoint - 验证所有脚本执行成功
    - 确保所有测试脚本能够正确执行，如有问题请提出

- [x] 4. 清理原有模块测试目录
  - [x] 4.1 创建清理验证脚本
    - 检查 TEST 目录中是否存在对应的测试文件
    - 生成清理计划
    - _需求: 3.1, 3.2_

  - [x] 4.2 清理 game_server_factory 测试目录
    - 验证 TEST/game_server_factory 中的文件
    - 删除 game_server_factory/tests 中的测试文件
    - 删除空的测试目录
    - _需求: 3.1, 3.2, 3.3_

  - [x] 4.3 清理 matchmaker_service 测试目录
    - 验证 TEST/matchmaker_service 中的文件
    - 删除 matchmaker_service/matchmaker/tests 中的测试文件
    - 删除空的测试目录
    - _需求: 3.1, 3.2, 3.3_

  - [x] 4.4 清理 game_server_template 测试目录
    - 验证 TEST/game_server_template 中的文件
    - 删除 game_server_template/tests 中的测试文件
    - 删除空的测试目录
    - _需求: 3.1, 3.2, 3.3_

  - [x] 4.5 清理 mobile_app 测试目录
    - 验证 TEST/mobile_app 中的文件
    - 删除 mobile_app/universal_game_client/test 中的测试文件
    - 删除空的测试目录
    - _需求: 3.1, 3.2, 3.3_

  - [x] 4.6 编写目录清理验证脚本
    - **属性 4: 目录清理完整性**
    - **验证: 需求 3.1, 3.2, 3.3, 3.4**
    - 创建脚本验证清理后原有目录中不存在已迁移的文件

  - [x] 4.7 验证清理后测试仍能执行
    - 运行所有测试
    - 验证测试通过
    - _需求: 3.4_

  - [x] 4.8 Checkpoint - 验证清理完成且测试通过
    - 确保清理完成且所有测试仍能正确执行，如有问题请提出

- [-] 5. 更新文档
  - [x] 5.1 更新 TEST/README.md
    - 确保目录结构说明准确
    - 更新快速开始指南
    - _需求: 5.1, 5.2_

  - [x] 5.2 更新 TEST/USAGE.md
    - 更新测试执行命令示例
    - 更新模块说明
    - _需求: 5.2, 5.3_

  - [x] 5.3 更新各模块的 README.md
    - 更新 TEST/game_server_factory/README.md
    - 更新 TEST/matchmaker_service/README.md
    - 更新 TEST/game_server_template/README.md
    - 更新 TEST/mobile_app/README.md
    - _需求: 5.1, 5.2_

  - [x] 5.4 更新故障排查指南
    - 添加常见问题
    - 添加解决方案
    - _需求: 5.3_

  - [x] 5.5 Checkpoint - 验证文档完整性
    - 确保所有文档都已更新，如有问题请提出

- [x] 6. 最终验证
  - [x] 6.1 运行完整测试套件
    - 执行 python3 run_all_tests.py
    - 验证所有测试通过
    - _需求: 1.1, 1.2, 1.3, 4.1, 4.2_

  - [x] 6.2 验证向后兼容性
    - 确保原有的测试命令仍可用
    - 验证测试结果一致
    - _需求: 4.1, 4.2_

  - [x] 6.3 生成最终报告
    - 总结所有更改
    - 记录测试结果
    - 提供建议

## 注意事项

- 所有任务都是必需的，以确保全面的实现
- 所有测试必须在迁移后通过
- 清理前必须验证 TEST 目录中存在对应的文件
- 所有更改应该被记录和备份

## 相关文件

- `TEST/README.md` - TEST 目录概览
- `TEST/USAGE.md` - 测试使用说明
- `run_all_tests.py` - 主测试执行脚本
- `TEST/scripts/run_all_tests.sh` - 测试运行脚本
- `TEST/scripts/run_component_tests.sh` - 组件测试脚本

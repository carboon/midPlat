# AI游戏平台 Makefile
# 需求: 7.1, 7.2, 7.4, 7.5

.PHONY: help setup deploy start stop restart status health logs clean validate network build test

# 默认目标
.DEFAULT_GOAL := help

# 环境变量
COMPOSE_FILE := docker-compose.yml
COMPOSE_PROD_FILE := docker-compose.prod.yml
ENV_FILE := .env

# 颜色定义
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# 帮助信息
help: ## 显示帮助信息
	@echo "$(BLUE)AI游戏平台部署管理$(NC)"
	@echo ""
	@echo "$(GREEN)可用命令:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)示例:$(NC)"
	@echo "  make setup     # 初始化环境"
	@echo "  make deploy    # 完整部署"
	@echo "  make health    # 健康检查"
	@echo "  make validate  # 验证部署"

# 环境设置
setup: ## 初始化环境和配置
	@echo "$(BLUE)初始化环境...$(NC)"
	@if [ ! -f $(ENV_FILE) ]; then \
		cp .env.example $(ENV_FILE); \
		echo "$(GREEN)已创建 .env 文件，请根据需要修改配置$(NC)"; \
	fi
	@chmod +x scripts/*.sh
	@./scripts/validate-env.sh validate
	@./scripts/setup-network.sh setup
	@echo "$(GREEN)环境初始化完成$(NC)"

# 环境验证
env-validate: ## 验证环境配置
	@./scripts/validate-env.sh validate

env-fix: ## 修复常见环境配置问题
	@./scripts/validate-env.sh fix

# 构建镜像
build: ## 构建所有Docker镜像
	@echo "$(BLUE)构建Docker镜像...$(NC)"
	@./scripts/build-images.sh build
	@echo "$(GREEN)镜像构建完成$(NC)"

# 并行构建镜像
build-parallel: ## 并行构建所有Docker镜像
	@echo "$(BLUE)并行构建Docker镜像...$(NC)"
	@PARALLEL_BUILD=true ./scripts/build-images.sh build
	@echo "$(GREEN)并行镜像构建完成$(NC)"

# 清理构建缓存
build-clean: ## 清理Docker构建缓存
	@./scripts/build-images.sh clean

# 完整部署
deploy: setup build ## 完整部署系统
	@echo "$(BLUE)开始部署AI游戏平台...$(NC)"
	@./scripts/deploy.sh deploy
	@echo "$(GREEN)部署完成$(NC)"

# 部署包含示例服务器
deploy-example: setup build ## 部署包含示例游戏服务器
	@echo "$(BLUE)部署包含示例服务器...$(NC)"
	@./scripts/deploy.sh deploy example
	@echo "$(GREEN)部署完成$(NC)"

# 生产环境部署
deploy-prod: setup build ## 生产环境部署
	@echo "$(BLUE)生产环境部署...$(NC)"
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "$(RED)错误: .env 文件不存在$(NC)"; \
		exit 1; \
	fi
	@docker-compose -f $(COMPOSE_FILE) -f $(COMPOSE_PROD_FILE) up -d
	@echo "$(GREEN)生产环境部署完成$(NC)"

# 启动服务
start: ## 启动所有服务
	@echo "$(BLUE)启动服务...$(NC)"
	@docker-compose up -d
	@./scripts/deploy.sh start
	@echo "$(GREEN)服务启动完成$(NC)"

# 停止服务
stop: ## 停止所有服务
	@echo "$(BLUE)停止服务...$(NC)"
	@docker-compose down
	@echo "$(GREEN)服务已停止$(NC)"

# 重启服务
restart: ## 重启所有服务
	@echo "$(BLUE)重启服务...$(NC)"
	@docker-compose restart
	@./scripts/health-check.sh quick
	@echo "$(GREEN)服务重启完成$(NC)"

# 查看状态
status: ## 查看服务状态
	@echo "$(BLUE)服务状态:$(NC)"
	@docker-compose ps
	@echo ""
	@./scripts/health-check.sh quick

# 健康检查
health: ## 运行健康检查
	@echo "$(BLUE)运行健康检查...$(NC)"
	@./scripts/health-check.sh comprehensive

# 快速健康检查
health-quick: ## 快速健康检查
	@./scripts/health-check.sh quick

# 监控模式
monitor: ## 启动监控模式
	@echo "$(BLUE)启动监控模式（按Ctrl+C退出）...$(NC)"
	@./scripts/health-check.sh monitor 30

# 查看日志
logs: ## 查看所有服务日志
	@docker-compose logs -f

# 查看特定服务日志
logs-matchmaker: ## 查看撮合服务日志
	@docker-compose logs -f matchmaker

logs-factory: ## 查看游戏服务器工厂日志
	@docker-compose logs -f game-server-factory

logs-example: ## 查看示例游戏服务器日志
	@docker-compose logs -f example-game-server

# 验证部署
validate: ## 验证部署配置和功能
	@echo "$(BLUE)验证部署...$(NC)"
	@./scripts/validate-deployment.sh comprehensive

# 验证网络配置
validate-network: ## 验证网络配置
	@./scripts/setup-network.sh verify

# 网络管理
network-setup: ## 设置网络配置
	@./scripts/setup-network.sh setup

network-info: ## 显示网络信息
	@./scripts/setup-network.sh info

network-reset: ## 重置网络配置
	@./scripts/setup-network.sh reset

network-init: ## 初始化Docker网络
	@./scripts/init-docker-network.sh init

# 容器监控
containers: ## 显示动态容器概览
	@./scripts/monitor-containers.sh overview

containers-monitor: ## 启动容器监控模式
	@./scripts/monitor-containers.sh monitor

containers-cleanup: ## 清理停止的动态容器
	@./scripts/monitor-containers.sh cleanup

# 测试
test: ## 运行集成测试
	@echo "$(BLUE)运行集成测试...$(NC)"
	@python3 test_integration.py

test-e2e: ## 运行端到端测试
	@echo "$(BLUE)运行端到端测试...$(NC)"
	@python3 test_end_to_end_integration.py

# 清理
clean: ## 清理所有资源
	@echo "$(BLUE)清理资源...$(NC)"
	@docker-compose down -v
	@docker system prune -f
	@docker volume prune -f
	@./scripts/setup-network.sh cleanup
	@echo "$(GREEN)清理完成$(NC)"

# 深度清理
clean-all: ## 深度清理（包括镜像）
	@echo "$(BLUE)深度清理...$(NC)"
	@docker-compose down -v --rmi all
	@docker system prune -a -f
	@docker volume prune -f
	@./scripts/setup-network.sh cleanup
	@echo "$(GREEN)深度清理完成$(NC)"

# 备份
backup: ## 备份配置和数据
	@echo "$(BLUE)备份配置和数据...$(NC)"
	@mkdir -p backups
	@cp $(ENV_FILE) backups/env-$(shell date +%Y%m%d-%H%M%S).backup
	@cp $(COMPOSE_FILE) backups/compose-$(shell date +%Y%m%d-%H%M%S).backup
	@docker run --rm -v factory_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/factory-data-$(shell date +%Y%m%d-%H%M%S).tar.gz -C /data .
	@echo "$(GREEN)备份完成$(NC)"

# 更新
update: ## 更新服务镜像
	@echo "$(BLUE)更新服务镜像...$(NC)"
	@docker-compose pull
	@docker-compose up -d
	@./scripts/health-check.sh quick
	@echo "$(GREEN)更新完成$(NC)"

# 开发环境
dev: ## 启动开发环境
	@echo "$(BLUE)启动开发环境...$(NC)"
	@make setup
	@make build
	@make start
	@make health-quick
	@echo "$(GREEN)开发环境就绪$(NC)"

# 生产环境检查
prod-check: ## 生产环境检查
	@echo "$(BLUE)生产环境检查...$(NC)"
	@if grep -q "DEBUG=true" $(ENV_FILE); then \
		echo "$(RED)警告: 生产环境中DEBUG仍为true$(NC)"; \
	fi
	@if grep -q "ALLOWED_ORIGINS=\*" $(ENV_FILE); then \
		echo "$(RED)警告: 生产环境中CORS设置为允许所有来源$(NC)"; \
	fi
	@./scripts/validate-deployment.sh comprehensive

# 性能测试
perf: ## 运行性能测试
	@echo "$(BLUE)运行性能测试...$(NC)"
	@./scripts/validate-deployment.sh performance

# 生成报告
report: ## 生成系统报告
	@echo "$(BLUE)生成系统报告...$(NC)"
	@./scripts/health-check.sh report
	@./scripts/validate-deployment.sh report
	@echo "$(GREEN)报告生成完成$(NC)"

# 调试模式
debug: ## 启动调试模式
	@echo "$(BLUE)启动调试模式...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) -f docker-compose.debug.yml up -d
	@echo "$(GREEN)调试模式启动完成$(NC)"

# 配置检查
config-check: ## 检查配置文件
	@echo "$(BLUE)检查配置文件...$(NC)"
	@docker-compose config
	@echo "$(GREEN)配置文件检查完成$(NC)"

# 端口检查
port-check: ## 检查端口占用
	@echo "$(BLUE)检查端口占用...$(NC)"
	@echo "撮合服务端口 (8000):"
	@lsof -i :8000 || echo "端口8000未被占用"
	@echo "游戏服务器工厂端口 (8080):"
	@lsof -i :8080 || echo "端口8080未被占用"
	@echo "示例游戏服务器端口 (8081):"
	@lsof -i :8081 || echo "端口8081未被占用"
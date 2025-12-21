#!/bin/bash

# AI游戏平台部署脚本
# 需求: 7.1, 7.2, 7.4, 7.5

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查Docker守护进程
    if ! docker info &> /dev/null; then
        log_error "Docker守护进程未运行，请启动Docker"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 验证环境配置
validate_environment() {
    log_info "验证环境配置..."
    
    if [ ! -f ".env" ]; then
        log_warning ".env文件不存在，从模板创建..."
        cp .env.example .env
        log_info "请编辑.env文件配置您的环境变量"
    fi
    
    # 验证必要的环境变量
    source .env
    
    required_vars=("ENVIRONMENT" "MATCHMAKER_PORT" "FACTORY_PORT" "BASE_PORT")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "缺少必要的环境变量: ${missing_vars[*]}"
        log_error "请检查.env文件配置"
        exit 1
    fi
    
    log_success "环境配置验证通过"
}

# 创建网络
create_network() {
    log_info "创建Docker网络..."
    
    if ! docker network ls | grep -q "game-network"; then
        docker network create \
            --driver bridge \
            --subnet=172.20.0.0/16 \
            --ip-range=172.20.240.0/20 \
            game-network
        log_success "Docker网络创建成功"
    else
        log_info "Docker网络已存在"
    fi
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    
    # 构建撮合服务
    log_info "构建撮合服务镜像..."
    docker-compose build matchmaker
    
    # 构建游戏服务器工厂
    log_info "构建游戏服务器工厂镜像..."
    docker-compose build game-server-factory
    
    # 构建游戏服务器模板
    log_info "构建游戏服务器模板镜像..."
    docker-compose build example-game-server
    
    log_success "所有镜像构建完成"
}

# 启动服务
start_services() {
    local profile=${1:-""}
    
    log_info "启动服务..."
    
    if [ -n "$profile" ]; then
        log_info "使用配置文件: $profile"
        docker-compose --profile "$profile" up -d
    else
        docker-compose up -d
    fi
    
    log_success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    local max_attempts=30
    local attempt=1
    
    # 等待撮合服务
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:${MATCHMAKER_PORT:-8000}/health &> /dev/null; then
            log_success "撮合服务就绪"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "撮合服务启动超时"
            exit 1
        fi
        
        log_info "等待撮合服务启动... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    # 等待游戏服务器工厂
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:${FACTORY_PORT:-8080}/health &> /dev/null; then
            log_success "游戏服务器工厂就绪"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "游戏服务器工厂启动超时"
            exit 1
        fi
        
        log_info "等待游戏服务器工厂启动... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_success "所有服务就绪"
}

# 运行健康检查
health_check() {
    log_info "运行健康检查..."
    
    # 检查撮合服务
    if ! curl -f http://localhost:${MATCHMAKER_PORT:-8000}/health &> /dev/null; then
        log_error "撮合服务健康检查失败"
        return 1
    fi
    
    # 检查游戏服务器工厂
    if ! curl -f http://localhost:${FACTORY_PORT:-8080}/health &> /dev/null; then
        log_error "游戏服务器工厂健康检查失败"
        return 1
    fi
    
    # 检查服务间通信
    if ! curl -f http://localhost:${FACTORY_PORT:-8080}/servers &> /dev/null; then
        log_error "服务间通信检查失败"
        return 1
    fi
    
    log_success "健康检查通过"
}

# 显示服务状态
show_status() {
    log_info "服务状态:"
    docker-compose ps
    
    echo ""
    log_info "服务端点:"
    echo "  撮合服务: http://localhost:${MATCHMAKER_PORT:-8000}"
    echo "  游戏服务器工厂: http://localhost:${FACTORY_PORT:-8080}"
    echo "  API文档: http://localhost:${FACTORY_PORT:-8080}/docs"
    
    echo ""
    log_info "健康检查端点:"
    echo "  撮合服务: http://localhost:${MATCHMAKER_PORT:-8000}/health"
    echo "  游戏服务器工厂: http://localhost:${FACTORY_PORT:-8080}/health"
}

# 清理资源
cleanup() {
    log_info "清理资源..."
    
    # 停止服务
    docker-compose down
    
    # 清理未使用的镜像
    docker image prune -f
    
    # 清理未使用的卷
    docker volume prune -f
    
    log_success "资源清理完成"
}

# 主函数
main() {
    local command=${1:-"deploy"}
    local profile=${2:-""}
    
    case $command in
        "deploy")
            log_info "开始部署AI游戏平台..."
            check_dependencies
            validate_environment
            create_network
            build_images
            start_services "$profile"
            wait_for_services
            health_check
            show_status
            log_success "部署完成!"
            ;;
        "start")
            log_info "启动服务..."
            start_services "$profile"
            wait_for_services
            health_check
            show_status
            ;;
        "stop")
            log_info "停止服务..."
            docker-compose down
            log_success "服务已停止"
            ;;
        "restart")
            log_info "重启服务..."
            docker-compose restart
            wait_for_services
            health_check
            show_status
            ;;
        "status")
            show_status
            ;;
        "health")
            health_check
            ;;
        "cleanup")
            cleanup
            ;;
        "logs")
            docker-compose logs -f
            ;;
        *)
            echo "用法: $0 {deploy|start|stop|restart|status|health|cleanup|logs} [profile]"
            echo ""
            echo "命令:"
            echo "  deploy   - 完整部署（默认）"
            echo "  start    - 启动服务"
            echo "  stop     - 停止服务"
            echo "  restart  - 重启服务"
            echo "  status   - 显示服务状态"
            echo "  health   - 运行健康检查"
            echo "  cleanup  - 清理资源"
            echo "  logs     - 查看日志"
            echo ""
            echo "配置文件:"
            echo "  example  - 包含示例游戏服务器"
            echo ""
            echo "示例:"
            echo "  $0 deploy example    # 部署包含示例服务器"
            echo "  $0 start            # 启动基本服务"
            echo "  $0 health           # 运行健康检查"
            exit 1
            ;;
    esac
}

# 脚本入口
main "$@"
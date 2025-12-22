#!/bin/bash

# 通用函数库 - 供其他脚本引用
# 包含 Docker Compose 兼容性检测和通用工具函数

# 颜色定义
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export NC='\033[0m' # No Color

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

# 自动检测 Docker Compose 命令（兼容新旧版本）
# 返回可用的 Docker Compose 命令
detect_docker_compose() {
    if command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    elif command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    else
        echo ""
    fi
}

# 获取 Docker Compose 命令
# 如果未设置 DOCKER_COMPOSE 变量，则自动检测
get_docker_compose_cmd() {
    if [ -z "$DOCKER_COMPOSE" ]; then
        DOCKER_COMPOSE=$(detect_docker_compose)
    fi
    
    if [ -z "$DOCKER_COMPOSE" ]; then
        log_error "Docker Compose 未安装"
        log_info "请安装 Docker Desktop 或独立的 docker-compose"
        log_info "  macOS: brew install --cask docker"
        log_info "  Linux: sudo apt-get install docker-compose-plugin"
        return 1
    fi
    
    echo "$DOCKER_COMPOSE"
}

# 执行 Docker Compose 命令
# 用法: run_docker_compose <args...>
run_docker_compose() {
    local cmd
    cmd=$(get_docker_compose_cmd) || return 1
    $cmd "$@"
}

# 检查 Docker 是否运行
check_docker_running() {
    if ! docker info &> /dev/null; then
        log_error "Docker 未运行"
        log_info "请启动 Docker Desktop"
        return 1
    fi
    return 0
}

# 检查容器是否运行
# 用法: is_container_running <container_name>
is_container_running() {
    local container=$1
    docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "$container"
}

# 获取容器名称
# 用法: get_container_name <service_name>
get_container_name() {
    local service=$1
    docker ps --filter "name=$service" --format "{{.Names}}" | head -1
}

# 等待容器就绪
# 用法: wait_for_container <container_name> <max_attempts>
wait_for_container() {
    local container=$1
    local max_attempts=${2:-30}
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if is_container_running "$container"; then
            return 0
        fi
        
        sleep 2
        ((attempt++))
    done
    
    return 1
}

# 检查端口是否可用
# 用法: is_port_available <port>
is_port_available() {
    local port=$1
    ! lsof -i ":$port" > /dev/null 2>&1
}

# 检查 URL 是否可访问
# 用法: is_url_accessible <url> <timeout>
is_url_accessible() {
    local url=$1
    local timeout=${2:-10}
    curl -f -s --max-time "$timeout" "$url" > /dev/null 2>&1
}

# 导出函数供其他脚本使用
export -f log_info
export -f log_success
export -f log_warning
export -f log_error
export -f detect_docker_compose
export -f get_docker_compose_cmd
export -f run_docker_compose
export -f check_docker_running
export -f is_container_running
export -f get_container_name
export -f wait_for_container
export -f is_port_available
export -f is_url_accessible

#!/bin/bash

# Docker网络初始化脚本
# 用于确保动态容器创建时的网络配置正确
# 需求: 7.1, 7.4

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

# 网络配置
NETWORK_NAME="game-network"
SUBNET="172.21.0.0/16"
IP_RANGE="172.21.240.0/20"
GATEWAY="172.21.0.1"

# 检查Docker是否运行
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker守护进程未运行"
        exit 1
    fi
}

# 创建或验证网络
ensure_network() {
    log_info "确保游戏网络存在..."
    
    if docker network ls | grep -q "$NETWORK_NAME"; then
        log_info "网络 $NETWORK_NAME 已存在，验证配置..."
        
        # 验证网络配置
        local current_subnet
        current_subnet=$(docker network inspect "$NETWORK_NAME" --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null)
        
        if [ "$current_subnet" = "$SUBNET" ]; then
            log_success "网络配置正确"
        else
            log_warning "网络配置不匹配，当前: $current_subnet，期望: $SUBNET"
            log_info "重新创建网络..."
            
            # 删除现有网络（如果没有容器使用）
            if docker network rm "$NETWORK_NAME" 2>/dev/null; then
                log_info "已删除现有网络"
            else
                log_warning "无法删除现有网络，可能有容器正在使用"
                return 0
            fi
        fi
    fi
    
    # 创建网络（如果不存在）
    if ! docker network ls | grep -q "$NETWORK_NAME"; then
        log_info "创建游戏网络..."
        
        docker network create \
            --driver bridge \
            --subnet="$SUBNET" \
            --ip-range="$IP_RANGE" \
            --gateway="$GATEWAY" \
            --opt com.docker.network.bridge.name=game-bridge \
            --opt com.docker.network.bridge.enable_icc=true \
            --opt com.docker.network.bridge.enable_ip_masquerade=true \
            --opt com.docker.network.driver.mtu=1500 \
            --label "ai-game-platform=main" \
            --label "managed-by=ai-game-platform" \
            "$NETWORK_NAME"
        
        log_success "游戏网络创建成功"
    fi
}

# 配置动态容器网络策略
configure_dynamic_policies() {
    log_info "配置动态容器网络策略..."
    
    # 设置iptables规则以允许动态容器间通信
    # 这些规则确保动态创建的游戏服务器容器可以相互通信
    
    # 允许game-network内的所有通信
    if command -v iptables > /dev/null 2>&1; then
        # 检查是否已有规则
        if ! iptables -C DOCKER-USER -s "$SUBNET" -d "$SUBNET" -j ACCEPT 2>/dev/null; then
            iptables -I DOCKER-USER -s "$SUBNET" -d "$SUBNET" -j ACCEPT 2>/dev/null || log_warning "无法设置iptables规则（可能需要root权限）"
        fi
    fi
    
    log_success "动态容器网络策略配置完成"
}

# 验证网络连通性
verify_network() {
    log_info "验证网络连通性..."
    
    # 创建测试容器验证网络
    local test_container="network-test-$$"
    
    if docker run -d --name "$test_container" --network "$NETWORK_NAME" alpine:latest sleep 10 > /dev/null 2>&1; then
        # 测试DNS解析
        if docker exec "$test_container" nslookup google.com > /dev/null 2>&1; then
            log_success "网络连通性正常"
        else
            log_warning "外部网络连通性可能存在问题"
        fi
        
        # 清理测试容器
        docker rm -f "$test_container" > /dev/null 2>&1
    else
        log_error "网络验证失败"
        return 1
    fi
}

# 显示网络信息
show_network_info() {
    log_info "网络配置信息:"
    echo ""
    
    # 基本信息
    echo "网络名称: $NETWORK_NAME"
    echo "子网: $SUBNET"
    echo "IP范围: $IP_RANGE"
    echo "网关: $GATEWAY"
    echo ""
    
    # 详细信息
    if command -v jq > /dev/null 2>&1; then
        docker network inspect "$NETWORK_NAME" --format '{{json .}}' | jq '{
            Name: .Name,
            Driver: .Driver,
            Subnet: .IPAM.Config[0].Subnet,
            Gateway: .IPAM.Config[0].Gateway,
            IPRange: .IPAM.Config[0].IPRange,
            Containers: (.Containers | length)
        }'
    else
        docker network inspect "$NETWORK_NAME" --format 'Name: {{.Name}}
Driver: {{.Driver}}
Subnet: {{range .IPAM.Config}}{{.Subnet}}{{end}}
Gateway: {{range .IPAM.Config}}{{.Gateway}}{{end}}
Connected Containers: {{len .Containers}}'
    fi
}

# 清理网络
cleanup_network() {
    log_info "清理网络配置..."
    
    # 停止所有相关容器
    docker ps -q --filter "network=$NETWORK_NAME" | xargs -r docker stop > /dev/null 2>&1 || true
    
    # 删除网络
    if docker network ls | grep -q "$NETWORK_NAME"; then
        docker network rm "$NETWORK_NAME" > /dev/null 2>&1 || log_warning "无法删除网络（可能有容器正在使用）"
    fi
    
    log_success "网络清理完成"
}

# 主函数
main() {
    local command=${1:-"init"}
    
    case $command in
        "init")
            log_info "初始化Docker网络配置..."
            check_docker
            ensure_network
            configure_dynamic_policies
            verify_network
            show_network_info
            log_success "网络初始化完成!"
            ;;
        "verify")
            check_docker
            verify_network
            ;;
        "info")
            show_network_info
            ;;
        "cleanup")
            cleanup_network
            ;;
        *)
            echo "用法: $0 {init|verify|info|cleanup}"
            echo ""
            echo "命令:"
            echo "  init    - 初始化网络配置（默认）"
            echo "  verify  - 验证网络连通性"
            echo "  info    - 显示网络信息"
            echo "  cleanup - 清理网络配置"
            echo ""
            echo "示例:"
            echo "  $0 init     # 初始化网络"
            echo "  $0 verify   # 验证网络"
            echo "  $0 info     # 查看网络信息"
            exit 1
            ;;
    esac
}

# 脚本入口
main "$@"
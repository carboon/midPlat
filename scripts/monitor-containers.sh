#!/bin/bash

# 动态容器监控脚本
# 用于监控游戏服务器工厂创建的动态容器
# 需求: 7.1, 7.4

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
NETWORK_NAME="game-network"
CONTAINER_PREFIX="game-server-"
MONITOR_INTERVAL=30

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

# 获取动态容器列表
get_dynamic_containers() {
    docker ps -a --filter "network=$NETWORK_NAME" --filter "name=$CONTAINER_PREFIX" --format "{{.Names}}" 2>/dev/null || true
}

# 获取容器状态
get_container_status() {
    local container_name=$1
    docker inspect "$container_name" --format '{{.State.Status}}' 2>/dev/null || echo "not_found"
}

# 获取容器资源使用情况
get_container_resources() {
    local container_name=$1
    docker stats "$container_name" --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" 2>/dev/null || echo "N/A\tN/A\tN/A\tN/A"
}

# 获取容器端口映射
get_container_ports() {
    local container_name=$1
    docker port "$container_name" 2>/dev/null | grep "0.0.0.0" | head -1 | cut -d':' -f2 || echo "N/A"
}

# 获取容器运行时间
get_container_uptime() {
    local container_name=$1
    local started_at
    started_at=$(docker inspect "$container_name" --format '{{.State.StartedAt}}' 2>/dev/null)
    
    if [ -n "$started_at" ] && [ "$started_at" != "0001-01-01T00:00:00Z" ]; then
        local start_timestamp
        start_timestamp=$(date -d "$started_at" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S" "${started_at%.*}" +%s 2>/dev/null || echo "0")
        local current_timestamp
        current_timestamp=$(date +%s)
        local uptime_seconds=$((current_timestamp - start_timestamp))
        
        if [ $uptime_seconds -gt 0 ]; then
            local hours=$((uptime_seconds / 3600))
            local minutes=$(((uptime_seconds % 3600) / 60))
            local seconds=$((uptime_seconds % 60))
            echo "${hours}h ${minutes}m ${seconds}s"
        else
            echo "N/A"
        fi
    else
        echo "N/A"
    fi
}

# 检查容器健康状态
check_container_health() {
    local container_name=$1
    local port
    port=$(get_container_ports "$container_name")
    
    if [ "$port" != "N/A" ]; then
        if curl -f -s --max-time 5 "http://localhost:$port" > /dev/null 2>&1; then
            echo "healthy"
        else
            echo "unhealthy"
        fi
    else
        echo "unknown"
    fi
}

# 显示容器概览
show_containers_overview() {
    log_info "动态游戏服务器容器概览"
    echo ""
    
    local containers
    containers=$(get_dynamic_containers)
    
    if [ -z "$containers" ]; then
        log_info "当前没有动态游戏服务器容器"
        return 0
    fi
    
    # 表头
    printf "%-20s %-10s %-8s %-15s %-10s %-15s\n" "容器名称" "状态" "端口" "运行时间" "健康状态" "CPU/内存"
    printf "%-20s %-10s %-8s %-15s %-10s %-15s\n" "--------------------" "----------" "--------" "---------------" "----------" "---------------"
    
    # 容器信息
    for container in $containers; do
        local status
        local port
        local uptime
        local health
        local resources
        
        status=$(get_container_status "$container")
        port=$(get_container_ports "$container")
        uptime=$(get_container_uptime "$container")
        health=$(check_container_health "$container")
        resources=$(get_container_resources "$container" | tail -1 | awk '{print $1"/"$2}')
        
        # 状态颜色
        case $status in
            "running")
                status="${GREEN}running${NC}"
                ;;
            "exited")
                status="${RED}exited${NC}"
                ;;
            "paused")
                status="${YELLOW}paused${NC}"
                ;;
            *)
                status="${RED}$status${NC}"
                ;;
        esac
        
        # 健康状态颜色
        case $health in
            "healthy")
                health="${GREEN}healthy${NC}"
                ;;
            "unhealthy")
                health="${RED}unhealthy${NC}"
                ;;
            *)
                health="${YELLOW}$health${NC}"
                ;;
        esac
        
        printf "%-30s %-20s %-8s %-15s %-20s %-15s\n" "$container" "$status" "$port" "$uptime" "$health" "$resources"
    done
    
    echo ""
}

# 显示详细容器信息
show_container_details() {
    local container_name=$1
    
    if [ -z "$container_name" ]; then
        log_error "请指定容器名称"
        return 1
    fi
    
    log_info "容器详细信息: $container_name"
    echo ""
    
    # 基本信息
    echo "基本信息:"
    docker inspect "$container_name" --format '  ID: {{.Id}}
  状态: {{.State.Status}}
  创建时间: {{.Created}}
  启动时间: {{.State.StartedAt}}
  镜像: {{.Config.Image}}
  网络: {{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' 2>/dev/null || {
        log_error "容器不存在或无法访问"
        return 1
    }
    
    echo ""
    
    # 端口映射
    echo "端口映射:"
    docker port "$container_name" 2>/dev/null | sed 's/^/  /' || echo "  无端口映射"
    
    echo ""
    
    # 环境变量
    echo "环境变量:"
    docker inspect "$container_name" --format '{{range .Config.Env}}  {{.}}{{"\n"}}{{end}}' 2>/dev/null | head -10
    
    echo ""
    
    # 资源使用
    echo "资源使用:"
    docker stats "$container_name" --no-stream --format "  CPU: {{.CPUPerc}}
  内存: {{.MemUsage}}
  网络: {{.NetIO}}
  磁盘: {{.BlockIO}}" 2>/dev/null || echo "  无法获取资源信息"
    
    echo ""
    
    # 最近日志
    echo "最近日志 (最后10行):"
    docker logs "$container_name" --tail 10 2>/dev/null | sed 's/^/  /' || echo "  无日志"
}

# 清理停止的容器
cleanup_stopped_containers() {
    log_info "清理停止的动态容器..."
    
    local stopped_containers
    stopped_containers=$(docker ps -a --filter "network=$NETWORK_NAME" --filter "name=$CONTAINER_PREFIX" --filter "status=exited" --format "{{.Names}}" 2>/dev/null || true)
    
    if [ -z "$stopped_containers" ]; then
        log_info "没有需要清理的停止容器"
        return 0
    fi
    
    local count=0
    for container in $stopped_containers; do
        log_info "删除停止的容器: $container"
        if docker rm "$container" > /dev/null 2>&1; then
            ((count++))
        else
            log_warning "无法删除容器: $container"
        fi
    done
    
    log_success "已清理 $count 个停止的容器"
}

# 监控模式
monitor_mode() {
    local interval=${1:-$MONITOR_INTERVAL}
    
    log_info "启动容器监控模式，刷新间隔: ${interval}秒"
    log_info "按 Ctrl+C 退出监控"
    echo ""
    
    while true; do
        clear
        echo "==================== 动态容器监控 - $(date) ===================="
        echo ""
        
        show_containers_overview
        
        # 显示网络统计
        local total_containers
        total_containers=$(get_dynamic_containers | wc -l)
        local running_containers
        running_containers=$(docker ps --filter "network=$NETWORK_NAME" --filter "name=$CONTAINER_PREFIX" --format "{{.Names}}" | wc -l)
        
        echo "统计信息:"
        echo "  总容器数: $total_containers"
        echo "  运行中: $running_containers"
        echo "  停止: $((total_containers - running_containers))"
        echo ""
        
        echo "下次刷新: ${interval}秒后"
        sleep "$interval"
    done
}

# 生成监控报告
generate_monitoring_report() {
    local report_file="container-monitoring-$(date +%Y%m%d-%H%M%S).txt"
    
    log_info "生成容器监控报告: $report_file"
    
    {
        echo "AI游戏平台动态容器监控报告"
        echo "生成时间: $(date)"
        echo "========================================"
        echo ""
        
        echo "容器概览:"
        show_containers_overview
        echo ""
        
        echo "网络信息:"
        docker network inspect "$NETWORK_NAME" --format '网络名称: {{.Name}}
驱动: {{.Driver}}
子网: {{range .IPAM.Config}}{{.Subnet}}{{end}}
连接的容器数: {{len .Containers}}'
        echo ""
        
        echo "详细容器信息:"
        local containers
        containers=$(get_dynamic_containers)
        
        for container in $containers; do
            echo "----------------------------------------"
            show_container_details "$container"
        done
        
    } > "$report_file"
    
    log_success "监控报告已生成: $report_file"
}

# 主函数
main() {
    local command=${1:-"overview"}
    local param=${2:-""}
    
    case $command in
        "overview")
            show_containers_overview
            ;;
        "details")
            show_container_details "$param"
            ;;
        "monitor")
            monitor_mode "$param"
            ;;
        "cleanup")
            cleanup_stopped_containers
            ;;
        "report")
            generate_monitoring_report
            ;;
        *)
            echo "用法: $0 {overview|details|monitor|cleanup|report} [参数]"
            echo ""
            echo "命令:"
            echo "  overview  - 显示容器概览（默认）"
            echo "  details   - 显示容器详细信息 [容器名称]"
            echo "  monitor   - 监控模式 [刷新间隔秒数]"
            echo "  cleanup   - 清理停止的容器"
            echo "  report    - 生成监控报告"
            echo ""
            echo "示例:"
            echo "  $0 overview                    # 显示概览"
            echo "  $0 details game-server-123     # 显示详细信息"
            echo "  $0 monitor 60                  # 每60秒监控一次"
            echo "  $0 cleanup                     # 清理停止的容器"
            echo "  $0 report                      # 生成报告"
            exit 1
            ;;
    esac
}

# 脚本入口
main "$@"
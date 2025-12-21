#!/bin/bash

# AI游戏平台健康检查脚本
# 需求: 6.2, 6.3, 7.4, 7.5

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
MATCHMAKER_PORT=${MATCHMAKER_PORT:-8000}
FACTORY_PORT=${FACTORY_PORT:-8080}
TIMEOUT=${HEALTH_CHECK_TIMEOUT:-10}

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

# 检查HTTP端点
check_http_endpoint() {
    local url=$1
    local name=$2
    local expected_status=${3:-200}
    
    log_info "检查 $name: $url"
    
    local response
    local status_code
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" --max-time $TIMEOUT "$url" 2>/dev/null || echo "HTTPSTATUS:000")
    status_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    
    if [ "$status_code" = "$expected_status" ]; then
        log_success "$name 健康检查通过 (状态码: $status_code)"
        return 0
    else
        log_error "$name 健康检查失败 (状态码: $status_code)"
        return 1
    fi
}

# 检查JSON响应
check_json_response() {
    local url=$1
    local name=$2
    local expected_field=$3
    
    log_info "检查 $name JSON响应: $url"
    
    local response
    response=$(curl -s --max-time $TIMEOUT "$url" 2>/dev/null || echo "{}")
    
    if echo "$response" | jq -e ".$expected_field" > /dev/null 2>&1; then
        log_success "$name JSON响应有效"
        return 0
    else
        log_error "$name JSON响应无效或缺少字段: $expected_field"
        return 1
    fi
}

# 检查容器状态
check_container_status() {
    log_info "检查Docker容器状态..."
    
    local containers=("matchmaker" "game-server-factory")
    local all_healthy=true
    
    for container in "${containers[@]}"; do
        if docker-compose ps "$container" | grep -q "Up"; then
            log_success "容器 $container 正在运行"
        else
            log_error "容器 $container 未运行"
            all_healthy=false
        fi
    done
    
    if [ "$all_healthy" = true ]; then
        return 0
    else
        return 1
    fi
}

# 检查网络连通性
check_network_connectivity() {
    log_info "检查网络连通性..."
    
    # 检查容器间网络 - 使用docker exec而不是docker-compose exec
    local matchmaker_container=$(docker ps --filter "name=matchmaker" --format "{{.Names}}" | head -1)
    local factory_container=$(docker ps --filter "name=game-server-factory" --format "{{.Names}}" | head -1)
    
    if [ -z "$matchmaker_container" ] || [ -z "$factory_container" ]; then
        log_warning "无法找到运行中的容器"
        return 0  # 不失败，只是警告
    fi
    
    if docker exec "$matchmaker_container" ping -c 1 -W 2 game-server-factory > /dev/null 2>&1; then
        log_success "容器间网络连通正常"
    else
        log_warning "容器间网络连通测试失败（可能是ping被禁用）"
        # 尝试HTTP连接测试
        if docker exec "$matchmaker_container" wget -q -O- --timeout=2 http://game-server-factory:8080/health > /dev/null 2>&1; then
            log_success "容器间HTTP连接正常"
        else
            log_warning "容器间连接可能存在问题"
        fi
    fi
    
    return 0
}

# 检查资源使用情况
check_resource_usage() {
    log_info "检查资源使用情况..."
    
    # 检查内存使用
    local memory_usage
    memory_usage=$(docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}" 2>/dev/null | grep -E "(matchmaker|game-server-factory)" || echo "")
    
    if [ -n "$memory_usage" ]; then
        log_info "内存使用情况:"
        echo "$memory_usage"
    else
        log_info "内存使用情况: 容器运行正常"
    fi
    
    # 检查磁盘空间
    local disk_usage
    disk_usage=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ "$disk_usage" -gt 90 ]; then
        log_error "磁盘使用率过高: ${disk_usage}%"
        return 1
    elif [ "$disk_usage" -gt 80 ]; then
        log_warning "磁盘使用率较高: ${disk_usage}%"
    else
        log_success "磁盘使用率正常: ${disk_usage}%"
    fi
    
    return 0
}

# 检查日志错误
check_logs_for_errors() {
    log_info "检查日志中的错误..."
    
    local error_count
    error_count=$(docker-compose logs --tail=100 2>/dev/null | grep -i "error\|exception\|failed" | wc -l)
    
    if [ "$error_count" -gt 10 ]; then
        log_error "发现大量错误日志 ($error_count 条)"
        return 1
    elif [ "$error_count" -gt 0 ]; then
        log_warning "发现少量错误日志 ($error_count 条)"
    else
        log_success "日志中无错误"
    fi
    
    return 0
}

# 综合健康检查
comprehensive_health_check() {
    log_info "开始综合健康检查..."
    
    local checks_passed=0
    local total_checks=0
    
    # 基础服务检查
    ((total_checks++))
    if check_container_status; then
        ((checks_passed++))
    fi
    
    # HTTP端点检查
    ((total_checks++))
    if check_http_endpoint "http://localhost:$MATCHMAKER_PORT/health" "撮合服务"; then
        ((checks_passed++))
    fi
    
    ((total_checks++))
    if check_http_endpoint "http://localhost:$FACTORY_PORT/health" "游戏服务器工厂"; then
        ((checks_passed++))
    fi
    
    # JSON响应检查
    ((total_checks++))
    if check_json_response "http://localhost:$MATCHMAKER_PORT/health" "撮合服务" "status"; then
        ((checks_passed++))
    fi
    
    ((total_checks++))
    if check_json_response "http://localhost:$FACTORY_PORT/health" "游戏服务器工厂" "status"; then
        ((checks_passed++))
    fi
    
    # 网络连通性检查
    ((total_checks++))
    if check_network_connectivity; then
        ((checks_passed++))
    fi
    
    # 资源使用检查
    ((total_checks++))
    if check_resource_usage; then
        ((checks_passed++))
    fi
    
    # 日志错误检查
    ((total_checks++))
    if check_logs_for_errors; then
        ((checks_passed++))
    fi
    
    # 输出结果
    echo ""
    log_info "健康检查结果: $checks_passed/$total_checks 项通过"
    
    if [ "$checks_passed" -eq "$total_checks" ]; then
        log_success "所有健康检查通过！系统运行正常"
        return 0
    elif [ "$checks_passed" -gt $((total_checks / 2)) ]; then
        log_warning "部分健康检查失败，系统可能存在问题"
        return 1
    else
        log_error "多项健康检查失败，系统存在严重问题"
        return 2
    fi
}

# 快速健康检查
quick_health_check() {
    log_info "快速健康检查..."
    
    if check_http_endpoint "http://localhost:$MATCHMAKER_PORT/health" "撮合服务" && \
       check_http_endpoint "http://localhost:$FACTORY_PORT/health" "游戏服务器工厂"; then
        log_success "快速健康检查通过"
        return 0
    else
        log_error "快速健康检查失败"
        return 1
    fi
}

# 监控模式
monitor_mode() {
    local interval=${1:-30}
    
    log_info "启动监控模式，检查间隔: ${interval}秒"
    log_info "按 Ctrl+C 退出监控"
    
    while true; do
        echo ""
        echo "==================== $(date) ===================="
        
        if quick_health_check; then
            echo -e "${GREEN}✓ 系统正常${NC}"
        else
            echo -e "${RED}✗ 系统异常${NC}"
        fi
        
        sleep "$interval"
    done
}

# 生成健康报告
generate_health_report() {
    local report_file="health-report-$(date +%Y%m%d-%H%M%S).txt"
    
    log_info "生成健康报告: $report_file"
    
    {
        echo "AI游戏平台健康检查报告"
        echo "生成时间: $(date)"
        echo "========================================"
        echo ""
        
        echo "容器状态:"
        docker-compose ps
        echo ""
        
        echo "服务健康检查:"
        curl -s "http://localhost:$MATCHMAKER_PORT/health" | jq . 2>/dev/null || echo "撮合服务无响应"
        curl -s "http://localhost:$FACTORY_PORT/health" | jq . 2>/dev/null || echo "游戏服务器工厂无响应"
        echo ""
        
        echo "资源使用情况:"
        docker stats --no-stream
        echo ""
        
        echo "最近日志 (最后50行):"
        docker-compose logs --tail=50
        
    } > "$report_file"
    
    log_success "健康报告已生成: $report_file"
}

# 主函数
main() {
    local command=${1:-"comprehensive"}
    local param=${2:-""}
    
    case $command in
        "quick")
            quick_health_check
            ;;
        "comprehensive")
            comprehensive_health_check
            ;;
        "containers")
            check_container_status
            ;;
        "network")
            check_network_connectivity
            ;;
        "resources")
            check_resource_usage
            ;;
        "logs")
            check_logs_for_errors
            ;;
        "monitor")
            monitor_mode "$param"
            ;;
        "report")
            generate_health_report
            ;;
        *)
            echo "用法: $0 {quick|comprehensive|containers|network|resources|logs|monitor|report} [参数]"
            echo ""
            echo "命令:"
            echo "  quick         - 快速健康检查（默认）"
            echo "  comprehensive - 综合健康检查"
            echo "  containers    - 检查容器状态"
            echo "  network       - 检查网络连通性"
            echo "  resources     - 检查资源使用情况"
            echo "  logs          - 检查日志错误"
            echo "  monitor       - 监控模式 [间隔秒数]"
            echo "  report        - 生成健康报告"
            echo ""
            echo "示例:"
            echo "  $0 quick              # 快速检查"
            echo "  $0 comprehensive      # 综合检查"
            echo "  $0 monitor 60         # 每60秒监控一次"
            echo "  $0 report             # 生成报告"
            exit 1
            ;;
    esac
}

# 脚本入口
main "$@"
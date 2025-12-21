#!/bin/bash

# 环境变量验证脚本
# 验证Docker Compose部署所需的环境变量
# 需求: 7.3

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

# 必需的环境变量
REQUIRED_VARS=(
    "ENVIRONMENT"
    "MATCHMAKER_PORT"
    "FACTORY_PORT"
    "BASE_PORT"
)

# 推荐的环境变量
RECOMMENDED_VARS=(
    "MAX_CONTAINERS"
    "CONTAINER_MEMORY_LIMIT"
    "CONTAINER_CPU_LIMIT"
    "HEARTBEAT_TIMEOUT"
    "CLEANUP_INTERVAL"
    "LOG_LEVEL"
)

# 生产环境必需的环境变量
PRODUCTION_VARS=(
    "ALLOWED_ORIGINS"
    "MATCHMAKER_URL"
    "GAME_SERVER_FACTORY_URL"
)

# 检查.env文件是否存在
check_env_file() {
    log_info "检查环境配置文件..."
    
    if [ ! -f ".env" ]; then
        log_warning ".env文件不存在"
        
        if [ -f ".env.example" ]; then
            log_info "从.env.example创建.env文件..."
            cp .env.example .env
            log_success ".env文件已创建，请根据需要修改配置"
        else
            log_error ".env.example文件也不存在，无法创建默认配置"
            return 1
        fi
    else
        log_success ".env文件存在"
    fi
}

# 加载环境变量
load_env_vars() {
    if [ -f ".env" ]; then
        # 导出环境变量，忽略注释和空行
        set -a
        source .env
        set +a
        log_info "环境变量已加载"
    else
        log_error "无法加载.env文件"
        return 1
    fi
}

# 验证必需的环境变量
validate_required_vars() {
    log_info "验证必需的环境变量..."
    
    local missing_vars=()
    local invalid_vars=()
    
    for var in "${REQUIRED_VARS[@]}"; do
        local value="${!var}"
        
        if [ -z "$value" ]; then
            missing_vars+=("$var")
        else
            # 验证特定变量的格式
            case $var in
                "ENVIRONMENT")
                    if [[ ! "$value" =~ ^(development|staging|production)$ ]]; then
                        invalid_vars+=("$var: 必须是 development, staging 或 production")
                    fi
                    ;;
                "MATCHMAKER_PORT"|"FACTORY_PORT"|"BASE_PORT")
                    if ! [[ "$value" =~ ^[0-9]+$ ]] || [ "$value" -lt 1 ] || [ "$value" -gt 65535 ]; then
                        invalid_vars+=("$var: 必须是1-65535之间的数字")
                    fi
                    ;;
            esac
        fi
    done
    
    # 报告结果
    if [ ${#missing_vars[@]} -eq 0 ] && [ ${#invalid_vars[@]} -eq 0 ]; then
        log_success "所有必需的环境变量都已正确配置"
        return 0
    else
        if [ ${#missing_vars[@]} -gt 0 ]; then
            log_error "缺少必需的环境变量: ${missing_vars[*]}"
        fi
        
        if [ ${#invalid_vars[@]} -gt 0 ]; then
            log_error "无效的环境变量配置:"
            for invalid in "${invalid_vars[@]}"; do
                log_error "  $invalid"
            done
        fi
        
        return 1
    fi
}

# 验证推荐的环境变量
validate_recommended_vars() {
    log_info "检查推荐的环境变量..."
    
    local missing_recommended=()
    local warnings=()
    
    for var in "${RECOMMENDED_VARS[@]}"; do
        local value="${!var}"
        
        if [ -z "$value" ]; then
            missing_recommended+=("$var")
        else
            # 验证推荐变量的合理性
            case $var in
                "MAX_CONTAINERS")
                    if ! [[ "$value" =~ ^[0-9]+$ ]] || [ "$value" -lt 1 ] || [ "$value" -gt 1000 ]; then
                        warnings+=("$var: 建议设置为1-1000之间的数字")
                    fi
                    ;;
                "LOG_LEVEL")
                    if [[ ! "$value" =~ ^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$ ]]; then
                        warnings+=("$var: 建议设置为 DEBUG, INFO, WARNING, ERROR 或 CRITICAL")
                    fi
                    ;;
                "HEARTBEAT_TIMEOUT"|"CLEANUP_INTERVAL")
                    if ! [[ "$value" =~ ^[0-9]+$ ]] || [ "$value" -lt 5 ] || [ "$value" -gt 3600 ]; then
                        warnings+=("$var: 建议设置为5-3600秒之间")
                    fi
                    ;;
            esac
        fi
    done
    
    # 报告结果
    if [ ${#missing_recommended[@]} -gt 0 ]; then
        log_warning "缺少推荐的环境变量: ${missing_recommended[*]}"
    fi
    
    if [ ${#warnings[@]} -gt 0 ]; then
        log_warning "环境变量配置建议:"
        for warning in "${warnings[@]}"; do
            log_warning "  $warning"
        done
    fi
    
    if [ ${#missing_recommended[@]} -eq 0 ] && [ ${#warnings[@]} -eq 0 ]; then
        log_success "所有推荐的环境变量都已正确配置"
    fi
}

# 验证生产环境配置
validate_production_config() {
    if [ "$ENVIRONMENT" != "production" ]; then
        return 0
    fi
    
    log_info "验证生产环境配置..."
    
    local production_issues=()
    
    # 检查生产环境必需变量
    for var in "${PRODUCTION_VARS[@]}"; do
        local value="${!var}"
        
        if [ -z "$value" ]; then
            production_issues+=("缺少生产环境必需变量: $var")
        fi
    done
    
    # 检查安全配置
    if [ "$DEBUG" = "true" ]; then
        production_issues+=("生产环境中DEBUG应设置为false")
    fi
    
    if [ "$ALLOWED_ORIGINS" = "*" ]; then
        production_issues+=("生产环境中ALLOWED_ORIGINS不应设置为*")
    fi
    
    if [ "$LOG_LEVEL" = "DEBUG" ]; then
        production_issues+=("生产环境中LOG_LEVEL不应设置为DEBUG")
    fi
    
    # 检查URL配置
    if [[ "$MATCHMAKER_URL" =~ ^http://localhost ]] || [[ "$MATCHMAKER_URL" =~ ^http://127\.0\.0\.1 ]]; then
        production_issues+=("生产环境中MATCHMAKER_URL不应使用localhost")
    fi
    
    if [[ "$GAME_SERVER_FACTORY_URL" =~ ^http://localhost ]] || [[ "$GAME_SERVER_FACTORY_URL" =~ ^http://127\.0\.0\.1 ]]; then
        production_issues+=("生产环境中GAME_SERVER_FACTORY_URL不应使用localhost")
    fi
    
    # 报告结果
    if [ ${#production_issues[@]} -eq 0 ]; then
        log_success "生产环境配置验证通过"
        return 0
    else
        log_error "生产环境配置问题:"
        for issue in "${production_issues[@]}"; do
            log_error "  $issue"
        done
        return 1
    fi
}

# 验证端口冲突
validate_port_conflicts() {
    log_info "检查端口冲突..."
    
    local ports=("$MATCHMAKER_PORT" "$FACTORY_PORT" "$EXAMPLE_SERVER_PORT")
    local port_conflicts=()
    
    # 检查端口是否被占用
    for port in "${ports[@]}"; do
        if [ -n "$port" ]; then
            if lsof -i ":$port" > /dev/null 2>&1; then
                port_conflicts+=("端口 $port 已被占用")
            fi
        fi
    done
    
    # 检查端口范围冲突
    if [ -n "$BASE_PORT" ] && [ -n "$MAX_PORT" ]; then
        if [ "$BASE_PORT" -ge "$MAX_PORT" ]; then
            port_conflicts+=("BASE_PORT ($BASE_PORT) 必须小于 MAX_PORT ($MAX_PORT)")
        fi
        
        # 检查端口范围是否与主要服务端口冲突
        for port in "${ports[@]}"; do
            if [ -n "$port" ] && [ "$port" -ge "$BASE_PORT" ] && [ "$port" -le "$MAX_PORT" ]; then
                port_conflicts+=("服务端口 $port 与动态端口范围 $BASE_PORT-$MAX_PORT 冲突")
            fi
        done
    fi
    
    # 报告结果
    if [ ${#port_conflicts[@]} -eq 0 ]; then
        log_success "端口配置验证通过"
        return 0
    else
        log_error "端口配置问题:"
        for conflict in "${port_conflicts[@]}"; do
            log_error "  $conflict"
        done
        return 1
    fi
}

# 验证Docker Compose配置
validate_docker_compose_config() {
    log_info "验证Docker Compose配置..."
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose 未安装"
        return 1
    fi
    
    # 验证配置文件语法
    if docker-compose config --quiet; then
        log_success "Docker Compose配置语法正确"
    else
        log_error "Docker Compose配置语法错误"
        return 1
    fi
    
    # 检查服务定义
    local services
    services=$(docker-compose config --services)
    
    local expected_services=("matchmaker" "game-server-factory")
    local missing_services=()
    
    for service in "${expected_services[@]}"; do
        if ! echo "$services" | grep -q "^$service$"; then
            missing_services+=("$service")
        fi
    done
    
    if [ ${#missing_services[@]} -eq 0 ]; then
        log_success "所有必需的服务都已定义"
        return 0
    else
        log_error "缺少必需的服务定义: ${missing_services[*]}"
        return 1
    fi
}

# 生成配置报告
generate_config_report() {
    local report_file="env-validation-$(date +%Y%m%d-%H%M%S).txt"
    
    log_info "生成环境配置报告: $report_file"
    
    {
        echo "AI游戏平台环境配置验证报告"
        echo "生成时间: $(date)"
        echo "========================================"
        echo ""
        
        echo "环境类型: ${ENVIRONMENT:-未设置}"
        echo "调试模式: ${DEBUG:-未设置}"
        echo "日志级别: ${LOG_LEVEL:-未设置}"
        echo ""
        
        echo "服务端口配置:"
        echo "  撮合服务: ${MATCHMAKER_PORT:-未设置}"
        echo "  游戏服务器工厂: ${FACTORY_PORT:-未设置}"
        echo "  示例游戏服务器: ${EXAMPLE_SERVER_PORT:-未设置}"
        echo "  动态端口范围: ${BASE_PORT:-未设置} - ${MAX_PORT:-未设置}"
        echo ""
        
        echo "容器配置:"
        echo "  最大容器数: ${MAX_CONTAINERS:-未设置}"
        echo "  内存限制: ${CONTAINER_MEMORY_LIMIT:-未设置}"
        echo "  CPU限制: ${CONTAINER_CPU_LIMIT:-未设置}"
        echo ""
        
        echo "网络配置:"
        echo "  允许的来源: ${ALLOWED_ORIGINS:-未设置}"
        echo "  撮合服务URL: ${MATCHMAKER_URL:-未设置}"
        echo "  游戏服务器工厂URL: ${GAME_SERVER_FACTORY_URL:-未设置}"
        echo ""
        
        echo "当前环境变量:"
        env | grep -E "^(ENVIRONMENT|DEBUG|LOG_LEVEL|MATCHMAKER_|FACTORY_|BASE_|MAX_|CONTAINER_|HEARTBEAT_|CLEANUP_|ALLOWED_|GAME_SERVER_)" | sort
        
    } > "$report_file"
    
    log_success "环境配置报告已生成: $report_file"
}

# 修复常见配置问题
fix_common_issues() {
    log_info "尝试修复常见配置问题..."
    
    local fixes_applied=0
    
    # 创建.env文件（如果不存在）
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
        log_success "已从.env.example创建.env文件"
        ((fixes_applied++))
    fi
    
    # 设置默认环境类型
    if [ -z "$ENVIRONMENT" ]; then
        echo "ENVIRONMENT=development" >> .env
        log_success "已设置默认环境类型为development"
        ((fixes_applied++))
    fi
    
    # 设置默认端口
    if [ -z "$MATCHMAKER_PORT" ]; then
        echo "MATCHMAKER_PORT=8000" >> .env
        log_success "已设置默认撮合服务端口为8000"
        ((fixes_applied++))
    fi
    
    if [ -z "$FACTORY_PORT" ]; then
        echo "FACTORY_PORT=8080" >> .env
        log_success "已设置默认游戏服务器工厂端口为8080"
        ((fixes_applied++))
    fi
    
    if [ -z "$BASE_PORT" ]; then
        echo "BASE_PORT=8082" >> .env
        log_success "已设置默认动态端口基础值为8082"
        ((fixes_applied++))
    fi
    
    log_info "应用了 $fixes_applied 个配置修复"
    
    if [ $fixes_applied -gt 0 ]; then
        log_warning "请重新运行验证以确认修复结果"
    fi
}

# 综合验证
comprehensive_validation() {
    log_info "开始综合环境配置验证..."
    
    local validation_passed=true
    
    # 执行所有验证
    check_env_file || validation_passed=false
    load_env_vars || validation_passed=false
    validate_required_vars || validation_passed=false
    validate_recommended_vars  # 推荐变量不影响整体结果
    validate_production_config || validation_passed=false
    validate_port_conflicts || validation_passed=false
    validate_docker_compose_config || validation_passed=false
    
    echo ""
    if [ "$validation_passed" = true ]; then
        log_success "环境配置验证通过！"
        return 0
    else
        log_error "环境配置验证失败，请修复上述问题"
        return 1
    fi
}

# 主函数
main() {
    local command=${1:-"validate"}
    
    case $command in
        "validate")
            comprehensive_validation
            ;;
        "check")
            check_env_file
            load_env_vars
            ;;
        "required")
            load_env_vars
            validate_required_vars
            ;;
        "recommended")
            load_env_vars
            validate_recommended_vars
            ;;
        "production")
            load_env_vars
            validate_production_config
            ;;
        "ports")
            load_env_vars
            validate_port_conflicts
            ;;
        "docker")
            validate_docker_compose_config
            ;;
        "fix")
            fix_common_issues
            ;;
        "report")
            load_env_vars
            generate_config_report
            ;;
        *)
            echo "用法: $0 {validate|check|required|recommended|production|ports|docker|fix|report}"
            echo ""
            echo "命令:"
            echo "  validate     - 综合验证（默认）"
            echo "  check        - 检查.env文件"
            echo "  required     - 验证必需变量"
            echo "  recommended  - 验证推荐变量"
            echo "  production   - 验证生产环境配置"
            echo "  ports        - 验证端口配置"
            echo "  docker       - 验证Docker Compose配置"
            echo "  fix          - 修复常见问题"
            echo "  report       - 生成配置报告"
            echo ""
            echo "示例:"
            echo "  $0 validate     # 综合验证"
            echo "  $0 fix          # 修复常见问题"
            echo "  $0 production   # 验证生产环境"
            exit 1
            ;;
    esac
}

# 脚本入口
main "$@"
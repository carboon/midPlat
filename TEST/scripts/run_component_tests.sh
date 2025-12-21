#!/bin/bash
# 运行特定组件测试的脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_DIR="${WORKSPACE_ROOT}/TEST"
LOG_DIR="${WORKSPACE_ROOT}/.kiro_workspace/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建日志目录
mkdir -p "${LOG_DIR}"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "${LOG_DIR}/test_component_${TIMESTAMP}.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "${LOG_DIR}/test_component_${TIMESTAMP}.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "${LOG_DIR}/test_component_${TIMESTAMP}.log"
}

# 帮助信息
show_help() {
    cat << EOF
运行特定组件测试脚本

用法: bash TEST/scripts/run_component_tests.sh <组件> [类型]

组件:
    factory     - Game Server Factory
    matchmaker  - Matchmaker Service
    template    - Game Server Template
    mobile      - Mobile App

类型 (可选):
    unit        - 仅运行单元测试
    integration - 仅运行集成测试
    property    - 仅运行属性测试
    (不指定则运行所有类型)

示例:
    # 运行 Game Server Factory 所有测试
    bash TEST/scripts/run_component_tests.sh factory

    # 仅运行单元测试
    bash TEST/scripts/run_component_tests.sh factory unit

    # 仅运行集成测试
    bash TEST/scripts/run_component_tests.sh factory integration
EOF
}

# 检查参数
if [ $# -lt 1 ]; then
    log_error "缺少必要参数"
    show_help
    exit 1
fi

COMPONENT=$1
TEST_TYPE=${2:-all}

# 验证组件
case $COMPONENT in
    factory)
        COMPONENT_DIR="${TEST_DIR}/game_server_factory"
        COMPONENT_NAME="Game Server Factory"
        ;;
    matchmaker)
        COMPONENT_DIR="${TEST_DIR}/matchmaker_service"
        COMPONENT_NAME="Matchmaker Service"
        ;;
    template)
        COMPONENT_DIR="${TEST_DIR}/game_server_template"
        COMPONENT_NAME="Game Server Template"
        ;;
    mobile)
        COMPONENT_DIR="${TEST_DIR}/mobile_app"
        COMPONENT_NAME="Mobile App"
        ;;
    *)
        log_error "未知组件: $COMPONENT"
        show_help
        exit 1
        ;;
esac

# 检查目录是否存在
if [ ! -d "$COMPONENT_DIR" ]; then
    log_error "组件目录不存在: $COMPONENT_DIR"
    exit 1
fi

# 主函数
main() {
    log_info "=========================================="
    log_info "运行 $COMPONENT_NAME 测试"
    log_info "=========================================="
    
    cd "$COMPONENT_DIR"
    
    case $COMPONENT in
        factory|matchmaker)
            # Python 测试
            case $TEST_TYPE in
                unit)
                    log_info "运行单元测试..."
                    if [ -d "unit" ]; then
                        python3 -m pytest unit/ -v --tb=short --timeout=120 2>&1 | tee -a "${LOG_DIR}/test_component_${TIMESTAMP}.log"
                    else
                        log_error "单元测试目录不存在"
                        exit 1
                    fi
                    ;;
                integration)
                    log_info "运行集成测试..."
                    if [ -d "integration" ]; then
                        python3 -m pytest integration/ -v --tb=short --timeout=120 2>&1 | tee -a "${LOG_DIR}/test_component_${TIMESTAMP}.log"
                    else
                        log_error "集成测试目录不存在"
                        exit 1
                    fi
                    ;;
                property)
                    log_info "运行属性测试..."
                    python3 -m pytest . -k "property" -v --tb=short --timeout=120 2>&1 | tee -a "${LOG_DIR}/test_component_${TIMESTAMP}.log"
                    ;;
                all)
                    log_info "运行所有测试..."
                    python3 -m pytest . -v --tb=short --timeout=120 2>&1 | tee -a "${LOG_DIR}/test_component_${TIMESTAMP}.log"
                    ;;
            esac
            ;;
        template)
            # JavaScript 测试
            case $TEST_TYPE in
                unit)
                    log_info "运行单元测试..."
                    if [ -d "unit" ]; then
                        npm test -- unit/ --runInBand --testTimeout=30000 2>&1 | tee -a "${LOG_DIR}/test_component_${TIMESTAMP}.log"
                    else
                        log_error "单元测试目录不存在"
                        exit 1
                    fi
                    ;;
                integration)
                    log_info "运行集成测试..."
                    if [ -d "integration" ]; then
                        npm test -- integration/ --runInBand --testTimeout=30000 2>&1 | tee -a "${LOG_DIR}/test_component_${TIMESTAMP}.log"
                    else
                        log_error "集成测试目录不存在"
                        exit 1
                    fi
                    ;;
                property)
                    log_info "运行属性测试..."
                    npm test -- --testNamePattern="property" --runInBand --testTimeout=30000 2>&1 | tee -a "${LOG_DIR}/test_component_${TIMESTAMP}.log"
                    ;;
                all)
                    log_info "运行所有测试..."
                    npm test -- --runInBand --testTimeout=30000 2>&1 | tee -a "${LOG_DIR}/test_component_${TIMESTAMP}.log"
                    ;;
            esac
            ;;
        mobile)
            # Dart 测试
            case $TEST_TYPE in
                unit)
                    log_info "运行单元测试..."
                    flutter test --exclude-tags=integration 2>&1 | tee -a "${LOG_DIR}/test_component_${TIMESTAMP}.log"
                    ;;
                integration)
                    log_info "运行集成测试..."
                    flutter test --tags=integration 2>&1 | tee -a "${LOG_DIR}/test_component_${TIMESTAMP}.log"
                    ;;
                property)
                    log_info "运行属性测试..."
                    flutter test --exclude-tags=integration 2>&1 | tee -a "${LOG_DIR}/test_component_${TIMESTAMP}.log"
                    ;;
                all)
                    log_info "运行所有测试..."
                    flutter test 2>&1 | tee -a "${LOG_DIR}/test_component_${TIMESTAMP}.log"
                    ;;
            esac
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        log_success "=========================================="
        log_success "$COMPONENT_NAME 测试完成 - 通过"
        log_success "=========================================="
        log_success "日志文件: ${LOG_DIR}/test_component_${TIMESTAMP}.log"
        exit 0
    else
        log_error "=========================================="
        log_error "$COMPONENT_NAME 测试完成 - 存在失败"
        log_error "=========================================="
        log_error "日志文件: ${LOG_DIR}/test_component_${TIMESTAMP}.log"
        exit 1
    fi
}

# 运行主函数
main "$@"

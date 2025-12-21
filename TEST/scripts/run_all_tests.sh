#!/bin/bash
# 运行所有测试的脚本

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
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "${LOG_DIR}/test_all_${TIMESTAMP}.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "${LOG_DIR}/test_all_${TIMESTAMP}.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "${LOG_DIR}/test_all_${TIMESTAMP}.log"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "${LOG_DIR}/test_all_${TIMESTAMP}.log"
}

# 帮助信息
show_help() {
    cat << EOF
运行所有测试脚本

用法: bash TEST/scripts/run_all_tests.sh [选项]

选项:
    -h, --help              显示此帮助信息
    -c, --clean             清理后运行测试
    -v, --verbose           详细输出
    --timeout SECONDS       设置测试超时时间

示例:
    # 运行所有测试
    bash TEST/scripts/run_all_tests.sh

    # 清理后运行
    bash TEST/scripts/run_all_tests.sh --clean

    # 详细输出
    bash TEST/scripts/run_all_tests.sh --verbose
EOF
}

# 解析参数
CLEAN=false
VERBOSE=false
TIMEOUT=300

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --timeout)
            TIMEOUT=$2
            shift 2
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 清理
if [ "$CLEAN" = true ]; then
    log_info "清理测试环境..."
    cd "${WORKSPACE_ROOT}"
    
    # 清理 Python 缓存
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # 清理 Node.js 缓存
    rm -rf game_server_template/node_modules 2>/dev/null || true
    rm -f game_server_template/package-lock.json 2>/dev/null || true
    npm cache clean --force 2>/dev/null || true
    
    # 清理 Flutter 缓存
    rm -rf mobile_app/universal_game_client/.dart_tool 2>/dev/null || true
    rm -rf mobile_app/universal_game_client/build 2>/dev/null || true
    flutter clean 2>/dev/null || true
    
    log_success "清理完成"
fi

# 主函数
main() {
    log_info "=========================================="
    log_info "运行所有测试 (从 TEST 目录)"
    log_info "=========================================="
    
    cd "${WORKSPACE_ROOT}"
    
    # 运行完整测试
    log_info "执行: python3 run_all_tests.py --timeout ${TIMEOUT}"
    
    if python3 run_all_tests.py --timeout "${TIMEOUT}" 2>&1 | tee -a "${LOG_DIR}/test_all_${TIMESTAMP}.log"; then
        log_success "=========================================="
        log_success "所有测试完成 - 通过"
        log_success "=========================================="
        log_success "日志文件: ${LOG_DIR}/test_all_${TIMESTAMP}.log"
        exit 0
    else
        log_error "=========================================="
        log_error "所有测试完成 - 存在失败"
        log_error "=========================================="
        log_error "日志文件: ${LOG_DIR}/test_all_${TIMESTAMP}.log"
        exit 1
    fi
}

# 运行主函数
main "$@"

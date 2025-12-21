#!/bin/bash

# Docker镜像构建脚本
# 优化镜像构建过程和缓存管理
# 需求: 7.1

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
BUILD_CACHE=${BUILD_CACHE:-true}
PARALLEL_BUILD=${PARALLEL_BUILD:-true}
PUSH_IMAGES=${PUSH_IMAGES:-false}
REGISTRY=${REGISTRY:-""}

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

# 检查Docker环境
check_docker_environment() {
    log_info "检查Docker环境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi
    
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker守护进程未运行"
        exit 1
    fi
    
    # 检查Docker Buildx
    if docker buildx version > /dev/null 2>&1; then
        log_info "Docker Buildx 可用"
        export DOCKER_BUILDKIT=1
    else
        log_warning "Docker Buildx 不可用，使用传统构建"
    fi
    
    log_success "Docker环境检查通过"
}

# 清理构建缓存
clean_build_cache() {
    log_info "清理Docker构建缓存..."
    
    # 清理构建缓存
    docker builder prune -f > /dev/null 2>&1 || true
    
    # 清理未使用的镜像
    docker image prune -f > /dev/null 2>&1 || true
    
    log_success "构建缓存清理完成"
}

# 构建单个服务镜像
build_service_image() {
    local service_name=$1
    local context_path=$2
    local dockerfile_path=${3:-"Dockerfile"}
    local image_tag=${4:-"latest"}
    
    log_info "构建 $service_name 镜像..."
    
    local build_args=""
    local cache_args=""
    
    # 构建参数
    if [ "$BUILD_CACHE" = "true" ]; then
        cache_args="--cache-from $service_name:$image_tag"
    fi
    
    # 添加构建时间标签
    build_args="--build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    build_args="$build_args --build-arg VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    
    # 执行构建
    local build_cmd="docker build"
    
    if [ "$DOCKER_BUILDKIT" = "1" ]; then
        build_cmd="docker buildx build --load"
    fi
    
    if $build_cmd \
        $cache_args \
        $build_args \
        --tag "$service_name:$image_tag" \
        --file "$context_path/$dockerfile_path" \
        "$context_path"; then
        
        log_success "$service_name 镜像构建成功"
        
        # 显示镜像信息
        local image_size
        image_size=$(docker images "$service_name:$image_tag" --format "{{.Size}}")
        log_info "$service_name 镜像大小: $image_size"
        
        return 0
    else
        log_error "$service_name 镜像构建失败"
        return 1
    fi
}

# 并行构建镜像
build_images_parallel() {
    log_info "并行构建所有服务镜像..."
    
    local pids=()
    local services=(
        "matchmaker:matchmaker_service/matchmaker"
        "game-server-factory:game_server_factory"
        "game-server-template:game_server_template"
    )
    
    # 启动并行构建
    for service_info in "${services[@]}"; do
        local service_name=$(echo "$service_info" | cut -d: -f1)
        local context_path=$(echo "$service_info" | cut -d: -f2)
        
        (
            build_service_image "$service_name" "$context_path" "Dockerfile" "latest"
        ) &
        
        local pid=$!
        pids+=($pid)
        log_info "启动 $service_name 构建进程 (PID: $pid)"
    done
    
    # 等待所有构建完成
    local success_count=0
    local total_count=${#pids[@]}
    
    for i in $(seq 0 $((${#pids[@]} - 1))); do
        local pid=${pids[$i]}
        local service_name=$(echo "${services[$i]}" | cut -d: -f1)
        
        if wait $pid; then
            log_success "$service_name 构建完成"
            ((success_count++))
        else
            log_error "$service_name 构建失败"
        fi
    done
    
    log_info "并行构建结果: $success_count/$total_count 成功"
    
    if [ $success_count -eq $total_count ]; then
        return 0
    else
        return 1
    fi
}

# 串行构建镜像
build_images_sequential() {
    log_info "串行构建所有服务镜像..."
    
    local success_count=0
    local total_count=0
    
    # 撮合服务
    ((total_count++))
    if build_service_image "matchmaker" "matchmaker_service/matchmaker" "Dockerfile" "latest"; then
        ((success_count++))
    fi
    
    # 游戏服务器工厂
    ((total_count++))
    if build_service_image "game-server-factory" "game_server_factory" "Dockerfile" "latest"; then
        ((success_count++))
    fi
    
    # 游戏服务器模板
    ((total_count++))
    if build_service_image "game-server-template" "game_server_template" "Dockerfile" "latest"; then
        ((success_count++))
    fi
    
    log_info "串行构建结果: $success_count/$total_count 成功"
    
    if [ $success_count -eq $total_count ]; then
        return 0
    else
        return 1
    fi
}

# 标记镜像
tag_images() {
    local tag=${1:-"latest"}
    
    log_info "标记镜像版本: $tag"
    
    local services=("matchmaker" "game-server-factory" "game-server-template")
    
    for service in "${services[@]}"; do
        if docker images "$service:latest" --format "{{.Repository}}" | grep -q "$service"; then
            docker tag "$service:latest" "$service:$tag"
            log_success "$service 已标记为 $tag"
        else
            log_warning "$service:latest 镜像不存在，跳过标记"
        fi
    done
}

# 推送镜像到仓库
push_images() {
    local tag=${1:-"latest"}
    
    if [ -z "$REGISTRY" ]; then
        log_warning "未配置镜像仓库，跳过推送"
        return 0
    fi
    
    log_info "推送镜像到仓库: $REGISTRY"
    
    local services=("matchmaker" "game-server-factory" "game-server-template")
    
    for service in "${services[@]}"; do
        local local_image="$service:$tag"
        local remote_image="$REGISTRY/$service:$tag"
        
        # 标记远程镜像
        docker tag "$local_image" "$remote_image"
        
        # 推送镜像
        if docker push "$remote_image"; then
            log_success "$service 推送成功"
        else
            log_error "$service 推送失败"
        fi
    done
}

# 验证镜像
verify_images() {
    log_info "验证构建的镜像..."
    
    local services=("matchmaker" "game-server-factory" "game-server-template")
    local all_valid=true
    
    for service in "${services[@]}"; do
        if docker images "$service:latest" --format "{{.Repository}}" | grep -q "$service"; then
            # 检查镜像是否可以运行
            if docker run --rm "$service:latest" --help > /dev/null 2>&1 || \
               docker run --rm "$service:latest" --version > /dev/null 2>&1 || \
               docker run --rm --entrypoint="" "$service:latest" echo "test" > /dev/null 2>&1; then
                log_success "$service 镜像验证通过"
            else
                log_warning "$service 镜像可能存在问题"
            fi
        else
            log_error "$service 镜像不存在"
            all_valid=false
        fi
    done
    
    if [ "$all_valid" = true ]; then
        return 0
    else
        return 1
    fi
}

# 显示镜像信息
show_images_info() {
    log_info "构建的镜像信息:"
    echo ""
    
    # 显示镜像列表
    docker images --filter "reference=matchmaker" --filter "reference=game-server-factory" --filter "reference=game-server-template" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    echo ""
    
    # 显示总大小
    local total_size
    total_size=$(docker images --filter "reference=matchmaker" --filter "reference=game-server-factory" --filter "reference=game-server-template" --format "{{.Size}}" | \
        sed 's/MB//' | sed 's/GB/*1024/' | sed 's/KB\/1024/' | \
        awk '{sum += $1} END {printf "%.1f MB", sum}')
    
    log_info "镜像总大小: $total_size"
}

# 生成构建报告
generate_build_report() {
    local report_file="build-report-$(date +%Y%m%d-%H%M%S).txt"
    
    log_info "生成构建报告: $report_file"
    
    {
        echo "AI游戏平台Docker镜像构建报告"
        echo "生成时间: $(date)"
        echo "========================================"
        echo ""
        
        echo "构建环境:"
        echo "  Docker版本: $(docker --version)"
        echo "  Docker Compose版本: $(docker-compose --version 2>/dev/null || echo 'N/A')"
        echo "  构建缓存: $BUILD_CACHE"
        echo "  并行构建: $PARALLEL_BUILD"
        echo ""
        
        echo "镜像信息:"
        docker images --filter "reference=matchmaker" --filter "reference=game-server-factory" --filter "reference=game-server-template" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
        echo ""
        
        echo "镜像详细信息:"
        for service in "matchmaker" "game-server-factory" "game-server-template"; do
            echo "----------------------------------------"
            echo "服务: $service"
            docker inspect "$service:latest" --format '  镜像ID: {{.Id}}
  创建时间: {{.Created}}
  架构: {{.Architecture}}
  操作系统: {{.Os}}
  大小: {{.Size}} bytes' 2>/dev/null || echo "  镜像不存在"
        done
        
    } > "$report_file"
    
    log_success "构建报告已生成: $report_file"
}

# 主函数
main() {
    local command=${1:-"build"}
    local param=${2:-""}
    
    case $command in
        "build")
            check_docker_environment
            if [ "$PARALLEL_BUILD" = "true" ]; then
                build_images_parallel
            else
                build_images_sequential
            fi
            verify_images
            show_images_info
            ;;
        "clean")
            clean_build_cache
            ;;
        "tag")
            tag_images "$param"
            ;;
        "push")
            push_images "$param"
            ;;
        "verify")
            verify_images
            ;;
        "info")
            show_images_info
            ;;
        "report")
            generate_build_report
            ;;
        "all")
            check_docker_environment
            clean_build_cache
            if [ "$PARALLEL_BUILD" = "true" ]; then
                build_images_parallel
            else
                build_images_sequential
            fi
            verify_images
            show_images_info
            if [ -n "$param" ]; then
                tag_images "$param"
            fi
            if [ "$PUSH_IMAGES" = "true" ]; then
                push_images "$param"
            fi
            generate_build_report
            ;;
        *)
            echo "用法: $0 {build|clean|tag|push|verify|info|report|all} [参数]"
            echo ""
            echo "命令:"
            echo "  build   - 构建所有镜像（默认）"
            echo "  clean   - 清理构建缓存"
            echo "  tag     - 标记镜像版本 [版本号]"
            echo "  push    - 推送镜像到仓库 [版本号]"
            echo "  verify  - 验证镜像"
            echo "  info    - 显示镜像信息"
            echo "  report  - 生成构建报告"
            echo "  all     - 执行完整构建流程 [版本号]"
            echo ""
            echo "环境变量:"
            echo "  BUILD_CACHE=true/false     - 是否使用构建缓存"
            echo "  PARALLEL_BUILD=true/false  - 是否并行构建"
            echo "  PUSH_IMAGES=true/false     - 是否推送镜像"
            echo "  REGISTRY=registry.com      - 镜像仓库地址"
            echo ""
            echo "示例:"
            echo "  $0 build                   # 构建所有镜像"
            echo "  $0 tag v1.0.0              # 标记版本"
            echo "  REGISTRY=my.registry.com $0 push v1.0.0  # 推送到仓库"
            echo "  $0 all v1.0.0              # 完整构建流程"
            exit 1
            ;;
    esac
}

# 脚本入口
main "$@"
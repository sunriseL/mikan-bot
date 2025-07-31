#!/bin/bash

# Docker 部署脚本
# 用于快速部署 Mikan Bot

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

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_success "Docker 环境检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p data
    mkdir -p logs
    
    log_success "目录创建完成"
}

# 检查配置文件
check_config() {
    log_info "检查配置文件..."
    
    if [ ! -f ".env" ]; then
        log_warning ".env 文件不存在，从模板创建..."
        if [ -f "env.example" ]; then
            cp env.example .env
            log_warning "请编辑 .env 文件配置环境变量"
            read -p "按 Enter 键继续..."
        else
            log_error "env.example 文件不存在"
            exit 1
        fi
    fi
    
    log_success "配置文件检查完成"
}

# 构建镜像
build_images() {
    log_info "构建 Docker 镜像..."
    docker-compose build
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 检查是否指定了环境
    if [ "$1" = "dev" ]; then
        log_info "启动开发环境..."
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    else
        log_info "启动默认环境..."
        docker-compose up -d
    fi
    
    log_success "服务启动完成"
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker-compose down
    log_success "服务停止完成"
}

# 重启服务
restart_services() {
    log_info "重启服务..."
    docker-compose restart
    log_success "服务重启完成"
}

# 查看日志
show_logs() {
    log_info "显示日志..."
    docker-compose logs -f
}

# 查看状态
show_status() {
    log_info "服务状态："
    docker-compose ps
}

# 清理
cleanup() {
    log_warning "清理 Docker 资源..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    log_success "清理完成"
}

# 主函数
main() {
    case "$1" in
        "start")
            check_docker
            create_directories
            check_config
            build_images
            start_services "$2"
            show_status
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "logs")
            show_logs
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup
            ;;
        "dev")
            check_docker
            create_directories
            check_config
            build_images
            start_services "dev"
            show_status
            ;;
        *)
            echo "用法: $0 {start|stop|restart|logs|status|cleanup|dev}"
            echo ""
            echo "命令说明："
            echo "  start [env]   - 启动服务 (可选: dev)"
            echo "  stop          - 停止服务"
            echo "  restart       - 重启服务"
            echo "  logs          - 查看日志"
            echo "  status        - 查看状态"
            echo "  cleanup       - 清理资源"
            echo "  dev           - 启动开发环境"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@" 
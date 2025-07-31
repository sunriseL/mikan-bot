# Docker 部署指南

## 概述

本项目提供了完整的 Docker 容器化部署方案，只需要一个 `mikan-bot` 服务即可运行。

## 文件结构

```
mikan/
├── Dockerfile                    # Docker 镜像构建文件
├── docker-compose.yml            # 生产环境配置
├── docker-compose.dev.yml        # 开发环境配置
├── docker-compose.override.yml   # 本地开发覆盖配置
├── docker-deploy.sh             # 部署脚本
├── env.example                  # 环境变量模板
├── .dockerignore                # Docker 忽略文件
└── DOCKER_DEPLOYMENT.md         # 本文档
```

## 快速开始

### 1. 环境准备

确保已安装 Docker 和 Docker Compose：

```bash
# 检查 Docker 版本
docker --version
docker-compose --version
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑配置文件
nano .env
```

主要配置项：
- `ONEAAPI_KEY`: OpenAI API 密钥
- `ONEAAPI_URL`: API 地址（可选）
- `ONEAAPI_MODEL`: 使用的模型名称

### 3. 使用部署脚本

```bash
# 启动开发环境
./docker-deploy.sh dev

# 启动生产环境
./docker-deploy.sh start

# 查看状态
./docker-deploy.sh status

# 查看日志
./docker-deploy.sh logs

# 停止服务
./docker-deploy.sh stop

# 重启服务
./docker-deploy.sh restart

# 清理资源
./docker-deploy.sh cleanup
```

### 4. 手动部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 环境配置

### 开发环境

使用 `docker-compose.dev.yml` 配置：
- 挂载源码目录用于热重载
- 启用调试模式
- 详细日志输出

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 生产环境

使用默认的 `docker-compose.yml` 配置：
- 优化性能
- 最小化日志输出
- 健康检查

```bash
docker-compose up -d
```

## 数据持久化

以下目录会被挂载到容器中：

- `./data` → `/app/data` - 数据文件
- `./logs` → `/app/logs` - 日志文件
- `./.env` → `/app/.env` - 环境变量

## 端口配置

- `8080` - NoneBot2 服务端口

## 健康检查

容器包含健康检查机制，会定期检查服务状态：

```bash
# 查看健康状态
docker-compose ps
```

## 故障排除

### 1. 容器启动失败

```bash
# 查看详细日志
docker-compose logs mikan-bot

# 检查配置文件
docker-compose config
```

### 2. 权限问题

```bash
# 确保脚本有执行权限
chmod +x docker-deploy.sh
```

### 3. 端口冲突

如果 8080 端口被占用，可以修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "8081:8080"  # 改为其他端口
```

## 更新部署

```bash
# 停止服务
./docker-deploy.sh stop

# 重新构建并启动
./docker-deploy.sh start
```

## 清理资源

```bash
# 清理所有容器和镜像
./docker-deploy.sh cleanup
```

## 注意事项

1. 首次启动需要下载基础镜像，可能需要一些时间
2. 确保 `.env` 文件中的 API 密钥配置正确
3. 生产环境建议使用 HTTPS 和反向代理
4. 定期备份 `data` 目录中的重要数据 
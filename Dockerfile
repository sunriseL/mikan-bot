# 使用 Python 3.11 作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml .
COPY src/ ./src/
# COPY README.md .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "nonebot2[fastapi]" && \
    pip install --no-cache-dir nb-cli && \
    nb plugin install nonebot_plugin_apscheduler && \
    nb plugin install nonebot_bison && \
    nb plugin install nonebot_plugin_alconna && \
    nb plugin install nonebot_plugin_htmlrender && \
    nb plugin install nonebot_plugin_roll && \
    pip install --no-cache-dir openai httpx

# 创建数据目录
RUN mkdir -p /app/data /app/logs

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 启动命令
CMD ["nb", "run"] 
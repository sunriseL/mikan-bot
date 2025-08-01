# Follower 插件

一个用于查询社交媒体粉丝数据的 NoneBot2 插件，通过外部 API 服务获取数据。

## 功能特性

- 📊 **粉丝趋势图表** - 查看指定用户的粉丝增长趋势
- 👥 **实时粉丝数** - 获取当前粉丝数量
- 🔧 **平台状态** - 查看各平台连接状态
- 🚀 **高性能** - 使用外部 API 服务，响应快速
- 🔄 **自动重试** - 网络错误时自动重试
- 📝 **详细日志** - 完整的请求和错误日志

## 支持平台

- **Twitter/X** - Twitter 平台粉丝数据
- **Instagram** - Instagram 平台粉丝数据  
- **YouTube** - YouTube 频道订阅数据
- **Bilibili** - B站粉丝数据

## 使用方法

### 基础命令

```
/粉丝趋势 平台 用户名    # 查看粉丝趋势图表
/当前粉丝 平台 用户名    # 查看当前粉丝数
/平台状态              # 查看各平台连接状态
/粉丝帮助              # 显示帮助信息
```

### 命令别名

```
follower_count, 粉丝趋势, 粉丝数    # 粉丝趋势图表
follower_now, 当前粉丝, 粉丝数      # 当前粉丝数
platform_status, 平台状态          # 平台状态
follower_help, 粉丝帮助            # 帮助信息
```

### 使用示例

```
/粉丝趋势 twitter kohinatamika
/当前粉丝 instagram kohinata_mika
/平台状态
/粉丝帮助
```

## 配置说明

插件配置文件：`src/plugins/follower/config.py`

```python
class FollowerConfig(BaseModel):
    api_base_url: str = "http://192.168.1.53:8000"  # API 服务地址
    api_timeout: float = 30.0                       # 请求超时时间
    retry_count: int = 3                            # 重试次数
    retry_delay: float = 1.0                        # 重试延迟
    supported_platforms: list = ["twitter", "instagram", "youtube", "bilibili"]
    cache_enabled: bool = True                      # 启用缓存
    cache_ttl: int = 300                           # 缓存时间（秒）
    log_level: str = "INFO"                        # 日志级别
    log_requests: bool = True                      # 记录请求日志
```

## API 接口

插件调用以下外部 API 接口：

- `GET /api/follower/trend/{platform}/{username}` - 获取粉丝趋势数据
- `GET /api/follower/chart/{platform}/{username}` - 获取趋势图表
- `GET /api/follower/current/{platform}/{username}` - 获取当前粉丝数
- `GET /api/platform/status` - 获取平台状态

## 错误处理

插件包含完善的错误处理机制：

- **网络错误** - 自动重试，显示友好错误信息
- **API 错误** - 解析错误响应，显示具体错误信息
- **参数错误** - 验证输入参数，提供使用说明
- **数据错误** - 处理空数据或格式错误

## 日志记录

插件会记录以下信息：

- API 请求和响应
- 错误和异常信息
- 用户操作日志
- 性能统计信息

## 依赖项

- `httpx` - HTTP 客户端
- `nonebot2` - 机器人框架
- `nonebot_plugin_apscheduler` - 定时任务

## 注意事项

1. 确保外部 API 服务正常运行
2. 检查网络连接和防火墙设置
3. 根据需要调整超时时间和重试次数
4. 定期检查 API 服务状态 
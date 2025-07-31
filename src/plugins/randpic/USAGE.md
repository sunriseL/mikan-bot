# 随机图片插件使用说明

## 快速开始

1. 将插件文件放在 `src/plugin/` 目录下
2. 在 NoneBot2 的配置文件中加载插件
3. 配置相关参数

## 配置示例

在 `.env` 文件中添加：

```env
# 随机图片插件配置
RANDPIC_COMMAND_LIST=["capoo", "meme", "cat"]
RANDPIC_STORE_DIR_PATH="data/randpic"
RANDPIC_BANNER_GROUP=[]
RANDPIC_LIMIT_VALUE=10
RANDPIC_LIMIT_INTERVAL_SECONDS=3600
```

## 基本使用

### 发送随机图片
- 在群聊中发送词条名称即可获取随机图片
- 例如：发送 "capoo" 会返回一张 capoo 的随机图片

### 添加图片
- 使用 `/添加 [词条名]` 命令
- 然后发送图片即可添加到对应词条

### 管理功能
- `/添加词条 [词条名]` - 创建新词条（需要管理员权限）
- `/添加alias [词条名] [别名]` - 为词条添加别名
- `/删除alias [别名]` - 删除别名（需要管理员权限）

### 查询功能
- `/checknsy` - 查看各词条的图片数量
- `/check_count` - 查看使用统计

## 注意事项

1. 管理员权限用户ID默认为 540729251
2. 图片会自动去重（基于MD5）
3. 支持用户使用次数限制
4. 插件会自动创建必要的文件夹和数据库 
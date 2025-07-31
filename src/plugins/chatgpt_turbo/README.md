# ChatGPT Turbo 插件

一个支持 OneAPI、DeepSeek、OpenAI 的 nonebot2 聊天机器人插件，具有上下文关联和多模态识别功能。

## 功能特性

- 支持多种大语言模型（OpenAI、DeepSeek、OneAPI）
- 多模态识别（图片+文字）
- 上下文记忆功能
- 多角色切换
- 群组独立会话管理
- DeepSeek-R1 思维链展示

## 配置说明

在 `.env` 文件中添加以下配置：

```env
# 必填：API密钥
oneapi_key="your-api-key-here"

# 可选：API地址（使用OneAPI等中转服务时需要）
oneapi_url="https://your-api-endpoint.com/v1"

# 可选：模型名称（默认：gpt-4o）
oneapi_model="gpt-4o"

# 可选：是否显示DeepSeek-R1思维链（默认：true）
r1_reason=true

# 可选：是否开启私聊（默认：true）
enable_private_chat=true
```

## 使用方法

### 基础命令

- `@机器人 [消息]` - 与机器人对话（带上下文记忆）
- `clear` - 清除当前群组的聊天记录
- `切换 [角色名]` - 切换角色（仅管理员）
- `set_limit [数字]` - 设置对话上限（仅管理员）

### 可用角色

- 小日向美香（默认）
- 樱井阳菜
- 铃原希实
- 羊宫妃那

### 示例

```
@机器人 你好！
切换 樱井阳菜
clear
set_limit 30
```

## 文件结构

```
chatgpt_turbo/
├── __init__.py          # 主插件文件
├── config.py            # 配置类定义
├── prompts.py           # 角色提示词配置
├── group_prompts.json   # 群组角色配置
└── README.md           # 说明文档
```

## 注意事项

1. 首次使用需要配置有效的 API 密钥
2. 群组角色配置会自动保存到 `group_prompts.json` 文件中
3. 每个群组有独立的会话管理，互不影响
4. 支持图片识别功能，但需要模型支持多模态输入 
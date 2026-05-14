# LLMRouter Serve - OpenAI 兼容 API 服务器

LLMRouter Serve 提供了一个与 OpenAI API 兼容的服务器，集成了智能路由功能，可以无缝对接 OpenClaw 和其他前端应用。

## 功能概述

OpenClaw Router 服务器提供以下核心功能：

- **智能路由**：自动根据查询内容选择最合适的 LLM 模型
- **OpenAI 兼容 API**：完全兼容 OpenAI Chat Completions API 格式
- **流式响应**：支持 SSE (Server-Sent Events) 流式输出
- **WebSocket 支持**：提供实时双向通信接口
- **多后端集成**：同时支持多个 LLM 提供商和模型
- **模型前缀显示**：在响应中标记实际使用的模型
- **API 密钥管理**：支持轮询多密钥和环境变量配置

## 快速开始

### 命令行启动

```bash
llmrouter serve --config serve_config.yaml --port 8000
```

### 代码集成

```python
from llmrouter.serve import create_app, run_server

# 创建应用
app = create_app(config_path="serve_config.yaml")

# 运行服务器
run_server(app, host="0.0.0.0", port=8000)
```

## 配置文件

使用 YAML 格式配置服务器：

```yaml
# 服务器设置
serve:
  host: "0.0.0.0"
  port: 8000
  show_model_prefix: true  # 在响应中显示模型名称

# 路由器配置
router:
  name: "randomrouter"  # 或 "thresholdrouter" 或自定义路由器
  config_path: "router_config.yaml"

# API 密钥
api_keys:
  openai: "${OPENAI_API_KEY}"  # 支持环境变量
  anthropic: ["sk-ant-xxx1", "sk-ant-xxx2"]  # 支持多密钥轮询

# LLM 后端配置
llms:
  gpt4:
    provider: openai
    model: gpt-4
    base_url: https://api.openai.com/v1
    api_key: "${OPENAI_API_KEY}"
    input_price: 0.03
    output_price: 0.06
    max_tokens: 4096
    context_limit: 8192

  claude3:
    provider: anthropic
    model: claude-3-opus-20240229
    base_url: https://api.anthropic.com/v1
    api_key: "${ANTHROPIC_API_KEY}"
    input_price: 0.015
    output_price: 0.075
    max_tokens: 4096
    context_limit: 200000
```

## OpenAI 兼容 API 接口

### 1. 健康检查

**端点**: `GET /health`

```bash
curl http://localhost:8000/health
```

响应示例：
```json
{
  "status": "ok",
  "router": "randomrouter",
  "llms": ["gpt4", "claude3"]
}
```

### 2. 模型列表

**端点**: `GET /v1/models`

```bash
curl http://localhost:8000/v1/models
```

响应示例：
```json
{
  "data": [
    {"id": "gpt4", "object": "model"},
    {"id": "claude3", "object": "model"}
  ]
}
```

### 3. 聊天完成（非流式）

**端点**: `POST /v1/chat/completions`

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [
      {"role": "user", "content": "你好，请介绍一下自己"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

请求参数：
- `model`: 模型名称，使用 `"auto"` 让路由器自动选择
- `messages`: 对话消息数组
- `temperature`: 温度参数 (可选)
- `max_tokens`: 最大输出 token 数 (可选，默认 4096)

响应示例：
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1715690000,
  "model": "gpt4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "[gpt4] 你好！我是一个 AI 助手..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### 4. 聊天完成（流式）

**端点**: `POST /v1/chat/completions` (带 `stream: true`)

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [
      {"role": "user", "content": "写一首关于春天的诗"}
    ],
    "stream": true
  }'
```

流式响应使用 SSE 格式：
```
data: {"id":"chatcmpl-xxx","choices":[{"delta":{"content":"[gpt4] 春天"}}]}

data: {"id":"chatcmpl-xxx","choices":[{"delta":{"content":"来了"}}]}

data: [DONE]
```

### 5. WebSocket 接口

**端点**: `WS /v1/chat/ws`

```javascript
const ws = new WebSocket('ws://localhost:8000/v1/chat/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    model: "auto",
    messages: [
      { role: "user", content: "你好" }
    ],
    temperature: 0.7,
    max_tokens: 1000
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

## 路由记忆功能

LLMRouter Serve 集成了智能路由系统，支持多种路由策略：

### 随机路由器 (RandomRouter)

平均分配请求到各个模型：

```yaml
router:
  name: "randomrouter"
```

### 阈值路由器 (ThresholdRouter)

基于负载和延迟动态选择模型：

```yaml
router:
  name: "thresholdrouter"
  config_path: "threshold_config.yaml"
```

### 自定义路由器

支持自定义路由逻辑：

```python
# custom_routers/myrouter/router.py
class MyRouter:
    def __init__(self, config_path):
        self.config = self._load_config(config_path)

    def route_single(self, query_dict):
        query = query_dict["query"]
        # 自定义路由逻辑
        return {"model_name": "gpt4"}
```

配置：
```yaml
router:
  name: "myrouter"
  config_path: "myrouter_config.yaml"
```

### 路由决策过程

1. 提取用户查询（最近一条用户消息，前 500 字符）
2. 调用路由器分析查询内容
3. 根据路由策略选择最优模型
4. 记录路由决策用于后续分析

## 多模态支持

LLMRouter Serve 支持多种 LLM 提供商和模型类型：

### 支持的提供商

- **OpenAI**: GPT-4, GPT-3.5 Turbo, GPT-4 Vision
- **Anthropic**: Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku
- **自定义**: 任何 OpenAI 兼容的 API

### 多模态示例

```yaml
llms:
  gpt4_vision:
    provider: openai
    model: gpt-4-vision-preview
    base_url: https://api.openai.com/v1
    api_key: "${OPENAI_API_KEY}"

  claude3_vision:
    provider: anthropic
    model: claude-3-opus-20240229
    base_url: https://api.anthropic.com/v1
    api_key: "${ANTHROPIC_API_KEY}"
```

### 图片输入支持

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt4_vision",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "描述这张图片"},
          {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
        ]
      }
    ]
  }'
```

## 高级功能

### 模型前缀显示

启用后，响应内容会自动添加模型名称前缀：

```yaml
serve:
  show_model_prefix: true
```

响应示例：
```
[gpt4] 根据您的查询，我建议使用 Python...
```

### API 密钥轮询

支持配置多个 API 密钥，自动轮询使用：

```yaml
api_keys:
  openai:
    - "sk-proj-xxx1"
    - "sk-proj-xxx2"
    - "sk-proj-xxx3"
```

### 环境变量支持

敏感信息可通过环境变量配置：

```yaml
api_keys:
  openai: "${OPENAI_API_KEY}"  # 从环境变量读取
  anthropic: "${ANTHROPIC_API_KEY}"
```

## 错误处理

服务器提供清晰的错误信息：

```json
{
  "error": {
    "message": "LLM 'unknown_model' not found",
    "type": "not_found_error",
    "code": 404
  }
}
```

## 性能优化

- 异步 HTTP 客户端：使用 httpx 实现高效并发请求
- 流式传输：支持实时响应，减少首字节延迟
- 连接池：复用 HTTP 连接，降低开销
- 超时控制：默认 120 秒超时，防止长时间等待

## 监控和日志

服务器会在控制台输出关键信息：

```
[OK] Router loaded: randomrouter
============================================================
  LLMRouter Serve
============================================================
  Server: http://0.0.0.0:8000
  API:    http://0.0.0.0:8000/v1/chat/completions
  Health: http://0.0.0.0:8000/health
============================================================
[Router] Query: '你好，介绍一下...' -> gpt4
```

## 常见问题

### Q: 如何禁用模型前缀？

A: 在配置文件中设置 `show_model_prefix: false`

### Q: 如何强制使用特定模型？

A: 在请求中将 `model` 参数设置为具体的模型名称，而非 "auto"

### Q: 支持哪些路由策略？

A: 内置 RandomRouter 和 ThresholdRouter，支持自定义路由器

### Q: 如何处理 API 限流？

A: 配置多个 API 密钥，系统会自动轮询使用

## 许可证

本项目遵循与 LLMRouter 相同的许可证。
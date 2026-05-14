# LLMRouter Serve API 服务说明

## 简介

LLMRouter Serve 提供了一个与 OpenAI API 兼容的服务器，集成了智能路由功能，可以无缝对接 OpenClaw 和其他前端应用。

## 架构说明

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端请求                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI 应用层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ /health      │  │ /v1/models   │  │ /v1/chat/...     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     路由层 (RouterAdapter)                    │
│  ┌──────────────────┐  ┌────────────────┐                   │
│  │ RandomRouter     │  │ 自定义路由器   │                   │
│  │ ThresholdRouter  │  │ ...            │                   │
│  └──────────────────┘  └────────────────┘                   │
│  根据 query 内容智能选择最佳 LLM 模型                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     后端层 (LLMBackend)                       │
│  管理多个 LLM 提供商 (OpenAI, Anthropic, 自定义)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     LLM 提供商 API                            │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 说明 |
|------|------|
| **ServeConfig** | 服务配置管理，支持从 YAML 文件加载配置 |
| **RouterAdapter** | 路由适配器，支持动态加载自定义路由器 |
| **LLMBackend** | LLM 后端调用器，处理与各提供商的通信 |
| **FastAPI App** | REST API 和 WebSocket 端点 |

## API 端点列表

### 1. 健康检查

**端点**: `GET /health`

检查服务健康状态。

**响应示例**:
```json
{
  "status": "ok",
  "router": "randomrouter",
  "llms": ["gpt4", "claude3"]
}
```

---

### 2. 模型列表

**端点**: `GET /v1/models`

获取所有可用模型列表。

**响应示例**:
```json
{
  "data": [
    {"id": "gpt4", "object": "model"},
    {"id": "claude3", "object": "model"}
  ]
}
```

---

### 3. 聊天完成（非流式）

**端点**: `POST /v1/chat/completions`

发送聊天请求并获取完整响应。

**请求参数**:
```json
{
  "model": "auto",           // 模型名称，"auto" 表示自动选择
  "messages": [              // 对话消息数组
    {"role": "user", "content": "你好，请介绍一下自己"}
  ],
  "temperature": 0.7,        // 温度参数（可选）
  "max_tokens": 4096,        // 最大输出 token 数（可选）
  "stream": false            // 是否流式输出
}
```

**响应示例**:
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

---

### 4. 聊天完成（流式）

**端点**: `POST /v1/chat/completions`

使用 SSE (Server-Sent Events) 格式流式返回响应。

**请求参数**:
```json
{
  "model": "auto",
  "messages": [
    {"role": "user", "content": "写一首关于春天的诗"}
  ],
  "stream": true
}
```

**响应格式**:
```
data: {"id":"chatcmpl-xxx","choices":[{"delta":{"content":"[gpt4] 春天"}}]}

data: {"id":"chatcmpl-xxx","choices":[{"delta":{"content":"来了"}}]}

data: [DONE]
```

---

### 5. WebSocket 聊天

**端点**: `WS /v1/chat/ws`

通过 WebSocket 实现实时双向通信。

**连接时发送**:
```json
{
  "model": "auto",
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**接收响应**:
```json
{
  "id": "chatcmpl-xxx",
  "choices": [
    {"delta": {"content": "[gpt4] 你好！"}}
  ]
}
```

## 配置说明

### 配置文件结构

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

### 配置参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `serve.host` | string | 服务器绑定地址 |
| `serve.port` | int | 服务器端口 |
| `serve.show_model_prefix` | bool | 是否在响应中显示模型名称 |
| `router.name` | string | 路由器名称 |
| `router.config_path` | string | 路由器配置文件路径 |
| `api_keys.{provider}` | string/list | API 密钥或密钥列表 |
| `llms.{name}.provider` | string | 提供商名称 |
| `llms.{name}.model` | string | 模型 ID |
| `llms.{name}.base_url` | string | API 基础 URL |
| `llms.{name}.api_key` | string | API 密钥 |
| `llms.{name}.input_price` | float | 输入 token 价格 |
| `llms.{name}.output_price` | float | 输出 token 价格 |
| `llms.{name}.max_tokens` | int | 最大输出 token 数 |
| `llms.{name}.context_limit` | int | 上下文窗口大小 |

## 使用示例

### 命令行启动

```bash
llmrouter serve --config serve_config.yaml --port 8000
```

### Python 代码集成

```python
from llmrouter.serve import create_app, run_server

# 创建应用
app = create_app(config_path="serve_config.yaml")

# 运行服务器
run_server(app, host="0.0.0.0", port=8000)
```

### curl 示例

```bash
# 健康检查
curl http://localhost:8000/health

# 获取模型列表
curl http://localhost:8000/v1/models

# 非流式聊天
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

# 流式聊天
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

### JavaScript/TypeScript 示例

```javascript
// Fetch API - 非流式
async function chatCompletions(message) {
  const response = await fetch('http://localhost:8000/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'auto',
      messages: [{ role: 'user', content: message }],
    }),
  });

  const data = await response.json();
  return data;
}

// WebSocket 示例
const ws = new WebSocket('ws://localhost:8000/v1/chat/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    model: 'auto',
    messages: [{ role: 'user', content: '你好' }],
    temperature: 0.7,
    max_tokens: 1000,
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

## 路由功能

### 支持的路由策略

| 路由器 | 说明 |
|--------|------|
| **randomrouter** | 随机选择模型 |
| **thresholdrouter** | 基于负载和延迟动态选择 |
| **自定义路由器** | 支持动态加载自定义路由逻辑 |

### 路由决策流程

1. 提取用户查询（最近一条用户消息，前 500 字符）
2. 调用路由器分析查询内容
3. 根据路由策略选择最优模型
4. 如模型不在可用列表，进行模糊匹配或回退

### 自定义路由器示例

```python
# custom_routers/myrouter/router.py
class MyRouter:
    def __init__(self, config_path):
        self.config = self._load_config(config_path)

    def route_single(self, query_dict):
        query = query_dict["query"]
        # 自定义路由逻辑
        if "代码" in query:
            return {"model_name": "gpt4"}
        elif "创意" in query:
            return {"model_name": "claude3"}
        else:
            return {"model_name": "gpt35"}
```

配置：
```yaml
router:
  name: "myrouter"
  config_path: "myrouter_config.yaml"
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
  openai: "${OPENAI_API_KEY}"
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

## 性能特性

- **异步处理**: 使用 httpx 实现高效并发请求
- **流式传输**: 支持 SSE 流式输出，减少首字节延迟
- **连接池**: 复用 HTTP 连接，降低开销
- **超时控制**: 默认 120 秒超时，防止长时间等待

## 监控日志

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
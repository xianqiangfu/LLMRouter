# OpenClaw Router

OpenClaw Router 是一个 OpenAI 兼容的 API 服务器，能够将每个请求智能路由到最合适的后端 LLM（Together、NVIDIA、OpenAI 兼容端点等）。它设计用于与 OpenClaw 集成，使您可以通过 Slack（以及 OpenClaw 支持的其他渠道）使用它。

## 为什么选择 OpenClaw + OpenClaw Router

将 OpenClaw（渠道 + 代理）与 OpenClaw Router（OpenAI 兼容路由层）结合使用，您可以获得：

- **Slack 原生体验**：无需构建自定义 UI，直接从移动端/桌面端与您的机器人对话
- **单一稳定端点**：OpenClaw 调用单个 `baseUrl`，而 Router 为每个请求选择最佳后端模型
- **提供商灵活性**：在 `openclaw_router/config.yaml` 中替换 Together/NVIDIA/OpenAI 兼容后端，无需修改 Slack/OpenClaw
- **密钥隔离**：上游 LLM API 密钥保留在服务器（Router）上，而非客户端
- **网络简洁性**：使用 Slack Socket 模式，通常只需要服务器的出站互联网连接；无需公共入站 Webhook URL
- **更好的运维/调试**：集中日志、健康检查和可选的 `[model]` 前缀以验证路由决策

## 特性

- **OpenAI 兼容 API**：可直接替换 OpenAI 风格的客户端（`/v1/chat/completions`）
- **HTTP 工具调用透传**：转发 OpenAI 兼容的 `tools` / `tool_choice` 字段，并在 `/v1/chat/completions` 响应中保留 `tool_calls`。Router 不执行工具本身
- **多种路由策略**：内置策略以及原始 LLMRouter 基于机器学习的路由器
- **流式支持**：端到端流式响应
- **可选模型前缀**：在响应中添加 `[model_name]` 以调试路由决策
- **多 API 密钥支持**：轮换密钥（例如 NVIDIA）以实现基本负载均衡
- **可选路由记忆（Contriever）**：持久化（查询 -> 模型）历史记录并检索 top-k 相似的过去路由以帮助 `router.strategy: llm`

## 概览

高级流程（Slack + OpenClaw + OpenClaw Router）：

```
Slack（移动端/桌面端）
        |
        | (Slack Cloud)
        v
OpenClaw（Slack 渠道，Socket 模式）
        |
        | HTTP (OpenAI 兼容): POST /v1/chat/completions  model="auto"
        v
OpenClaw Router (FastAPI, 默认 :8000)
        |
        | (路由：内置策略或原始 LLMRouter ML 路由器)
        |
        | HTTP 到提供商 (Together/NVIDIA/OpenAI 兼容)
        v
上游 LLM 提供商
```

核心思想：
- OpenClaw 表现得像一个 OpenAI 客户端
- OpenClaw Router 表现得像一个 OpenAI 兼容服务器
- OpenClaw Router 使用您在 `openclaw_router/config.yaml` 中配置的 API 密钥调用您的真实模型提供商

## 安装

Python 依赖由主项目打包管理。遵循仓库根目录的安装说明：
- 参见 `../README.md`

如果您需要 Slack 集成，还需要 OpenClaw（Node.js）。OpenClaw 有严格的 Node.js 版本要求；如果您看到语法错误或版本错误，请升级 Node（通常通过 `nvm`）。

### 安装 OpenClaw（Slack / Discord 网关）

1) 安装较新的 Node.js（推荐：通过 `nvm`）

OpenClaw 的最低 Node 版本可能会随时间变化。如果您运行 `openclaw` 并且它说"requires Node >= X"，请安装该版本（或更新的）。在我们的设置中，OpenClaw 需要 Node 22+。

```bash
# 安装 nvm (Linux/macOS)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# 为当前 shell 加载 nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

# 安装并使用现代 Node.js（例如：22）
nvm install 22
nvm use 22

node -v
npm -v
```

如果 `nvm use` 警告关于 `.npmrc` `prefix`/`globalconfig` 冲突，请删除 npm prefix 设置（或运行建议的 `nvm use --delete-prefix ...`）。最简单的目标是：您的 `node` 和 `npm` 应该来自 `~/.nvm/...` 路径，全局安装不应尝试写入 `/usr/local/...`。

2) 安装 OpenClaw

```bash
npm install -g openclaw
openclaw --version
openclaw doctor
```

常见安装/运行时问题：
- `npm ERR! EACCES ... /usr/local/lib/node_modules`：您正尝试全局安装到 root 拥有的目录。使用 `nvm`（推荐）使全局安装进入您的用户目录，或修复 npm 权限/prefix
- `openclaw requires Node >= ...`：将 Node 升级到所需版本并重试
- `openclaw: command not found`：您的 npm global bin 不在 `PATH` 上（或您在新的 shell/session 中 `nvm` 未加载）

## 配置摘要

通常需要配置 2 个文件：

1. `openclaw_router/config.yaml`
   - 控制哪些后端模型存在、路由如何工作以及调用上游提供商时使用哪些 API 密钥

2. `~/.openclaw/openclaw.json`
   - 告诉 OpenClaw 如何调用 OpenClaw Router（作为自定义模型提供商）
   - 配置用于接收事件的 Slack 令牌和 Socket 模式

注意：`~/.openclaw/openclaw.json` 是完整的 OpenClaw 配置。您应该编辑/合并特定部分，而不是替换整个文件。

## 分步指南（推荐：一个脚本启动 Router + Gateway）

### 1) 配置 OpenClaw Router 后端（API 密钥在此）

编辑 `openclaw_router/config.yaml`。

注意：
- `api_keys` 部分在 OpenClaw Router 调用上游提供商时使用。这是您放置 Together/NVIDIA/OpenAI 密钥的地方
- OpenClaw 不需要上游提供商密钥。OpenClaw 只调用您的 Router

示例：Together（OpenAI 兼容）

```yaml
serve:
  host: "0.0.0.0"
  port: 8000
  show_model_prefix: true

router:
  strategy: llm
  provider: together
  base_url: https://api.together.xyz/v1
  model: meta-llama/Llama-3.1-8B-Instruct-Turbo

api_keys:
  together: ${TOGETHER_API_KEY}

llms:
  llama-3.1-8b:
    description: "快速聊天"
    provider: together
    model: meta-llama/Llama-3.1-8B-Instruct-Turbo
    base_url: https://api.together.xyz/v1
    max_tokens: 1024
    context_limit: 128000

  qwen2.5-72b:
    description: "更强的推理能力"
    provider: together
    model: Qwen/Qwen2.5-72B-Instruct-Turbo
    base_url: https://api.together.xyz/v1
    max_tokens: 1024
    context_limit: 32768
```

### 2) 配置 OpenClaw 调用您的 Router（provider: `openclaw`）

在 `~/.openclaw/openclaw.json` 中，确保在 `models.providers.openclaw` 下存在这些键。

这是一个片段（合并到您现有的 JSON 中）：

```json
{
  "models": {
    "providers": {
      "openclaw": {
        "api": "openai-completions",
        "baseUrl": "http://127.0.0.1:8000/v1",
        "apiKey": "not-needed",
        "models": [{"id": "auto", "name": "OpenClaw Router"}]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {"primary": "openclaw/auto"}
    }
  }
}
```

重要字段的含义：
- `baseUrl`：OpenClaw 将发送请求到的 Router 地址。Router 监听您在 `openclaw_router/config.yaml` 中设置的 `serve.port`
  - 如果 OpenClaw 和 Router 在同一台机器上运行，使用 `http://127.0.0.1:<port>/v1`
  - 如果它们在不同的机器/容器上运行，`localhost` 将是错误的。使用可访问的 IP/主机名
- `api`：OpenClaw 用于与您的 `baseUrl` 通信的协议。OpenClaw Router 是 OpenAI 兼容的，所以使用 `openai-completions`
- `apiKey`：如果您的 Router 不强制认证，可以是占位符。它不是 Together/NVIDIA/OpenAI 的密钥

如果您更改 Router 端口（例如使用 `./scripts/start-openclaw.sh -p 9000`），您还必须更新 `baseUrl` 以匹配。

安全补丁（推荐）：这仅更新相关键，并保持 OpenClaw 配置的其余部分完整。

```bash
python - <<'PY'
import json
from pathlib import Path

p = Path.home() / ".openclaw" / "openclaw.json"
cfg = json.loads(p.read_text())

models = cfg.setdefault("models", {})
models.setdefault("mode", "merge")
providers = models.setdefault("providers", {})
claw = providers.setdefault("openclaw", {})

claw["api"] = "openai-completions"
claw["baseUrl"] = "http://127.0.0.1:8000/v1"
claw.setdefault("apiKey", "not-needed")
claw.setdefault("models", [{"id": "auto", "name": "OpenClaw Router"}])

agents = cfg.setdefault("agents", {})
defaults = agents.setdefault("defaults", {})
defaults.setdefault("model", {})["primary"] = "openclaw/auto"

p.write_text(json.dumps(cfg, indent=2))
print("updated", p)
PY
```

首次设置时可选但推荐：
- 确保 `gateway.mode` 设置为 `local`，否则 `openclaw gateway run` 可能会被阻止

```json
{
  "gateway": { "mode": "local" }
}
```

### 3) 在 OpenClaw 中配置 Slack（Socket 模式）

OpenClaw 的 Slack 配置在 `channels.slack` 下（较新版本已从 `slack.*` 迁移）。

在 `~/.openclaw/openclaw.json` 中，确保您有：

```json
{
  "channels": {
    "slack": {
      "enabled": true,
      "mode": "socket",
      "botToken": "xoxb-your-bot-token",
      "appToken": "xapp-your-app-token"
    }
  }
}
```

#### Slack 应用设置清单（Socket 模式）

1. 在您的工作区中创建一个 Slack 应用（从零开始）
2. 添加一个 Bot 用户
3. 启用 Socket 模式
4. 创建一个应用级令牌（这将成为您的 `xapp-...` 令牌）：
   - 范围：`connections:write`
   - Slack 仅显示此令牌一次。如果丢失，创建一个新的
5. OAuth & Permissions：
   - 仅供提及机器人的最小范围：`app_mentions:read`、`chat:write`
   - 如果您需要 DM 支持和消息事件，通常还需要：`im:history`（以及可选的 `im:read`）
6. 事件订阅（bot 事件）：
   - `app_mention`（推荐）
   - `message.im`（如果您想要 DM）
   - 可选 `message.channels`（如果您想要频道消息）
7. 更改范围/事件后，将应用安装（或重新安装）到您的工作区
8. 在 Slack 中，将机器人邀请到您希望其响应的频道（对于公共频道）

在 Slack UI 中找到令牌的位置：
- Bot 令牌（`xoxb-...`）："OAuth & Permissions" -> "Bot User OAuth Token"
- App 令牌（`xapp-...`）："Socket Mode" -> "App-Level Tokens"（Slack 只显示一次）

在 Slack UI 中配置事件订阅的位置：
- "Event Subscriptions"（左侧边栏 Features 下）
  - 在 Socket 模式中，事件通过 WebSocket 传递；通常不需要公共 Request URL
  - 添加事件后，单击页面底部的 **Save Changes**（容易遗漏）

### 4) 启动所有服务（Router + OpenClaw Gateway）

从仓库根目录：

```bash
./scripts/start-openclaw.sh
```

此脚本需要 `bash`（Linux/macOS）。在 Windows 上，在 WSL 下运行，或在单独的终端中启动 Router 和 OpenClaw。

常用选项：

```bash
./scripts/start-openclaw.sh -c openclaw_router/config.yaml
./scripts/start-openclaw.sh -p 9000
./scripts/start-openclaw.sh -r knnrouter --router-config configs/model_config_test/knnrouter.yaml
./scripts/start-openclaw.sh --no-gateway
```

日志：
- Router：`/tmp/openclaw.log`
- Gateway：`/tmp/openclaw-gateway.log`

停止所有服务：

```bash
./scripts/stop-openclaw.sh
```

### 5) 配对/访问批准（许多设置中默认需要）

如果 Slack 说类似"access not configured"并显示配对代码，请在服务器上批准：

```bash
openclaw pairing approve slack <pairing-code>
```

批准后，再次尝试向机器人发送 DM 或在频道中提及它。

## 配置参考

### 主 Router 配置（`openclaw_router/config.yaml`）

最小形状：

```yaml
serve:
  host: "0.0.0.0"
  port: 8000
  show_model_prefix: true

router:
  strategy: random   # random | round_robin | rules | llm | llmrouter

api_keys:
  together: ${TOGETHER_API_KEY}    # 或字面密钥字符串
  nvidia:
    - nvapi-...                    # 列表 = 基本密钥轮换

llms:
  some-model:
    provider: together
    model: meta-llama/Llama-3.1-8B-Instruct-Turbo
    base_url: https://api.together.xyz/v1
    description: "..."
    max_tokens: 1024
    context_limit: 128000
```

关键字段：
- `serve.host` / `serve.port`：OpenClaw Router 监听的位置
- `router.strategy`：
  - `random` / `round_robin` / `rules`：确定性/简单路由
  - `llm`：使用"router LLM"选择后端模型
    - 如果 `auth_mode` 解析为 `bearer`，则需要 API 密钥
    - 如果 `auth_mode` 解析为 `none`（对于本地 OpenAI 兼容后端），密钥是可选的
  - `llmrouter`：使用原始 LLMRouter 基于机器学习的路由器
- `api_keys`：OpenClaw Router 调用上游提供商时使用的密钥
  - 支持环境变量如 `${TOGETHER_API_KEY}`
- `llms`：您的后端模型池（Router 为每个请求选择其中一个）
  - 您可以在一个池中混合框架（例如 `sglang`、`vllm`、`llama_cpp`、`lmstudio`、`huggingface_cli`、云提供商）

OpenAI 兼容适配器字段（在 `router` 和每个 `llms.<name>` 中均支持）：
- `provider_type`：目前为 `openai_compatible`（为将来扩展保留）
- `auth_mode`：`auto | bearer | none`
- `chat_path`：默认为 `/chat/completions`
- `local`：可选的布尔覆盖，用于在 `auto` 模式中进行本地检测

示例：本地多框架池

```yaml
llms:
  sglang_qwen:
    provider: sglang
    model: Qwen/Qwen2.5-7B-Instruct
    base_url: http://127.0.0.1:30000/v1
    auth_mode: none

  vllm_llama:
    provider: vllm
    model: meta-llama/Llama-3.1-8B-Instruct
    base_url: http://127.0.0.1:8001/v1
    auth_mode: none

  lmstudio_local:
    provider: lmstudio
    model: local-model
    base_url: http://127.0.0.1:1234/v1
    auth_mode: none
```

可选路由记忆（检索增强路由）：

```yaml
memory:
  enabled: true
  # 如果省略/为空，默认为：~/.llmrouter/openclaw_memory.jsonl
  path: "${HOME}/.llmrouter/openclaw_memory.jsonl"
  top_k: 10
  retriever_model: "facebook/contriever-msmarco"
  device: "cpu"          # "cpu" 或 "cuda"
  max_length: 256
  max_query_chars: 500
  max_prompt_chars: 200
  per_user: false
```

注意：
- Memory 将（查询 -> 选定模型）对持久化到 JSONL 文件，并检索 top-k 相似的过去查询
- 目前，memory 仅用于增强 `router.strategy: llm`（router LLM 提示获取检索到的对）
- 首次运行将下载检索器模型（如果不存在）（需要出站互联网）

可选媒体理解（将图像/音频/视频转换为文本描述）：

```yaml
media:
  enabled: true
  # 使用 Together AI API（与 api_keys.together 相同的密钥）
  api_key_env: "TOGETHER_API_KEY"
  base_url: "https://api.together.xyz/v1"
  # 用于图像/视频理解的视觉模型（Qwen3-VL 推荐用于无服务器）
  vision_model: "Qwen/Qwen3-VL-8B-Instruct"
  # 音频转录模型（Whisper）
  audio_model: "openai/whisper-large-v3"
  # 提示词
  image_prompt: "用 2-3 句话简要描述这张图片。"
  video_prompt: "描述您在这些视频帧中看到的内容。"
  # 视频处理
  video_max_frames: 4
  # 最大描述长度
  max_description_chars: 500
```

**媒体理解流程：**

启用媒体理解后，router 会自动：

1. **检测传入消息中的媒体**（支持两种格式）：
   - OpenAI 多模态格式：`{"type": "image_url", "image_url": {"url": "data:image/..."}}`
   - OpenClaw 格式：`[media attached: /path/to/file (mime/type) | optional_url]`

2. **将媒体转换为文本**：
   - 图像 → Vision API (Qwen3-VL) → 文本描述
   - 音频 → Whisper API → 转录文本
   - 视频 → 帧提取 + Vision API → 描述

3. **替换消息内容中的媒体占位符**，使用生成的文本描述，以便 LLM 理解图像/音频/视频中的内容

4. **使用处理后的文本**进行路由决策（选择哪个模型）

**示例流程：**
```
用户发送："[media attached: photo.png (image/png)]"
           ↓
Vision API："图像显示一只猫坐在沙发上。"
           ↓
LLM 收到："[图像：图像显示一只猫坐在沙发上。]"
           ↓
LLM 基于图像描述进行响应
```

注意：
- 图像描述使用 Together AI 的 Qwen3-VL-8B-Instruct 视觉模型（无服务器兼容）
- 音频转录使用 Together AI 的 Whisper Large v3
- 视频处理提取关键帧并描述它们（需要 `opencv-python`）
- 如果还启用了 memory，组合的文本（原始 + 媒体描述）将存储用于检索

LLMRouter 策略配置（支持两种等效形式）：

```yaml
router:
  strategy: llmrouter
  llmrouter:
    name: knnrouter
    config_path: configs/model_config_test/knnrouter.yaml
    model_path: saved_models/knnrouter.pt  # 可选
```

或：

```yaml
router:
  strategy: llmrouter
  name: knnrouter
  config_path: configs/model_config_test/knnrouter.yaml
  model_path: saved_models/knnrouter.pt  # 可选
```

## 路由策略（内置 + 原始 LLMRouter）

OpenClaw Router 支持两个路由族：

1) 内置策略（在 `openclaw_router/config.yaml` 中配置 `router.strategy`）
- `random`：随机选择后端模型（可选择加权）
- `round_robin`：循环遍历后端模型
- `rules`：关键词规则（将关键词映射到特定后端模型）
- `llm`：使用小型"router LLM"选择后端模型
  - 使用 `router.provider`、`router.base_url`、`router.model` 和（如果需要）您的 `api_keys` 调用 router LLM

路由粒度说明：
- 默认情况下，路由是请求级别的，而非代理身份级别
- 如果 OpenClaw 发送 `model: "auto"`，router 根据请求内容进行每请求决策
- 如果需要严格的每代理绑定，请在 OpenClaw 中配置显式模型名称，或添加确定性 `rules`

2) 原始 LLMRouter 基于机器学习的路由器（学习型路由器）
- 设置 `router.strategy: llmrouter` 并选择路由器名称（例如 `knnrouter`、`mlprouter`、`svmrouter` 等）
- 使用启动脚本，可以通过 `-r` 传递路由器名称（以及可选的 `--router-config`）：

```bash
./scripts/start-openclaw.sh -r knnrouter
./scripts/start-openclaw.sh -r knnrouter --router-config configs/model_config_test/knnrouter.yaml
```

路由器配置自动检测：
- 如果不传递 `--router-config`，OpenClaw Router 将尝试（按顺序）：
  - `configs/model_config_test/<router>.yaml`
  - `custom_routers/<router>/config.yaml`
  - `configs/model_config_train/<router>.yaml`

列出路由器：
- `llmrouter list-routers`
- 或：`./scripts/start-openclaw.sh --list-routers`

有关训练 ML 路由器和准备路由器配置，请遵循主项目文档：
- 参见 `../README.md`

## 命令行选项

### 启动脚本（`./scripts/start-openclaw.sh`）

这是 Slack 的推荐入口点：它同时启动 OpenClaw Router 和 OpenClaw Gateway。

| 选项 | 描述 |
|--------|-------------|
| `-c, --config FILE` | 配置文件路径（默认：`openclaw_router/config.yaml`） |
| `-p, --port PORT` | Router 端口（默认：`8000`） |
| `-r, --router NAME` | 路由器名称或内置策略（例如 `random`、`llm`、`knnrouter`） |
| `--router-config FILE` | 路由器特定的配置文件路径（可选；如果省略则自动检测） |
| `--no-gateway` | 不启动 OpenClaw Gateway |
| `--no-prefix` | 不在响应中添加模型名称前缀 |
| `--list-routers` | 列出可用的原始 LLMRouter 路由器 |
| `-h, --help` | 显示帮助消息 |

### 仅 Router 替代方案（无需 Bash 脚本）

如果您不想使用 bash 脚本：

```bash
# 启动 Router（OpenAI 兼容 API）
llmrouter serve --config openclaw_router/config.yaml

# 可选：使用原始 LLMRouter ML 路由器
llmrouter serve --config openclaw_router/config.yaml \
  --router knnrouter \
  --router-config configs/model_config_test/knnrouter.yaml

# 在另一个终端中启动 OpenClaw Gateway（需要 gateway.mode=local）
openclaw gateway run --bind loopback --port 18789 --force
```

## API 端点

运行后，可以使用以下端点：

| 端点 | 方法 | 描述 |
|----------|--------|-------------|
| `/health` | GET | 健康检查 |
| `/v1/chat/completions` | POST | 聊天完成（OpenAI 兼容） |
| `/v1/models` | GET | 列出可用模型 |
| `/v1/chat/ws` | WS | 实时流式聊天（WebSocket） |
| `/routers` | GET | 列出可用的路由策略 |

快速检查：

```bash
curl -s http://127.0.0.1:8000/health

curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Hello from OpenAI-compatible client"}]
  }'

# 流式
curl -N http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Hello (streaming)"}],
    "stream": true
  }'

# WebSocket 流式
# 参见 tests/test_websocket.py 获取 Python 客户端示例
```

## 使用示例

```bash
# 使用内置随机策略
./scripts/start-openclaw.sh -r random

# 使用内置轮询策略
./scripts/start-openclaw.sh -r round_robin

# 使用基于 LLM 的路由（使用小模型进行决策）
./scripts/start-openclaw.sh -r llm

# 使用原始 LLMRouter ML 路由器
./scripts/start-openclaw.sh -r knnrouter

# 使用显式路由器配置文件的 ML 路由器
./scripts/start-openclaw.sh -r knnrouter --router-config configs/model_config_test/knnrouter.yaml

# 自定义端口
./scripts/start-openclaw.sh -p 9000

# 启动而不启动 OpenClaw Gateway（仅 API）
./scripts/start-openclaw.sh --no-gateway
```

## 架构

### 完整集成（通过 OpenClaw 的 Slack）

```
+----------------+     +------------------------+     +------------------+
| Slack 用户     | --> | OpenClaw Gateway       | --> | OpenClaw Router    |
| (移动端/桌面端)|     | (port 18789, socket)  |     | (port 8000, /v1)  |
+----------------+     +------------------------+     +--------+---------+
                                                          |
                               +--------------------------+--------------------+
                               |                          |                    |
                               v                          v                    v
                         +-----------+              +-----------+        +-----------+
                         | LLaMA     |              | Qwen      |        | Mistral   |
                         +-----------+              +-----------+        +-----------+
```

### 独立模式（仅 API）

```
+-----------------------------------------------+
| 客户端（curl / OpenAI SDK / OpenClaw 等）   |
+---------------------------+-------------------+
                            |
                            v
+-----------------------------------------------------------+
| OpenClaw Router (port 8000)                                |
| - 内置: random / round_robin / rules / llm               |
| - 原始 LLMRouter 路由器: knnrouter / mlprouter / ...       |
+---------------------------+-------------------------------+
                            |
        +-------------------+-------------------+
        v                   v                   v
  +-----------+       +-----------+       +-----------+
  | LLaMA     |       | Qwen      |       | Mistral   |
  +-----------+       +-----------+       +-----------+
```

### 核心组件

```
openclaw_router/
├── __init__.py         # 模块导出
├── __main__.py         # CLI 入口点
├── server.py           # FastAPI 服务器实现
├── config.py           # 配置类和数据结构
├── config.yaml         # 主配置文件
├── routers.py          # 路由策略实现
├── memory.py           # 路由记忆（检索增强）
└── media.py            # 媒体理解（图像/音频/视频）
```

## 目录结构

```
LLMRouter/
  scripts/
    start-openclaw.sh        # 启动 OpenClaw Router + OpenClaw Gateway
    stop-openclaw.sh         # 停止所有服务
  configs/
    openclaw_example.yaml
  openclaw_router/
    __init__.py             # 模块导出
    __main__.py             # CLI 入口点
    server.py               # FastAPI 服务器
    config.py               # 配置类
    config.yaml             # 主配置文件
    routers.py              # 路由策略
    memory.py               # 路由记忆
    media.py                # 媒体理解
    README_CN.md            # 本文件
  custom_routers/
    randomrouter/           # 示例自定义路由器
      config.yaml
```

## 日志

- Router 日志：`/tmp/openclaw.log`
- Gateway 日志：`/tmp/openclaw-gateway.log`

实时查看日志：

```bash
tail -f /tmp/openclaw.log
```

## 故障排除

### "No API provider registered for api: undefined" (OpenClaw)

您的 `models.providers.<name>.api` 缺失。添加：
- `models.providers.openclaw.api = "openai-completions"`

### Slack 什么也没收到 / 机器人从不回复

检查清单：
- OpenClaw 是否运行并已连接（Socket 模式）？
  - 检查 `/tmp/openclaw-gateway.log`
- 您在更新范围后安装（或重新安装）了 Slack 应用吗？
- 您添加了正确的 bot 事件（例如 `app_mention`、`message.im`）吗？
- 机器人在频道中吗（邀请它）？
- OpenClaw 打印了仍需要批准的配对代码吗？

### "OpenClaw: access not configured"（配对）

如果 OpenClaw 打印配对代码，请在服务器上批准：

```bash
openclaw pairing approve slack <pairing-code>
```

### 端口已被占用

如果 Router 端口已被占用，启动脚本将尝试停止先前的 Router 进程。您也可以手动停止服务：

```bash
./scripts/stop-openclaw.sh
```

### Router 未加载（ML 路由器）

如果您使用 `-r <router>` 启动但它未加载：
- 尝试显式传递 `--router-config`（参见本 README 中的示例）
- 或检查自动检测路径之一是否存在：
  - `configs/model_config_test/<router>.yaml`
  - `custom_routers/<router>/config.yaml`
  - `configs/model_config_train/<router>.yaml`

### "No module named openclaw_router"

这通常意味着您使用的 Python 环境未安装此仓库，或者您从不同的目录/会话运行。

修复：
- 激活正确的虚拟环境，并以可编辑模式安装仓库：

```bash
pip install -e .
```

### 使用 `router.strategy: llm` 响应缓慢

`llm` 策略进行两次上游调用：
1) 调用 router LLM 决定使用哪个后端模型
2) 调用选定的后端模型生成最终答案

如果您想要更低的延迟，请使用 `random` 或 `round_robin`。

### 内部网络 / VPN

您的手机网络不需要直接访问您的服务器。

只要运行 OpenClaw 的服务器可以通过互联网（出站）访问 Slack，Slack 集成就可以工作。Socket 模式不需要公共入站 Webhook URL。

### "openclaw requires Node >= ..."

升级 Node.js，然后在需要时重新安装 OpenClaw：
- 首选 `nvm` 并使用 OpenClaw 需要的现代 Node 版本

## 与 OpenClaw Gateway 集成

### 工作原理

OpenClaw Gateway 是一个 Node.js 应用，充当 Slack、Discord 等聊天渠道与 LLM API 之间的桥梁。当与 OpenClaw Router 配合使用时：

1. **用户通过 Slack 发送消息**
2. **OpenClaw Gateway 接收消息**（通过 Socket 模式）
3. **Gateway 调用 OpenClaw Router**（通过 HTTP POST 到 `/v1/chat/completions`）
4. **Router 选择最佳模型**并调用后端 API
5. **响应返回给 Gateway**，然后发送回 Slack

### 配置要点

1. **Gateway 模式**：设置为 `local` 以启用本地运行
   ```json
   {"gateway": {"mode": "local"}}
   ```

2. **Provider 定义**：在 `~/.openclaw/openclaw.json` 中定义 `openclaw` provider
   ```json
   {
     "models": {
       "providers": {
         "openclaw": {
           "api": "openai-completions",
           "baseUrl": "http://127.0.0.1:8000/v1",
           "apiKey": "not-needed"
         }
       }
     }
   }
   ```

3. **代理配置**：设置默认模型使用 `openclaw/auto`
   ```json
   {
     "agents": {
       "defaults": {
         "model": {"primary": "openclaw/auto"}
       }
     }
   }
   ```

### 部署建议

1. **开发环境**：
   - Router 和 Gateway 在同一台机器上运行
   - 使用 `localhost` 或 `127.0.0.1` 进行通信

2. **生产环境**：
   - 考虑使用 Docker 或 systemd 服务
   - 配置日志轮转
   - 设置健康检查端点监控
   - 使用适当的 `baseUrl`（如果 Router 在不同机器上）

3. **网络要求**：
   - Router 需要出站互联网访问上游 LLM API
   - Gateway 需要 Socket 模式访问 Slack
   - 客户端不需要直接访问 Router（通过 Slack Cloud 转发）

## 支持

- 插件系统源码：`llmrouter/plugin_system.py`
- MetaRouter 基类：`llmrouter/models/meta_router.py`
- 推理 CLI：`llmrouter/cli/router_inference.py`
- 训练 CLI：`llmrouter/cli/router_train.py`
- 示例：研究 `randomrouter` 和 `thresholdrouter`
- GitHub Issues：报告错误或请求功能

---

愉快路由！🚀
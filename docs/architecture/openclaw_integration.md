# OpenClaw 集成架构图

## 1. 完整集成架构（Slack + OpenClaw Gateway + Router）

```mermaid
graph TB
    %% 用户和消息平台层
    subgraph UserLayer["用户和消息平台层"]
        MobileUser["移动端用户<br/>Slack App"]
        DesktopUser["桌面端用户<br/>Slack Client"]
        SlackCloud["Slack Cloud<br/>消息转发服务"]
    end

    %% OpenClaw Gateway 层
    subgraph GatewayLayer["OpenClaw Gateway 层"]
        GatewayApp["OpenClaw Gateway<br/>Node.js 应用"]
        SlackChannel["Slack 渠道<br/>Socket 模式"]
        DiscordChannel["Discord 渠道<br/>WebSocket"]
        AgentSystem["代理系统<br/>Agent 配置"]
    end

    %% OpenClaw Router 层
    subgraph RouterLayer["OpenClaw Router 层"]
        FastAPIServer["FastAPI 服务器<br/>端口: 8000"]
        OpenAIEndpoint["OpenAI 兼容端点<br/>/v1/chat/completions"]

        subgraph RoutingStrategies["路由策略"]
            RandomStrategy["Random<br/>随机选择"]
            RoundRobin["Round Robin<br/>轮询"]
            RulesStrategy["Rules<br/>关键词规则"]
            LLMS["LLM<br/>小型路由模型"]
            LLMRouter["LLMRouter<br/>机器学习路由器"]
        end

        subgraph RouterFeatures["Router 功能"]
            MemoryFeature["路由记忆<br/>检索增强"]
            MediaFeature["媒体理解<br/>图像/音频/视频"]
            PrefixFeature["模型前缀<br/>调试标签"]
        end
    end

    %% LLM 提供商层
    subgraph ProviderLayer["LLM 提供商层"]
        Together["Together AI<br/>API: api.together.xyz"]
        NVIDIA["NVIDIA NIM<br/>API: build.nvidia.com"]
        OpenAI["OpenAI<br/>api.openai.com"]
        LocalvLLM["vLLM<br/>本地模型"]
        LocalSGLang["SGLang<br/>本地模型"]
        LocalOllama["Ollama<br/>本地模型"]
    end

    %% 数据存储层
    subgraph StorageLayer["数据存储层"]
        RouterConfig["路由配置<br/>config.yaml"]
        OpenClawConfig["OpenClaw 配置<br/>~/.openclaw/openclaw.json"]
        MemoryFile["路由记忆<br/>openclaw_memory.jsonl"]
    end

    %% 连接关系
    MobileUser -->|Slack 客户端| SlackCloud
    DesktopUser -->|Slack 客户端| SlackCloud
    SlackCloud -->|Socket 模式<br/>WebSocket| SlackChannel
    SlackChannel --> GatewayApp
    DiscordChannel --> GatewayApp

    GatewayApp -->|HTTP POST<br/>OpenAI 兼容| OpenAIEndpoint
    OpenAIEndpoint --> FastAPIServer

    FastAPIServer --> RoutingStrategies
    FastAPIServer --> RouterFeatures

    RoutingStrategies -->|选择最佳模型| ProviderLayer

    MemoryFeature -->|检索历史路由| MemoryFile
    MediaFeature -->|视觉/音频 API| Together

    GatewayApp -->|加载配置| OpenClawConfig
    FastAPIServer -->|加载配置| RouterConfig

    %% 样式
    classDef userLayer fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef gatewayLayer fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef routerLayer fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef providerLayer fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    classDef storageLayer fill:#eceff1,stroke:#455a64,stroke-width:2px

    class MobileUser,DesktopUser,SlackCloud userLayer
    class GatewayApp,SlackChannel,DiscordChannel,AgentSystem gatewayLayer
    class FastAPIServer,OpenAIEndpoint,RandomStrategy,RoundRobin,RulesStrategy,LLMS,LLMRouter,MemoryFeature,MediaFeature,PrefixFeature routerLayer
    class Together,NVIDIA,OpenAI,LocalvLLM,LocalSGLang,LocalOllama providerLayer
    class RouterConfig,OpenClawConfig,MemoryFile storageLayer
```

## 2. 请求流向详解

```mermaid
sequenceDiagram
    participant User as 用户
    participant Slack as Slack Cloud
    participant Gateway as OpenClaw Gateway
    participant Router as OpenClaw Router
    participant Strategy as 路由策略
    participant Provider as LLM 提供商

    User->>Slack: 发送消息（文本/媒体）
    Slack->>Gateway: Socket 模式转发消息
    Gateway->>Router: POST /v1/chat/completions
    Note over Router: 加载配置

    alt 媒体处理
        Router->>Provider: 调用视觉/音频 API
        Provider-->>Router: 返回媒体描述
        Note over Router: 替换消息内容
    end

    alt 路由记忆启用
        Router->>Router: 检索历史路由
        Note over Router: 检索 top-k 相似查询
    end

    Router->>Strategy: 执行路由决策

    opt 内置策略
        alt Random/RoundRobin
            Strategy->>Strategy: 随机/轮询选择
        else Rules
            Strategy->>Strategy: 关键词匹配
        else LLM
            Strategy->>Provider: 调用路由 LLM
            Provider-->>Strategy: 返回选定模型
        end
    end

    opt ML 路由器
        Strategy->>Strategy: 加载模型和嵌入
        Strategy->>Strategy: 预测最佳模型
    end

    Strategy->>Router: 返回选定的模型
    Router->>Provider: POST 到选定模型 API
    Provider-->>Router: 返回 LLM 响应

    opt 模型前缀
        Router->>Router: 添加 [model_name] 前缀
    end

    alt 路由记忆启用
        Router->>Router: 保存（查询 -> 模型）对
    end

    Router-->>Gateway: 返回响应
    Gateway-->>Slack: 发送响应
    Slack-->>User: 显示消息
```

## 3. 部署架构（生产环境）

```mermaid
graph TB
    subgraph ClientSide["客户端"]
        UserDevice["用户设备<br/>移动端/桌面端<br/>Slack/Discord 客户端"]
    end

    subgraph CloudPlatform["云平台（Slack/Discord）"]
        SlackService["Slack 服务<br/>消息中继"]
    end

    subgraph ServerSide["服务器（VPS/云服务器）"]
        subgraph OpenClawGW["OpenClaw Gateway"]
            GWProcess["openclaw gateway run<br/>Node.js 进程"]
            GWSocket["Socket 连接<br/>端口: 18789"]
            GWConfig["~/.openclaw/openclaw.json"]
            GWLog["/tmp/openclaw-gateway.log"]
        end

        subgraph OpenClawRT["OpenClaw Router"]
            RTProcess["llmrouter serve<br/>Python/FastAPI 进程"]
            RTAPI["OpenAI API<br/>端口: 8000"]
            RTConfig["openclaw_router/config.yaml"]
            RTLog["/tmp/openclaw.log"]
            RTMemory["路由记忆<br/>.llmrouter/openclaw_memory.jsonl"]
        end

        subgraph InitScripts["初始化脚本"]
            StartScript["start-openclaw.sh<br/>启动 Router + Gateway"]
            StopScript["stop-openclaw.sh<br/>停止所有服务"]
        end
    end

    subgraph ExternalServices["外部服务"]
        LLMProviders["LLM API 提供商<br/>Together / NVIDIA / OpenAI"]
        Internet["互联网连接<br/>出站访问"]
    end

    %% 连接关系
    UserDevice -->|HTTPS/WSS| SlackService
    SlackService -->|WebSocket<br/>Socket 模式| GWSocket
    GWSocket --> GWProcess
    GWProcess -->|HTTP POST<br/>localhost:8000| RTAPI
    RTAPI --> RTProcess

    GWProcess -->|读取| GWConfig
    RTProcess -->|读取| RTConfig
    RTProcess -->|读写| RTMemory

    StartScript --> GWProcess
    StartScript --> RTProcess
    StopScript -.-> GWProcess
    StopScript -.-> RTProcess

    RTProcess -->|HTTPS API 调用| LLMProviders
    LLMProviders --> Internet
    GWSocket --> Internet

    %% 样式
    classDef clientSide fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef cloudPlatform fill:#fff9c4,stroke:#f9a825,stroke-width:2px
    classDef serverSide fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    classDef externalServices fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px

    class UserDevice clientSide
    class SlackService cloudPlatform
    class GWProcess,GWSocket,GWConfig,GWLog,RTProcess,RTAPI,RTConfig,RTLog,RTMemory,StartScript,StopScript serverSide
    class LLMProviders,Internet externalServices
```

## 4. 路由策略分类

```mermaid
mindmap
  root((OpenClaw Router<br/>路由策略))
    内置策略
      Random
        随机选择模型
        支持加权
      RoundRobin
        循环遍历模型
        负载均衡
      Rules
        关键词匹配
        规则引擎
      LLM
        使用小型 LLM 决策
        基于内容路由
    ML 路由器
      KNN Router
        K 近邻路由
        基于嵌入相似度
      MLP Router
        多层感知机
        深度学习
      SVM Router
        支持向量机
        分类器
      Router-R1
        多轮对话路由
        预训练模型
      GMT Router
        图多任务路由
        个性化
      Graph Router
        图神经网络
        结构化路由
    代理路由
      KNN Multi-Round
        多轮 KNN 路由
        对话上下文
      LLM Multi-Round
        多轮 LLM 路由
        自适应路由
    高级功能
      路由记忆
        检索增强
        历史匹配
      媒体理解
        图像描述
        音频转录
        视频帧提取
```

## 5. 组件关系详解

### OpenClaw Gateway 与 Router 的关系

| 组件 | 技术 | 端口 | 协议 | 职责 |
|------|------|------|------|------|
| OpenClaw Gateway | Node.js | 18789 | WebSocket (Slack) + HTTP | 消息平台与 LLM API 之间的桥梁 |
| OpenClaw Router | Python/FastAPI | 8000 | HTTP (OpenAI 兼容) | 智能路由请求到最佳 LLM |

**通信方式**：
- Gateway 通过 HTTP POST 调用 Router 的 `/v1/chat/completions` 端点
- 请求格式兼容 OpenAI Chat Completions API
- Router 返回标准的 OpenAI 响应格式

### 请求处理流程

1. **用户发送消息** → Slack/Discord 客户端
2. **消息平台转发** → OpenClaw Gateway（Socket 模式）
3. **Gateway 处理** → 调用 OpenClaw Router API
4. **Router 路由** → 根据策略选择最佳 LLM
5. **LLM 生成** → 调用上游 API 获取响应
6. **响应返回** → Gateway → 消息平台 → 用户

### 配置文件关系

1. **`openclaw_router/config.yaml`**：
   - 控制 Router 的行为
   - 定义后端 LLM 池
   - 配置路由策略
   - 存储 API 密钥

2. **`~/.openclaw/openclaw.json`**：
   - 配置 OpenClaw Gateway
   - 定义如何调用 Router（baseUrl, apiKey）
   - 配置 Slack/Discord 集成
   - 设置代理默认模型

## 6. 网络拓扑

```mermaid
graph LR
    A[用户<br/>Slack/Discord 客户端] -->|HTTPS/WSS| B[Slack/Discord Cloud]
    B -->|WebSocket<br/>Socket 模式| C[OpenClaw Gateway<br/>端口: 18789]
    C -->|HTTP POST<br/>OpenAI 兼容| D[OpenClaw Router<br/>端口: 8000]
    D -->|HTTPS API 调用| E[LLM 提供商<br/>Together/NVIDIA/OpenAI]

    style A fill:#e3f2fd,stroke:#1565c0
    style B fill:#fff9c4,stroke:#f9a825
    style C fill:#fff3e0,stroke:#ef6c00
    style D fill:#f3e5f5,stroke:#7b1fa2
    style E fill:#e8f5e9,stroke:#2e7d32
```

**网络要求**：
- **出站访问**：服务器需要访问 Slack/Discord 和 LLM API 提供商
- **入站访问**：无需公共入站端口（Socket 模式通过 WebSocket 连接）
- **内部通信**：Gateway 和 Router 通常运行在同一服务器上，使用 localhost 通信

## 7. 部署选项

### 开发环境
```
┌─────────────────────────────────────────────────┐
│  本地开发机                                     │
│  ┌─────────────────────────────────────────┐   │
│  │ OpenClaw Gateway (18789)              │   │
│  │ OpenClaw Router (8000)                │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
         │                    │
         ↓                    ↓
┌─────────────────┐  ┌─────────────────┐
│ Slack/Discord   │  │ LLM API 提供商  │
└─────────────────┘  └─────────────────┘
```

### 生产环境（单服务器）
```
┌─────────────────────────────────────────────────┐
│  VPS / 云服务器                                 │
│  ┌─────────────────────────────────────────┐   │
│  │ OpenClaw Gateway (系统服务)           │   │
│  │ OpenClaw Router (系统服务)            │   │
│  │ 健康检查监控                           │   │
│  │ 日志轮转                               │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
         │                    │
         ↓                    ↓
┌─────────────────┐  ┌─────────────────┐
│ Slack/Discord   │  │ LLM API 提供商  │
└─────────────────┘  └─────────────────┘
```

### 生产环境（分布式）
```
┌──────────────────┐  ┌──────────────────┐
│ Gateway 服务器   │  │ Router 服务器    │
│ OpenClaw GW      │  │ OpenClaw Router  │
│ 端口: 18789      │  │ 端口: 8000       │
└──────────────────┘  └──────────────────┘
         │                    │
         └────────┬───────────┘
                  ↓
    ┌────────────────────────┐
    │   负载均衡 / API 网关  │
    └────────────────────────┘
                  │
                  ↓
    ┌────────────────────────┐
    │   LLM API 提供商       │
    └────────────────────────┘
```

## 8. 安全架构

```mermaid
graph TB
    subgraph SecurityLayers["安全层"]
        L1["消息平台认证<br/>Slack/Discord OAuth"]
        L2["Gateway 模式<br/>local 模式限制"]
        L3["API 密钥隔离<br/>上游密钥在服务器"]
        L4["配对批准<br/>手动 approve"]
    end

    subgraph DataProtection["数据保护"]
        D1["API 密钥<br/>环境变量"]
        D2["配置文件<br/>用户目录权限"]
        D3["日志文件<br/>受限访问"]
    end

    subgraph NetworkSecurity["网络安全"]
        N1["Socket 模式<br/>无需公共端口"]
        N2["出站连接<br/>API 白名单"]
        N3["本地通信<br/>localhost"]
    end

    L1 --> L2 --> L3 --> L4
    D1 --> D2 --> D3
    N1 --> N2 --> N3

    style SecurityLayers fill:#ffebee,stroke:#c62828
    style DataProtection fill:#e8eaf6,stroke:#283593
    style NetworkSecurity fill:#e0f2f1,stroke:#00695c
```

**安全特性**：
1. **API 密钥隔离**：上游 LLM API 密钥存储在服务器（Router），不暴露给客户端
2. **Socket 模式**：无需公共入站 Webhook URL，降低攻击面
3. **配对批准**：首次访问需要手动 approve
4. **环境变量**：敏感信息通过环境变量传递

## 总结

OpenClaw 集成架构提供了完整的消息平台到 LLM 的解决方案：

- **用户友好**：Slack/Discord 原生体验，无需自定义 UI
- **灵活路由**：支持多种路由策略和 ML 路由器
- **部署简单**：单脚本启动，支持 systemd 服务
- **安全可靠**：API 密钥隔离，Socket 模式，配对批准
- **易于扩展**：支持自定义路由器、本地模型、多提供商
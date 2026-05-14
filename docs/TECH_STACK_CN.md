# LLMRouter 核心技术栈梳理

本文档详细梳理了 LLMRouter 项目的核心技术栈、第三方依赖库、API 服务提供商配置、本地 LLM 模型支持及其依赖关系图。

---

## 目录

- [1. 核心技术栈](#1-核心技术栈)
- [2. 第三方依赖库及版本要求](#2-第三方依赖库及版本要求)
- [3. API 服务提供商配置](#3-api-服务提供商配置)
- [4. 本地 LLM 模型支持](#4-本地-llm-模型支持)
- [5. 依赖关系图](#5-依赖关系图)
- [6. 模块架构](#6-模块架构)

---

## 1. 核心技术栈

### 1.1 编程语言

| 技术 | 版本要求 | 说明 |
|-----|---------|------|
| Python | >= 3.10 | 项目主要编程语言，支持 3.10 和 3.11 |

### 1.2 深度学习框架

| 技术 | 版本要求 | 说明 |
|-----|---------|------|
| PyTorch | >= 2.0 | 核心深度学习框架，用于路由模型训练和推理 |
| vLLM | 0.6.3（可选） | 高性能 LLM 推理引擎，用于 RouterR1 |

### 1.3 Web 服务框架

| 技术 | 版本要求 | 说明 |
|-----|---------|------|
| FastAPI | 最新 | 构建 OpenAI 兼容 API 服务 |
| Uvicorn | 最新 | ASGI 服务器，用于运行 FastAPI |
| WebSockets | 最新 | 支持实时流式通信 |
| Gradio | >= 4.0 | 交互式聊天界面 |

### 1.4 数据处理与机器学习

| 技术 | 版本要求 | 说明 |
|-----|---------|------|
| NumPy | >= 1.21 | 数值计算 |
| Pandas | >= 1.5 | 数据处理与分析 |
| Scikit-learn | >= 1.2 | 机器学习算法（KNN、SVM、MLP 等） |
| SciPy | >= 1.10 | 科学计算 |
| Datasets | >= 2.14 | 数据集处理（Hugging Face） |

### 1.5 NLP 与模型相关

| 技术 | 版本要求 | 说明 |
|-----|---------|------|
| Transformers | >= 4.40 | Hugging Face Transformers 库 |
| SentencePiece | >= 0.1.99 | 分词器 |
| PEFT | >= 0.7 | 参数高效微调库 |
| Torch-Geometric | >= 2.3 | 图神经网络库（GraphRouter、GMTRouter） |
| Protobuf | >= 3.20 | Protocol Buffers |

### 1.6 配置与工具

| 技术 | 版本要求 | 说明 |
|-----|---------|------|
| PyYAML | >= 6.0 | YAML 配置文件解析 |
| Pydantic | >= 2.0 | 数据验证和解析 |
| tqdm | >= 4.65 | 进度条显示 |
| LiteLLM | >= 1.0 | 多提供商 LLM API 统一调用 |

### 1.7 网络请求

| 技术 | 版本要求 | 说明 |
|-----|---------|------|
| httpx | 最新 | 异步 HTTP 客户端 |

---

## 2. 第三方依赖库及版本要求

### 2.1 核心依赖（必装）

```toml
[project]
name = "llmrouter-lib"
version = "0.3.1"
requires-python = ">=3.10"

dependencies = [
  "torch>=2.0",
  "transformers>=4.40",
  "sentencepiece>=0.1.99",
  "numpy>=1.21",
  "pandas>=1.5",
  "scikit-learn>=1.2",
  "pyyaml>=6.0",
  "tqdm>=4.65",
  "datasets>=2.14",
  "pydantic>=2.0",
  "gradio>=4.0",
  "litellm>=1.0",
  "peft>=0.7",
  "torch-geometric>=2.3",
  "scipy>=1.10",
  "protobuf>=3.20",
  "fastapi",
  "uvicorn",
  "websockets",
  "httpx",
]
```

### 2.2 可选依赖

#### RouterR1 依赖（GPU 专用）

```toml
[project.optional-dependencies]
router-r1 = ["vllm==0.6.3", "torch==2.4.0", "openai>=1.0"]
```

#### 完整依赖

```toml
all = ["vllm==0.6.3", "torch==2.4.0", "openai>=1.0"]
```

### 2.3 安装方式

```bash
# 基础安装
pip install -e .

# 安装 RouterR1 支持（需要 GPU）
pip install -e ".[router-r1]"

# 安装所有可选依赖
pip install -e ".[all]"
```

---

## 3. API 服务提供商配置

### 3.1 支持的 API 提供商

| 提供商 | Base URL | 认证方式 | 状态 |
|--------|----------|---------|------|
| NVIDIA | https://integrate.api.nvidia.com/v1 | Bearer Token | ✅ 已支持 |
| OpenAI | https://api.openai.com/v1 | Bearer Token | ✅ 已支持 |
| Anthropic | https://api.anthropic.com/v1 | Bearer Token | ✅ 已支持 |
| Together AI | https://api.together.xyz/v1 | Bearer Token | ✅ 已支持 |
| Hugging Face | https://router.huggingface.co/v1 | Bearer Token | ✅ 已支持 |

### 3.2 API 密钥配置

#### 服务特定字典格式（推荐）

```bash
export API_KEYS='{
  "NVIDIA": "nvidia-key-1,nvidia-key-2",
  "OpenAI": ["openai-key-1", "openai-key-2"],
  "Anthropic": "anthropic-key-1",
  "Together": "together-key"
}'
```

#### 环境变量方式

```bash
export NVIDIA_API_KEY="your-nvidia-key"
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export TOGETHER_API_KEY="your-together-key"
```

### 3.3 API 端点配置

API 端点按优先级解析：

1. **模型级别**（最高优先级）：在 LLM 候选 JSON 中指定 `api_endpoint`
2. **路由器级别**（后备）：在路由器 YAML 配置中指定 `api_endpoint`
3. **错误**：均未指定时抛出描述性错误

#### LLM 候选 JSON 示例

```json
{
  "qwen2.5-7b-instruct": {
    "model": "qwen/qwen2.5-7b-instruct",
    "service": "NVIDIA",
    "api_endpoint": "https://integrate.api.nvidia.com/v1",
    "input_price": 0.2,
    "output_price": 0.2
  },
  "gpt-4": {
    "model": "gpt-4",
    "service": "OpenAI",
    "api_endpoint": "https://api.openai.com/v1",
    "input_price": 5.0,
    "output_price": 15.0
  }
}
```

### 3.4 免费资源

| 提供商 | 免费额度 | 说明 |
|--------|---------|------|
| NVIDIA | 免费可用 | 访问 [build.nvidia.com](https://build.nvidia.com/) 获取 |

---

## 4. 本地 LLM 模型支持

### 4.1 支持的本地推理框架

| 框架 | 协议 | 端口示例 | 认证要求 |
|------|------|---------|---------|
| Ollama | OpenAI 兼容 | http://localhost:11434/v1 | 无（本地） |
| vLLM | OpenAI 兼容 | http://localhost:8001/v1 | 无（本地） |
| SGLang | OpenAI 兼容 | http://localhost:30000/v1 | 无（本地） |
| llama.cpp | OpenAI 兼容 | http://localhost:8080/v1 | 无（本地） |
| LM Studio | OpenAI 兼容 | http://localhost:1234/v1 | 无（本地） |
| Hugging Face CLI | OpenAI 兼容 | http://localhost:8082/v1 | 无（本地） |

### 4.2 本地模型配置示例

#### Ollama

```yaml
llms:
  gemma3:
    provider: ollama
    provider_type: openai_compatible
    model: gemma3
    base_url: http://localhost:11434/v1
    auth_mode: none
    chat_path: /chat/completions
    description: "Local Ollama backend"
```

#### vLLM

```yaml
llms:
  vllm_llama:
    provider: vllm
    provider_type: openai_compatible
    model: meta-llama/Llama-3.1-8B-Instruct
    base_url: http://localhost:8001/v1
    auth_mode: none
    chat_path: /chat/completions
    description: "Local vLLM backend"
```

#### SGLang

```yaml
llms:
  sglang_qwen:
    provider: sglang
    provider_type: openai_compatible
    model: Qwen/Qwen2.5-7B-Instruct
    base_url: http://localhost:30000/v1
    auth_mode: none
    chat_path: /chat/completions
    description: "Local SGLang backend"
```

### 4.3 本地模型 API 密钥配置

对于本地提供商，使用空字符串作为 API 密钥：

```bash
export API_KEYS='{"Ollama": "", "vllm": "", "sglang": ""}'
```

### 4.4 重要说明

1. **端点格式**：必须使用 `/v1` 端点（OpenAI 兼容），而非原生 API 端点
2. **自动检测**：系统自动检测本地主机端点（`localhost` 或 `127.0.0.1`）
3. **认证模式**：本地提供商可设置 `auth_mode: none`

---

## 5. 依赖关系图

### 5.1 核心模块依赖关系

```
┌─────────────────────────────────────────────────────────────────┐
│                        LLMRouter 核心                          │
└─────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│   路由器模型   │           │  数据处理模块  │           │  评估模块     │
│   (models/)   │           │  (data/)      │           │(evaluation/)  │
└───────────────┘           └───────────────┘           └───────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│• KNN Router   │           │• 数据生成    │           │• 批量评估    │
│• SVM Router   │           │• 嵌入提取    │           │• 指标计算    │
│• MLP Router   │           │• API 调用    │           │• Arena 评估  │
│• GraphRouter  │           │• 数据转换    │           │• 对话评估    │
│• GMTRouter    │           │• 提示工程    │           └───────────────┘
│• RouterR1     │           └───────────────┘
•• AutoMix      │
••• 等等        │
└───────────────┘
        │
        ▼
┌───────────────┐
│  工具模块     │
│  (utils/)     │
└───────────────┘
        │
        ▼
┌───────────────┐
│• API 调用     │
•• 嵌入生成    │
•• 配置管理    │
•• 助手函数    │
└───────────────┘
```

### 5.2 服务层依赖关系

```
┌─────────────────────────────────────────────────────────────────┐
│                         服务层                                  │
└─────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│  FastAPI 服务  │           │ OpenClaw Router│         │   Gradio UI   │
│  (serve/)     │           │(openclaw/)   │           │   (chat/)     │
└───────────────┘           └───────────────┘           └───────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│• OpenAI API   │           │• 路由策略    │           │• 交互式聊天  │
│• WebSocket    │           │• 记忆系统    │           │• 实时显示    │
│• 流式响应     │           │• 多模态支持  │           │• 历史记录    │
└───────────────┘           └───────────────┘           └───────────────┘
```

### 5.3 外部依赖关系

```
┌─────────────────────────────────────────────────────────────────┐
│                       外部服务依赖                              │
└─────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│   云端 API     │           │  本地推理     │           │  Hugging Face│
│   服务商      │           │  服务框架     │           │    生态       │
└───────────────┘           └───────────────┘           └───────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│• NVIDIA API   │           │• Ollama       │           │• Transformers │
│• OpenAI API   │           │• vLLM         │           │• Datasets     │
│• Anthropic API│          │• SGLang       │           │• PEFT         │
│• Together AI  │           │• llama.cpp    │           └───────────────┘
│• HF Endpoints │           │• LM Studio    │
└───────────────┘           └───────────────┘
```

### 5.4 技术栈层次图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         应用层 (Application Layer)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  CLI 工具   │  │ Gradio UI   │  │  ComfyUI    │  │ OpenClaw    │ │
│  │  (llmrouter)│  │             │  │  可视化界面  │  │  集成       │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                       服务层 (Service Layer)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ FastAPI 服务│  │路由策略引擎 │  │ 记忆系统    │  │ 多模态处理  │ │
│  │ (OpenAI兼容)│  │(16+ 策略)   │  │(检索增强)   │  │ (图片/视频) │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                      核心层 (Core Layer)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  路由器     │  │ 数据生成    │  │  评估引擎   │  │  插件系统    │ │
│  │  (16+ 模型) │  │  管道       │  │ (11 数据集)  │  │ (自定义扩展) │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                      工具层 (Utility Layer)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ API 调用    │  │ 嵌入生成    │  │ 配置管理    │  │ 提示工程    │ │
│  │(LiteLLM)    │  │(Longformer) │  │ (YAML/JSON) │  │  模板系统   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                     框架层 (Framework Layer)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   PyTorch   │  │ Transformers│  │FastAPI/Uvicorn│ │ Scikit-learn│ │
│  │ (深度学习)   │  │  (NLP 模型)  │  │ (Web 服务)  │  │ (ML 算法)   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                    外部服务层 (External Layer)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ 云端 API     │  │ 本地推理    │  │ Hugging Face│  │  数据集      │ │
│  │ 服务商       │  │ 服务框架    │  │  模型中心   │  │ (Benchmark)  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. 模块架构

### 6.1 目录结构

```
LLMRouter/
├── llmrouter/              # 核心库代码
│   ├── models/             # 路由器模型实现
│   │   ├── knnrouter/      # KNN 路由器
│   │   ├── svmrouter/      # SVM 路由器
│   │   ├── mlprouter/      # MLP 路由器
│   │   ├── mfrouter/       # 矩阵分解路由器
│   │   ├── elorouter/      # Elo 评级路由器
│   │   ├── routerdc/       # 双对比学习路由器
│   │   ├── automix/        # AutoMix 路由器
│   │   ├── hybrid_llm/     # 混合 LLM 路由器
│   │   ├── graphrouter/    # 图路由器
│   │   ├── causallm_router/ # 因果 LM 路由器
│   │   ├── gmtrouter/      # 图神经个性化路由器
│   │   ├── personalizedrouter/ # GNN 个性化路由器
│   │   ├── knnmultiroundrouter/ # KNN 多轮路由器
│   │   ├── llmmultiroundrouter/ # LLM 多轮路由器
│   │   ├── router_r1/      # RouterR1（预训练）
│   │   ├── smallest_llm/   # 总是路由到最小模型
│   │   ├── largest_llm/    # 总是路由到最大模型
│   │   ├── meta_router.py  # 元路由器基类
│   │   └── base_trainer.py # 训练器基类
│   │
│   ├── data/               # 数据处理模块
│   │   ├── data_generation.py    # 数据生成
│   │   ├── generate_llm_embeddings.py # LLM 嵌入生成
│   │   ├── api_calling_evaluation.py # API 调用与评估
│   │   ├── embeddings.py          # 嵌入生成工具
│   │   ├── evaluation.py          # 评估指标
│   │   ├── api_calling.py         # API 调用工具
│   │   ├── data_processing.py     # 数据处理
│   │   ├── data_convert.py        # 数据转换
│   │   ├── conversation.py        # 对话处理
│   │   ├── prompting.py           # 提示工程
│   │   └── model_loader.py        # 模型加载
│   │
│   ├── evaluation/         # 评估模块
│   │   ├── batch_evaluator.py  # 批量评估
│   │   └── example.py          # 评估示例
│   │
│   ├── serve/              # API 服务模块
│   │   ├── config.py           # 服务配置
│   │   ├── server.py           # FastAPI 服务器
│   │   └── __init__.py
│   │
│   ├── utils/              # 工具模块
│   │   ├── setup.py            # 环境设置
│   │   └── ...                 # 其他工具
│   │
│   └── cli/                # 命令行工具
│       ├── router_main.py      # 主入口
│       ├── router_train.py     # 训练命令
│       ├── router_inference.py # 推理命令
│       └── router_chat.py      # 聊天命令
│
├── openclaw_router/       # OpenClaw 集成
│   ├── config.py           # OpenClaw 配置
│   ├── server.py           # OpenClaw 服务器
│   ├── routers.py          # 路由策略
│   ├── memory.py           # 记忆系统
│   ├── media.py            # 多模态处理
│   └── __main__.py
│
├── custom_routers/        # 自定义路由器
│   ├── randomrouter/       # 随机路由器
│   ├── thresholdrouter/    # 阈值路由器
│   └── ...                 # 其他自定义路由器
│
├── custom_tasks/          # 自定义任务
│   └── ...                 # 自定义任务定义
│
├── configs/               # 配置文件
│   ├── model_config_train/    # 训练配置
│   ├── model_config_test/     # 测试配置
│   └── openclaw_example.yaml  # OpenClaw 示例配置
│
├── data/                  # 数据目录
│   ├── example_data/          # 示例数据
│   ├── multimodal_tasks/      # 多模态任务
│   └── ...
│
├── scripts/               # 脚本目录
│   └── ...
│
├── ComfyUI/               # ComfyUI 可视化界面
│   └── ...
│
├── tests/                 # 测试目录
│   └── ...
│
├── docs/                  # 文档目录
│   └── architecture/          # 架构文档
│
├── pyproject.toml         # 项目配置
└── README.md              # 项目说明
```

### 6.2 路由器分类

#### 单轮路由器 (Single-Round Routers)
- `knnrouter` - K 近邻路由器
- `svmrouter` - 支持向量机路由器
- `mlprouter` - 多层感知机路由器
- `mfrouter` - 矩阵分解路由器
- `elorouter` - Elo 评级路由器
- `routerdc` - 双对比学习路由器
- `automix` - 自动模型混合
- `hybrid_llm` - 混合 LLM 路由策略
- `graphrouter` - 图路由器
- `causallm_router` - 因果语言模型路由器
- `smallest_llm` - 总是路由到最小模型
- `largest_llm` - 总是路由到最大模型

#### 多轮路由器 (Multi-Round Routers)
- `router_r1` - 预训练 Router-R1 模型

#### 个性化路由器 (Personalized Routers)
- `gmtrouter` - 基于图的个性化路由器
- `personalizedrouter` - GNN 个性化路由器

#### 代理路由器 (Agentic Routers)
- `knnmultiroundrouter` - KNN 多轮路由器
- `llmmultiroundrouter` - LLM 多轮路由器

### 6.3 数据集支持

支持 11 个基准数据集：

| 类别 | 数据集 | 任务类型 |
|------|--------|---------|
| 问答 | NaturalQA | 开放域问答 |
| 问答 | TriviaQA | 知识问答 |
| 推理 | MMLU | 多任务语言理解 |
| 推理 | GPQA | 研究级问答 |
| 问答 | GSM8K | 数学推理 |
| 问答 | Math | 数学问题 |
| 推理 | CommonsenseQA | 常识推理 |
| 推理 | OpenbookQA | 开放书问答 |
| 推理 | ARC-Challenge | 抽象推理 |
| 编程 | MBPP | Python 编程 |
| 编程 | HumanEval | 函数补全 |

### 6.4 多模态支持

支持 5 个多模态任务，涵盖 3 个数据集：

| 数据集 | 任务类型 | 模态 |
|--------|---------|------|
| Geometry3K | 几何问题 | 图片 + 文本 |
| MathVista | 数学视觉 | 图片 + 文本 |
| Charades-Ego | 视频理解 | 视频 + 文本 |

---

## 7. 附录

### 7.1 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `API_KEYS` | API 密钥配置（推荐字典格式） | `{"NVIDIA": "key", "OpenAI": "key"}` |
| `NVIDIA_API_KEY` | NVIDIA API 密钥 | `nvapi-xxx` |
| `OPENAI_API_KEY` | OpenAI API 密钥 | `sk-xxx` |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | `sk-ant-xxx` |
| `TOGETHER_API_KEY` | Together AI API 密钥 | `xxx` |
| `HF_TOKEN` | Hugging Face Token | `hf_xxx` |
| `CUDA_VISIBLE_DEVICES` | 可见 GPU 设备 | `0,1,2` |
| `KMP_DUPLICATE_LIB_OK` | OpenMP 兼容性 | `True` |

### 7.2 配置文件示例

#### 训练配置示例

```yaml
# configs/model_config_train/knnrouter.yaml

data_path:
  query_data_train: 'data/example_data/query_data/default_query_train.jsonl'
  query_data_test: 'data/example_data/query_data/default_query_test.jsonl'
  query_embedding_data: 'data/example_data/embeddings/query_embeddings_longformer.pt'
  routing_data_train: 'data/example_data/routing_data/default_routing_train_data.jsonl'
  routing_data_test: 'data/example_data/routing_data/default_routing_test_data.jsonl'
  llm_data: 'data/example_data/llm_candidates/default_llm.json'
  llm_embedding_data: 'data/example_data/llm_candidates/default_llm_embeddings.json'

model_path:
  ini_model_path: ''
  save_model_path: 'saved_models/knnrouter/knnrouter_model.pkl'

metric:
  weights:
    performance: 1
    cost: 0
    llm_judge: 0

hparam:
  n_neighbors: 5
  weights: "uniform"
  algorithm: "auto"
  leaf_size: 30
  p: 2
  metric: "minkowski"
  n_jobs: -1

api_endpoint: 'https://integrate.api.nvidia.com/v1'  # 默认 API 端点
```

#### OpenClaw 配置示例

```yaml
# configs/openclaw_example.yaml

serve:
  host: "0.0.0.0"
  port: 8000
  show_model_prefix: true

router:
  strategy: llm
  provider: nvidia
  model: meta/llama-3.1-8b-instruct
  base_url: https://integrate.api.nvidia.com/v1
  provider_type: openai_compatible
  auth_mode: auto
  chat_path: /chat/completions

api_keys:
  nvidia:
    - nvapi-xxx...
  openai: ${OPENAI_API_KEY}
  anthropic: ${ANTHROPIC_API_KEY}

llms:
  llama-3.1-8b:
    provider: nvidia
    model: meta/llama-3.1-8b-instruct
    base_url: https://integrate.api.nvidia.com/v1
    description: "Fast responses"
    max_tokens: 1024
    context_limit: 128000
    input_price: 0.2
    output_price: 0.2

  llama3-70b:
    provider: nvidia
    model: meta/llama3-70b-instruct
    base_url: https://integrate.api.nvidia.com/v1
    description: "Complex reasoning"
    max_tokens: 1024
    context_limit: 8192
    input_price: 0.9
    output_price: 0.9
```

### 7.3 常用命令

```bash
# 训练路由器
llmrouter train --router knnrouter --config configs/model_config_train/knnrouter.yaml

# 推理
llmrouter infer --router knnrouter --config configs/model_config_test/knnrouter.yaml --query "Hello"

# 聊天界面
llmrouter chat --router knnrouter --config configs/model_config_test/knnrouter.yaml

# 启动 OpenClaw Router 服务
llmrouter serve --config configs/openclaw_example.yaml

# 列出所有路由器
llmrouter list-routers
```

---

**文档版本**: 1.0.0
**最后更新**: 2026-05-15
**维护者**: LLMRouter 开发团队
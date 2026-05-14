# LLMRouter 技术文档总览

## 1. 项目概述

LLMRouter 是一个开源的智能路由系统，通过动态选择最合适的大语言模型（LLM）来优化推理过程。该项目提供了 16+ 种路由算法，支持从简单的基于规则的路由到复杂的机器学习和图神经网络路由。

### 1.1 核心功能

- **智能路由**：根据任务复杂度、成本和性能要求自动路由查询到最优 LLM
- **多种路由模型**：支持 16+ 种路由模型，涵盖四大类别
  - 单轮路由器（Single-Round Routers）
  - 多轮路由器（Multi-Round Routers）
  - 个性化路由器（Personalized Routers）
  - 代理路由器（Agentic Routers）
- **统一 CLI 工具**：提供完整的命令行接口支持训练、推理和交互式聊天
- **完整流水线**：包含数据生成、训练、推理和评估的完整流程
- **插件系统**：支持自定义路由器和任务，无需修改核心代码
- **可视化界面**：集成 ComfyUI 可视化界面
- **OpenAI 兼容 API**：支持 OpenClaw Router 部署

### 1.2 支持的路由算法

#### 单轮路由器
- KNN Router：基于 K-近邻的路由算法
- SVM Router：基于支持向量机的路由算法
- MLP Router：基于多层感知机的路由算法
- MF Router：基于矩阵分解的路由算法
- ELO Router：基于 ELO 评分的路由算法
- RouterDC：基于双对比学习的路由算法
- AutoMix：自动模型混合路由
- Hybrid LLM：混合 LLM 路由策略
- Graph Router：基于图神经网络的路由算法
- CausalLM Router：基于因果语言模型的路由器
- Smallest LLM：始终路由到最小模型
- Largest LLM：始终路由到最大模型

#### 多轮路由器
- Router-R1：预训练的多轮对话路由模型

#### 个性化路由器
- GMT Router：基于图神经网络的个性化路由器，支持用户偏好学习
- Personalized Router：基于 GNN 的个性化路由器，支持用户特征

#### 代理路由器
- KNN Multi-Round Router：基于 KNN 的代理路由器，用于复杂任务
- LLM Multi-Round Router：基于 LLM 的代理路由器，用于复杂任务

---

## 2. 整体架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           LLMRouter 系统架构                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐           │
│  │   用户接口   │      │  API 服务器  │      │  可视化界面  │           │
│  ├──────────────┤      ├──────────────┤      ├──────────────┤           │
│  │  - CLI 工具  │      │  OpenAI 兼容 │      │   ComfyUI    │           │
│  │  - 聊天界面  │      │  OpenClaw   │      │  可视化工作流 │           │
│  │  - 推理接口  │      │  FastAPI    │      │              │           │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘           │
│         │                     │                     │                    │
│         └─────────────────────┼─────────────────────┘                    │
│                               │                                          │
└───────────────────────────────┼──────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          核心路由层                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      MetaRouter (基类)                           │   │
│  │  - route_single()                                               │   │
│  │  - route_batch()                                                │   │
│  │  - compute_metrics()                                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                │                                        │
│        ┌───────────┬───────────┼───────────┬───────────┐                │
│        ▼           ▼           ▼           ▼           ▼                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ 单轮路由 │ │ 多轮路由 │ │个性化路由│ │ 代理路由 │ │ 基准路由 │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│        │           │           │           │           │                │
│        ▼           ▼           ▼           ▼           ▼                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ KNN/SVM/ │ │ Router-  │ │  GMT/    │ │ KNN-MR/  │ │ Smallest │      │
│  │ MLP/MF/  │ │ R1       │ │ Personal │ │ LLM-MR   │ │ Largest  │      │
│  │ Graph... │ │          │ │          │ │          │ │          │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          数据处理层                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │  数据加载器  │  │  嵌入生成器  │  │  评估系统    │                   │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤                   │
│  │ - 查询数据   │  │ - Longformer │  │ - 指标注册   │                   │
│  │ - LLM 元数据 │  │ - 文本嵌入   │  │ - 批量评估   │                   │
│  │ - 路由数据   │  │ - LLM 嵌入   │  │ - 多任务评估 │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          外部服务层                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ NVIDIA   │  │ OpenAI   │  │ Together │  │ Anthropic│                 │
│  │ API      │  │ API      │  │ AI       │  │ API      │                 │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                 │
│                                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ vLLM     │  │ SGLang   │  │ Ollama   │  │ 本地服务 │                 │
│  │ 本地部署 │  │ 本地部署 │  │ 本地部署 │  │          │                 │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                 │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心模块关系图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         核心模块依赖关系                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  llmrouter/                                                               │
│  ├── __init__.py                                                         │
│  │                                                                       │
│  ├── cli/                      # 命令行接口                              │
│  │   ├── router_main.py       # 主入口，命令分发                         │
│  │   ├── router_train.py      # 训练命令                                 │
│  │   ├── router_inference.py  # 推理命令                                 │
│  │   └── router_chat.py       # 聊天界面                                 │
│  │                                                                       │
│  ├── models/                   # 路由器模型                              │
│  │   ├── meta_router.py       # 路由器基类                               │
│  │   ├── base_trainer.py      # 训练器基类                               │
│  │   ├── knnrouter/           # KNN 路由器                               │
│  │   ├── svmrouter/           # SVM 路由器                               │
│  │   ├── mlprouter/           # MLP 路由器                               │
│  │   ├── mfrouter/            # 矩阵分解路由器                           │
│  │   ├── elorouter/           # ELO 评分路由器                           │
│  │   ├── routerdc/            # 双对比学习路由器                         │
│  │   ├── automix/             # 自动混合路由器                           │
│  │   ├── hybrid_llm/          # 混合 LLM 路由器                          │
│  │   ├── graphrouter/         # 图路由器                                 │
│  │   ├── causallm_router/     # 因果 LLM 路由器                          │
│  │   ├── smallest_llm/        # 最小模型路由器                           │
│  │   ├── largest_llm/         # 最大模型路由器                           │
│  │   ├── router_r1/           # 多轮路由器                               │
│  │   ├── knnmultiroundrouter/ # KNN 多轮路由器                          │
│  │   ├── llmmultiroundrouter/ # LLM 多轮路由器                          │
│  │   ├── gmtrouter/           # GMT 个性化路由器                        │
│  │   └── personalizedrouter/  # 个性化路由器                            │
│  │                                                                       │
│  ├── data/                     # 数据处理                                │
│  │   ├── data_generation.py   # 数据生成                                │
│  │   ├── generate_llm_embeddings.py  # LLM 嵌入生成                     │
│  │   ├── api_calling_evaluation.py   # API 调用与评估                   │
│  │   ├── data_loader.py       # 数据加载器                               │
│  │   └── multimodal_generation.py    # 多模态数据生成                    │
│  │                                                                       │
│  ├── evaluation/               # 评估系统                                │
│  │   ├── __init__.py          # 评估指标注册                            │
│  │   └── 多种指标实现         # EM, F1, BERT Score, GSM8K 等             │
│  │                                                                       │
│  ├── serve/                    # API 服务器                              │
│  │   ├── server.py            # FastAPI 服务器                           │
│  │   └── config.py            # 服务器配置                               │
│  │                                                                       │
│  ├── prompts/                  # 提示词模板                              │
│  │   └── 多任务提示词         # 任务特定的提示词                         │
│  │                                                                       │
│  └── utils/                    # 工具函数                                │
│      ├── evaluation.py        # 评估工具函数                            │
│      ├── embedding.py         # 嵌入生成工具                            │
│      └── 其他工具...          │                                                                           │
│  plugin_system.py             # 插件系统                                │
│                                                                           │
│  openclaw_router/             # OpenClaw 路由器                          │
│  ├── server.py                # OpenAI 兼容服务器                       │
│  ├── config.py                # 配置管理                                 │
│  └── routers.py               # 路由策略实现                             │
│                                                                           │
│  custom_routers/              # 自定义路由器                             │
│  ├── randomrouter/            # 随机路由器示例                           │
│  └── thresholdrouter/         # 阈值路由器示例                           │
│                                                                           │
│  custom_tasks/                # 自定义任务                               │
│  └── 任务定义文件             │
│                                                                           │
│  ComfyUI/                     # ComfyUI 集成                            │
│  ├── nodes.py                 # 自定义节点                               │
│  └── workflows/               # 工作流示例                               │
│                                                                           │
│  configs/                     # 配置文件                                 │
│  ├── model_config_train/      # 训练配置                                 │
│  ├── model_config_test/       # 测试配置                                 │
│  └── openclaw_example.yaml    # OpenClaw 配置示例                       │
│                                                                           │
│  scripts/                     # 脚本                                     │
│  ├── start-openclaw.sh        # 启动 OpenClaw                            │
│  └── stop-openclaw.sh         # 停止 OpenClaw                            │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 核心路由器类型说明

### 3.1 单轮路由器（Single-Round Routers）

单轮路由器根据单个查询的嵌入和特征，一次性决定路由到哪个 LLM 模型。

#### 3.1.1 KNN Router（K-近邻路由器）

**原理**：基于 K-近邻算法的无参路由方法，通过查找历史数据中最相似的 K 个查询，使用多数投票选择最佳 LLM。

**特点**：
- 无需训练，只需存储历史查询和对应最佳模型
- 支持增量学习，可即时添加新示例
- 可解释性强，可检查哪些历史查询影响了决策

**适用场景**：
- 小到中等规模数据集（10-10000 个示例）
- 需要快速原型开发
- 数据分布频繁变化

**配置示例**：
```yaml
hparam:
  n_neighbors: 5           # K 值
  weights: "distance"      # 投票权重方式
  metric: "cosine"         # 距离度量
  algorithm: "auto"        # 搜索算法
```

**文件路径**：`llmrouter/models/knnrouter/`

#### 3.1.2 SVM Router（支持向量机路由器）

**原理**：基于支持向量机的分类路由，在高维嵌入空间中找到最优分类超平面。

**特点**：
- 支持核函数，可处理非线性关系
- 训练速度快，适合中等规模数据
- 泛化性能好

**适用场景**：
- 需要快速训练
- 中等规模数据集
- 对分类边界有清晰要求

**文件路径**：`llmrouter/models/svmrouter/`

#### 3.1.3 MLP Router（多层感知机路由器）

**原理**：基于深度神经网络的参数化路由器，学习查询嵌入到 LLM 选择的多层映射。

**特点**：
- 推理速度快（O(1) 复杂度）
- 可学习复杂的非线性关系
- 支持多种激活函数和正则化

**适用场景**：
- 大规模数据集（>10000 个示例）
- 需要快速推理
- 复杂路由模式

**配置示例**：
```yaml
hparam:
  hidden_dim: 256          # 隐藏层维度
  num_layers: 3            # 层数
  dropout: 0.1             # Dropout 比例
  learning_rate: 0.001     # 学习率
```

**文件路径**：`llmrouter/models/mlprouter/`

#### 3.1.4 MF Router（矩阵分解路由器）

**原理**：基于矩阵分解的协同过滤方法，学习查询和 LLM 的潜在表示。

**特点**：
- 捕捉查询和 LLM 之间的隐式关系
- 支持冷启动场景
- 内存效率高

**适用场景**：
- 需要捕捉查询-模型关联
- 稀疏数据场景
- 推荐系统类似应用

**文件路径**：`llmrouter/models/mfrouter/`

#### 3.1.5 ELO Router（ELO 评分路由器）

**原理**：基于 ELO 评分系统，动态调整各 LLM 的评分，选择当前评分最高的模型。

**特点**：
- 在线学习能力强
- 自适应性强
- 计算简单

**适用场景**：
- 需要持续更新模型评分
- 在线学习场景
- 竞争环境

**文件路径**：`llmrouter/models/elorouter/`

#### 3.1.6 RouterDC（双对比学习路由器）

**原理**：基于双对比学习的查询感知路由器，通过对比学习提升路由决策。

**特点**：
- 引入对比学习损失
- 提升查询表示质量
- 强泛化能力

**文件路径**：`llmrouter/models/routerdc/`

#### 3.1.7 AutoMix（自动混合路由器）

**原理**：自动混合多个 LLM 的输出，根据任务需求动态调整混合比例。

**特点**：
- 模型融合策略
- 自动权重调整
- 综合性能优化

**文件路径**：`llmrouter/models/automix/`

#### 3.1.8 Hybrid LLM（混合 LLM 路由器）

**原理**：结合多种路由策略的混合方法，根据任务特征选择合适的路由策略。

**特点**：
- 多策略融合
- 成本和质量平衡
- 灵活的路由决策

**文件路径**：`llmrouter/models/hybrid_llm/`

#### 3.1.9 Graph Router（图路由器）

**原理**：基于图神经网络的路由器，将查询、LLM 构建为图结构进行学习。

**特点**：
- 捕捉复杂关系
- 图神经网络建模
- 关系推理能力

**文件路径**：`llmrouter/models/graphrouter/`

#### 3.1.10 CausalLM Router（因果语言模型路由器）

**原理**：使用因果语言模型进行路由决策，基于文本生成能力选择模型。

**特点**：
- 基于生成式路由
- 上下文理解强
- 自然语言推理

**文件路径**：`llmrouter/models/causallm_router/`

#### 3.1.11 Smallest LLM / Largest LLM（基准路由器）

**原理**：始终路由到最小或最大的模型，作为性能基准。

**特点**：
- 无训练需求
- 成本极端优化（最小）或性能极端优化（最大）
- 基准对比

**文件路径**：`llmrouter/models/smallest_llm/`, `llmrouter/models/largest_llm/`

### 3.2 多轮路由器（Multi-Round Routers）

多轮路由器处理多轮对话场景，考虑对话上下文进行路由决策。

#### 3.2.1 Router-R1

**原理**：预训练的多轮路由模型，通过强化学习学习多轮路由和聚合策略。

**特点**：
- 预训练模型，无需大量数据
- 支持复杂的多轮对话
- 强化学习优化

**适用场景**：
- 多轮对话系统
- 需要预训练模型
- 复杂推理任务

**文件路径**：`llmrouter/models/router_r1/`

### 3.3 个性化路由器（Personalized Routers）

个性化路由器考虑用户特征和偏好，为不同用户提供个性化的路由决策。

#### 3.3.1 GMT Router（图多任务个性化路由器）

**原理**：基于图神经网络的多任务个性化路由器，构建包含用户、查询、任务、LLM 的异构图进行学习。

**特点**：
- 用户偏好建模
- 多任务学习
- 异构图神经网络

**适用场景**：
- 多用户场景
- 需要个性化推荐
- 多任务支持

**配置示例**：
```yaml
hparam:
  embedding_dim: 64          # GNN 隐藏维度
  user_num: 1000            # 用户数量
  num_task: 4               # 任务数量
  train_mask_rate: 0.3      # 训练时的边掩码率
```

**文件路径**：`llmrouter/models/gmtrouter/`

#### 3.3.2 Personalized Router（个性化路由器）

**原理**：基于 GNN 的个性化路由器，使用用户特征进行个性化建模。

**特点**：
- 用户特征集成
- 图结构建模
- 个性化消息传递

**适用场景**：
- 有用户特征数据
- 需要用户级个性化
- 图结构适用

**配置示例**：
```yaml
hparam:
  embedding_dim: 64
  user_num: 1000
  num_task: 4
  learning_rate: 0.001
```

**数据要求**：
- 使用 PersonaRoute-Bench 数据集
- 需要 user_id 字段
- 支持用户偏好权重

**文件路径**：`llmrouter/models/personalizedrouter/`

### 3.4 代理路由器（Agentic Routers）

代理路由器将复杂任务分解为多个子任务，为每个子任务选择最优模型。

#### 3.4.1 KNN Multi-Round Router

**原理**：结合 KNN 路由和查询分解的多轮代理路由器。

**流程**：
1. 使用基础 LLM 将查询分解为 1-4 个子查询
2. 对每个子查询使用 KNN 路由到最优模型
3. 使用路由模型执行子查询
4. 使用基础 LLM 聚合子查询结果

**特点**：
- 查询自动分解
- 子查询独立路由
- 结果聚合

**适用场景**：
- 复杂多面查询
- 需要多步推理
- 子任务差异化

**配置示例**：
```yaml
hparam:
  n_neighbors: 5
  weights: "distance"
  metric: "cosine"

base_model: "Qwen/Qwen2.5-3B-Instruct"
use_local_llm: false
```

**文件路径**：`llmrouter/models/knnmultiroundrouter/`

#### 3.4.2 LLM Multi-Round Router

**原理**：使用 LLM 进行路由决策的多轮代理路由器。

**流程**：
1. LLM 分析查询并决定子查询数量和内容
2. LLM 路由每个子查询到合适的模型
3. 执行子查询
4. LLM 聚合结果

**特点**：
- LLM 驱动的路由
- 灵活的分解策略
- 强推理能力

**适用场景**：
- 需要智能分解
- 复杂任务规划
- LLM 可用资源充足

**文件路径**：`llmrouter/models/llmmultiroundrouter/`

---

## 4. 安装和配置

### 4.1 环境要求

- Python >= 3.10
- PyTorch >= 2.0
- CUDA（可选，用于 GPU 加速）

### 4.2 安装方法

#### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/ulab-uiuc/LLMRouter.git
cd LLMRouter

# 创建虚拟环境
conda create -n llmrouter python=3.10
conda activate llmrouter

# 基础安装
pip install -e .

# 可选：安装 RouterR1 支持（需要 GPU）
pip install -e ".[router-r1]"

# 可选：安装所有可选依赖
pip install -e ".[all]"
```

#### 从 PyPI 安装

```bash
pip install llmrouter-lib
```

### 4.3 API 密钥配置

LLMRouter 需要配置 API 密钥来调用 LLM 服务。

#### 服务特定字典格式（推荐）

```bash
export API_KEYS='{"NVIDIA": "nvidia-key-1,nvidia-key-2", "OpenAI": ["openai-key-1"], "Anthropic": "anthropic-key-1"}'
```

**格式说明**：
- 键：服务提供商名称（必须与 LLM 候选 JSON 中的 `service` 字段匹配）
- 值：可以是逗号分隔字符串、JSON 数组或单个字符串
- 系统自动匹配 `service` 字段选择对应的 API 密钥
- 每个服务维护自己的轮询计数器进行负载均衡

#### LLM 候选 JSON 示例

```json
{
  "qwen2.5-7b-instruct": {
    "service": "NVIDIA",
    "model": "qwen/qwen2.5-7b-instruct",
    "api_endpoint": "https://integrate.api.nvidia.com/v1"
  },
  "gpt-4": {
    "service": "OpenAI",
    "model": "gpt-4",
    "api_endpoint": "https://api.openai.com/v1"
  }
}
```

#### 传统格式（向后兼容）

```bash
# JSON 数组格式
export API_KEYS='["key1", "key2", "key3"]'

# 逗号分隔格式
export API_KEYS='key1,key2,key3'

# 单个密钥
export API_KEYS='your-api-key'
```

### 4.4 API 端点配置

API 端点可按优先级配置：

1. **模型级**（最高优先级）：LLM 候选 JSON 中的 `api_endpoint` 字段
2. **路由器级**（回退）：路由器 YAML 配置中的 `api_endpoint` 字段

**LLM 候选 JSON 示例**：
```json
{
  "qwen2.5-7b-instruct": {
    "model": "qwen/qwen2.5-7b-instruct",
    "api_endpoint": "https://integrate.api.nvidia.com/v1"
  },
  "custom-model": {
    "model": "custom/model-name",
    "api_endpoint": "https://api.customprovider.com/v1"
  }
}
```

**路由器 YAML 示例**：
```yaml
api_endpoint: 'https://integrate.api.nvidia.com/v1'  # 所有模型的回退端点
```

### 4.5 本地 LLM 模型配置

LLMRouter 支持本地托管的 OpenAI 兼容 LLM 推理服务器（如 Ollama、vLLM、SGLang）。

对于本地提供商，可以使用空字符串 `""` 作为 API 密钥值。

```bash
export API_KEYS='{"Ollama": ""}'
```

```json
{
  "gemma3": {
    "size": "3B",
    "feature": "Gemma 3B model hosted locally via Ollama",
    "input_price": 0.0,
    "output_price": 0.0,
    "model": "gemma3",
    "service": "Ollama",
    "api_endpoint": "http://localhost:11434/v1"
  }
}
```

**注意**：使用 `/v1` 端点（OpenAI 兼容），而不是原生 API 端点。空字符串会自动检测本地主机端点（`localhost` 或 `127.0.0.1`）。

---

## 5. 快速开始指南

### 5.1 数据准备

LLMRouter 包含完整的数据生成流水线，支持 11 个基准数据集。

#### 流水线概览

1. **生成查询数据**：从基准数据集提取查询并创建训练/测试分割
2. **生成 LLM 嵌入**：从 LLM 元数据创建嵌入
3. **API 调用与评估**：调用 LLM API、评估响应并生成统一嵌入和路由数据

#### 快速开始

```bash
# 步骤 1：生成查询数据
python llmrouter/data/data_generation.py --config llmrouter/data/sample_config.yaml

# 步骤 2：生成 LLM 嵌入
python llmrouter/data/generate_llm_embeddings.py --config llmrouter/data/sample_config.yaml

# 步骤 3：API 调用与评估（需要 API_KEYS）
python llmrouter/data/api_calling_evaluation.py --config llmrouter/data/sample_config.yaml --workers 100
```

#### 输出文件

- **查询数据**（JSONL）：`query_data_train.jsonl` 和 `query_data_test.jsonl`
- **LLM 嵌入**（JSON）：`default_llm_embeddings.json`
- **查询嵌入**（PyTorch）：`query_embeddings_longformer.pt`
- **路由数据**（JSONL）：`default_routing_train_data.jsonl` 和 `default_routing_test_data.jsonl`

### 5.2 训练路由器

使用 `llmrouter train` 命令训练各种路由器模型。

#### 基本用法

```bash
# 训练 KNN 路由器
llmrouter train --router knnrouter --config configs/model_config_train/knnrouter.yaml

# 使用 GPU 训练 MLP 路由器
CUDA_VISIBLE_DEVICES=2 llmrouter train --router mlprouter --config configs/model_config_train/mlprouter.yaml --device cuda

# 安静模式训练 MF 路由器
CUDA_VISIBLE_DEVICES=1 llmrouter train --router mfrouter --config configs/model_config_train/mfrouter.yaml --device cuda --quiet
```

#### 训练个性化路由器

```bash
# 训练个性化路由器（需要 PersonaRoute-Bench 数据集）
CUDA_VISIBLE_DEVICES=0 llmrouter train --router personalizedrouter --config configs/model_config_train/personalizedrouter.yaml --device cuda
```

### 5.3 推理

使用 `llmrouter infer` 命令进行推理（需要 API 密钥）。

#### 单查询推理

```bash
llmrouter infer --router knnrouter --config config.yaml --query "What is machine learning?"
```

#### 批量推理

```bash
llmrouter infer --router knnrouter --config config.yaml --input queries.txt --output results.json
```

#### 仅路由（不调用 LLM API）

```bash
llmrouter infer --router knnrouter --config config.yaml --query "Hello" --route-only
```

#### 自定义生成参数

```bash
llmrouter infer --router knnrouter --config config.yaml --query "Explain AI" --temp 0.7 --max-tokens 2048 --verbose
```

**输入文件格式支持**：
- `.txt`：每行一个查询
- `.json`：字符串列表或包含 `"query"` 字段的对象列表
- `.jsonl`：每行一个 JSON 对象

### 5.4 交互式聊天

使用 `llmrouter chat` 命令启动交互式聊天界面（需要 API 密钥）。

#### 基本聊天

```bash
llmrouter chat --router knnrouter --config config.yaml
```

#### 自定义主机和端口

```bash
llmrouter chat --router knnrouter --config config.yaml --host 0.0.0.0 --port 7860
```

#### 公共共享链接

```bash
llmrouter chat --router knnrouter --config config.yaml --share
```

#### 查询模式

```bash
llmrouter chat --router knnrouter --config config.yaml --mode full_context --top_k 5
```

**查询模式说明**：
- `current_only`：仅基于当前查询路由（默认）
- `full_context`：结合所有聊天历史和当前查询
- `retrieval`：检索前 K 个相似历史查询作为上下文

### 5.5 直接脚本执行

也可以直接运行 CLI 脚本：

```bash
# 训练
python -m llmrouter.cli.router_train --router knnrouter --config config.yaml

# 推理
python -m llmrouter.cli.router_inference --router knnrouter --config config.yaml --query "Hello"

# 聊天
python -m llmrouter.cli.router_chat --router knnrouter --config config.yaml
```

### 5.6 列出可用路由器

```bash
llmrouter list-routers
```

### 5.7 使用 OpenClaw Router

OpenClaw Router 提供 OpenAI 兼容的 API 服务器。

#### 配置

编辑 `openclaw_router/config.yaml`：

```yaml
serve:
  host: "0.0.0.0"
  port: 8000
  show_model_prefix: true

router:
  strategy: llm  # 或：random, round_robin, rules, llmrouter
  provider: together
  base_url: https://api.together.xyz/v1
  model: "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"

api_keys:
  together: ${TOGETHER_API_KEY}

llms:
  llama-3.1-8b:
    provider: together
    model: "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    base_url: https://api.together.xyz/v1
    description: "Fast responses"

  llama-3.3-70b:
    provider: together
    model: "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    base_url: https://api.together.xyz/v1
    description: "Complex reasoning"
```

#### 启动服务器

```bash
# 使用启动脚本（推荐）
./scripts/start-openclaw.sh

# 使用 ML 路由器
./scripts/start-openclaw.sh -r knnrouter

# 自定义端口
./scripts/start-openclaw.sh -p 9000

# 或直接使用 CLI
llmrouter serve --config openclaw_router/config.yaml
```

#### 测试 API

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Explain quantum computing"}]
  }'
```

---

## 6. 插件系统

LLMRouter 提供插件系统，允许添加自定义路由器和任务。

### 6.1 自定义路由器

#### 创建自定义路由器

**1. 创建路由器目录**：
```bash
mkdir -p custom_routers/my_router
```

**2. 实现路由器**（`custom_routers/my_router/router.py`）：
```python
from llmrouter.models.meta_router import MetaRouter
import torch.nn as nn

class MyRouter(MetaRouter):
    """自定义路由器实现"""

    def __init__(self, yaml_path: str):
        model = nn.Identity()
        super().__init__(model=model, yaml_path=yaml_path)
        self.llm_names = list(self.llm_data.keys())

    def route_single(self, query_input: dict) -> dict:
        """路由单个查询到最佳 LLM"""
        query = query_input['query']

        # 自定义路由逻辑
        selected_llm = (self.llm_names[0] if len(query) < 50
                       else self.llm_names[-1])

        return {
            "query": query,
            "model_name": selected_llm,
            "predicted_llm": selected_llm,
        }

    def route_batch(self, batch: list) -> list:
        """路由多个查询"""
        return [self.route_single(q) for q in batch]
```

**3. 创建配置**（`custom_routers/my_router/config.yaml`）：
```yaml
data_path:
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

hparam:
  # 自定义超参数

api_endpoint: 'https://integrate.api.nvidia.com/v1'
```

**4. 使用自定义路由器**：
```bash
# 推理
llmrouter infer --router my_router \
  --config custom_routers/my_router/config.yaml \
  --query "What is machine learning?"

# 列出所有路由器（包括自定义的）
llmrouter list-routers
```

#### 插件发现位置

自定义路由器自动从以下位置发现：
- `./custom_routers/`（推荐 - 项目目录）
- `~/.llmrouter/plugins/`（用户主目录）
- `$LLMROUTER_PLUGINS` 环境变量（冒号分隔的路径）

### 6.2 自定义任务

**1. 创建任务格式化器**（`custom_tasks/my_tasks.py`）：
```python
from llmrouter.utils.prompting import register_prompt
from llmrouter.prompts import load_prompt_template

@register_prompt('my_task', default_metric='my_metric')
def format_my_task_prompt(sample_data):
    system_prompt = load_prompt_template("task_my_task")
    user_query = f"Question: {sample_data.get('query', '')}"
    return {"system": system_prompt, "user": user_query}
```

**2. 创建提示词模板**（`custom_tasks/task_prompts/task_my_task.yaml`）：
```yaml
template: |
  You are an expert at [task description]. [Instructions].
```

**3. 注册自定义指标**（可选）：
```python
from llmrouter.evaluation import evaluation_metric

@evaluation_metric('my_metric')
def my_metric(prediction: str, ground_truth: str, **kwargs) -> float:
    return 1.0 if prediction == ground_truth else 0.0
```

**4. 使用自定义任务**：
```python
import custom_tasks.my_tasks  # 导入触发注册

from llmrouter.utils import generate_task_query
from llmrouter.utils.evaluation import calculate_task_performance

# 生成提示词
prompt = generate_task_query('my_task', {'query': '...'})

# 评估（指标从任务自动推断）
score = calculate_task_performance(
    prediction="...",
    ground_truth="...",
    task_name="my_task"
)
```

---

## 7. ComfyUI 集成

LLMRouter 提供强大的可视化界面，通过 ComfyUI 构建数据生成和路由流水线。

### 7.1 安装与设置

**前提条件**：必须安装 [ComfyUI](https://github.com/Comfy-Org/ComfyUI)。

**1. 链接自定义节点**：
```bash
ln -s /path/to/LLMRouter/ComfyUI /path/to/ComfyUI/custom_nodes/LLMRouter
```

**2. 链接工作流示例**（可选）：
```bash
ln -s /path/to/LLMRouter/ComfyUI/workflows/llm_router_example.json /path/to/ComfyUI/user/default/workflows/llm_router_example.json
```

**3. 运行应用程序**：
```bash
python /path/to/ComfyUI/main.py
```

### 7.2 使用 ComfyUI 界面

#### 查找节点

1. 打开 ComfyUI Web 界面
2. 使用**节点库**侧边栏或**右键**点击画布
3. 导航到 **`LLMRouter`** 类别
4. 查找按功能组织的节点：
   - **数据**：`Select Datasets`、`Select LLMs`、`Generate Data`
   - **单轮**：`KNN Router`、`SVM Router`、`MLP Router` 等
   - **多轮/代理**：复杂任务的专用路由器

#### 加载示例

1. 点击 **`Workflows`** 选项卡
2. 选择 **`llm_router_example.json`**
3. 这将加载完整的流水线

### 7.3 关键特性

- **可视化配置**：在画布上直接调整参数（例如样本大小、模型候选）并选择数据集
- **端到端自动化**：无缝连接节点构建完整流水线：数据生成 → 路由器训练 → 评估
- **实时监控**：通过即时视觉反馈跟踪查询生成、嵌入提取和模型训练的状态
- **模块化设计**：通过拖放和连接数据集、LLM 和路由器的节点自定义构建流水线

---

## 8. 评估系统

LLMRouter 提供灵活的评估系统，支持多种评估指标。

### 8.1 内置指标

- `'em'` - 精确匹配
- `'em_mc'` - 多选题精确匹配
- `'cem'` - 包含精确匹配
- `'cemf1'` - 包含精确匹配（F1 回退）
- `'f1'` - F1 分数
- `'bert_score'` - BERT 语义相似度
- `'gsm8k'` - GSM8K 数学问题评估

### 8.2 使用评估系统

```python
from llmrouter.evaluation import evaluate_batch

# 准备数据
data = [
    {'prediction': 'hello world', 'ground_truth': 'hello', 'metric': 'f1'},
    {'prediction': 'exact match', 'ground_truth': 'exact match', 'metric': 'em'}
]

# 评估
results = evaluate_batch(data)

# 查看结果
for result in results:
    print(f"Score: {result['score']}")
```

### 8.3 注册自定义指标

```python
from llmrouter.evaluation import evaluation_metric

@evaluation_metric('my_custom_metric')
def my_eval_function(prediction: str, ground_truth: str, threshold: float = 0.5, **kwargs) -> float:
    """自定义评估逻辑"""
    return 1.0 if len(prediction) > threshold else 0.0
```

---

## 9. 项目结构

```
LLMRouter/
├── llmrouter/                 # 核心包
│   ├── __init__.py
│   ├── plugin_system.py       # 插件系统
│   ├── cli/                   # 命令行接口
│   │   ├── router_main.py
│   │   ├── router_train.py
│   │   ├── router_inference.py
│   │   └── router_chat.py
│   ├── models/                # 路由器模型
│   │   ├── meta_router.py
│   │   ├── base_trainer.py
│   │   ├── knnrouter/
│   │   ├── svmrouter/
│   │   ├── mlprouter/
│   │   └── ...
│   ├── data/                  # 数据处理
│   │   ├── data_generation.py
│   │   ├── generate_llm_embeddings.py
│   │   ├── api_calling_evaluation.py
│   │   └── data_loader.py
│   ├── evaluation/            # 评估系统
│   ├── serve/                 # API 服务器
│   │   ├── server.py
│   │   └── config.py
│   ├── prompts/               # 提示词模板
│   └── utils/                 # 工具函数
├── openclaw_router/           # OpenClaw 路由器
│   ├── server.py
│   ├── config.py
│   └── routers.py
├── custom_routers/            # 自定义路由器
│   ├── randomrouter/
│   └── thresholdrouter/
├── custom_tasks/              # 自定义任务
├── ComfyUI/                   # ComfyUI 集成
│   ├── nodes.py
│   └── workflows/
├── configs/                   # 配置文件
│   ├── model_config_train/
│   ├── model_config_test/
│   └── openclaw_example.yaml
├── scripts/                   # 脚本
│   ├── start-openclaw.sh
│   └── stop-openclaw.sh
├── data/                      # 数据目录
│   ├── example_data/
│   └── multimodal_tasks/
├── tests/                     # 测试
├── pyproject.toml             # 项目配置
└── README.md                  # 项目说明
```

---

## 10. 常见问题

### 10.1 数据相关

**Q: 如何使用自己的数据集？**

A: 创建自定义任务格式化器，使用 `@register_prompt` 装饰器注册您的任务。参考 `custom_tasks/README.md`。

**Q: 支持哪些数据集格式？**

A: 支持多种格式：
- `.jsonl`：每行一个 JSON 对象
- `.json`：JSON 数组
- `.txt`：每行一个查询

### 10.2 路由器选择

**Q: 如何选择合适的路由器？**

A: 根据场景选择：
- 小数据集 + 快速原型 → KNN Router
- 中等数据集 + 快速推理 → MLP Router
- 多用户场景 → Personalized Router
- 复杂多任务 → Agentic Router
- 基准对比 → Smallest/Largest LLM

**Q: 如何比较不同路由器的性能？**

A: 使用相同的数据集和配置训练多个路由器，然后在测试集上比较性能指标。

### 10.3 API 相关

**Q: 如何配置多个 API 提供商？**

A: 使用服务特定的字典格式：
```bash
export API_KEYS='{"NVIDIA": "key1,key2", "OpenAI": ["key1"], "Anthropic": "key1"}'
```

**Q: 如何使用本地模型？**

A: 配置本地提供商（如 Ollama、vLLM）：
```bash
export API_KEYS='{"Ollama": ""}'
```

在 LLM 候选 JSON 中指定 `api_endpoint` 为本地服务器地址。

### 10.4 部署相关

**Q: 如何部署到生产环境？**

A: 使用 OpenClaw Router：
1. 配置 `openclaw_router/config.yaml`
2. 使用 `llmrouter serve` 启动服务器
3. 通过 OpenAI 兼容 API 访问

**Q: 如何监控路由决策？**

A: 在配置中设置 `show_model_prefix: true`，响应中会包含 `[model_name]` 前缀。

---

## 11. 贡献指南

我们欢迎社区贡献！如果您开发了新的路由策略、学习目标、训练范式或评估协议，请提交 PR 将其集成到 LLMRouter。

### 11.1 添加新路由器

1. 在 `llmrouter/models/` 或 `custom_routers/` 中创建新目录
2. 实现 `MetaRouter` 接口
3. 添加 README 和配置示例
4. 添加测试（可选）
5. 提交 PR

### 11.2 添加新任务

1. 在 `custom_tasks/` 中创建任务格式化器
2. 使用 `@register_prompt` 注册任务
3. 添加提示词模板
4. 提交 PR

### 11.3 报告问题

请在 GitHub Issues 中报告 bug 或请求新功能。

---

## 12. 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 13. 引用

如果您在研究中使用了 LLMRouter，请引用：

```bibtex
@misc{llmrouter2025,
  title        = {LLMRouter: An Open-Source Library for LLM Routing},
  author       = {Tao Feng and Haozhen Zhang and Zijie Lei and Haodong Yue and Chongshan Lin and Ge Liu and Jiaxuan You},
  year         = {2025},
  howpublished = {\url{https://github.com/ulab-uiuc/LLMRouter}},
  note         = {GitHub repository}
}
```

---

## 14. 相关资源

- **主页**: https://github.com/ulab-uiuc/LLMRouter
- **文档**: https://ulab-uiuc.github.io/LLMRouter/
- **Slack 社区**: [加入我们](https://join.slack.com/t/llmrouteropen-ri04588/shared_invite/zt-3mkx82cut-A25v5yR52xVKi7_jm_YK_w)
- **微信交流群**: 查看项目主页获取二维码

---

## 15. 致谢

LLMRouter 构建于社区优秀研究工作之上。我们感谢以下启发了路由器实现的工作：

- [RouteLLM](https://arxiv.org/abs/2406.18665) - ICLR 2025
- [RouterDC](https://arxiv.org/abs/2409.19886) - NeurIPS 2024
- [AutoMix](https://arxiv.org/abs/2310.12963) - NeurIPS 2024
- [Hybrid LLM](https://arxiv.org/abs/2404.14618) - ICLR 2024
- [GraphRouter](https://arxiv.org/abs/2410.03834) - ICLR 2025
- [GMTRouter](https://arxiv.org/abs/2511.08590)
- [PersonalizedRouter](https://arxiv.org/abs/2511.16883)
- [Router-R1](https://arxiv.org/abs/2506.09033) - NeurIPS 2025
- [FusionFactory](https://arxiv.org/abs/2507.10540)

---

*最后更新：2026-05*
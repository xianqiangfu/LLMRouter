# Configs 目录说明

本目录包含 LLMRouter 项目的配置文件，用于模型训练和测试。

## 目录结构

```
configs/
├── model_config_train/    # 训练配置文件目录
├── model_config_test/     # 测试配置文件目录
├── openclaw_example.yaml  # OpenClaw Router 示例配置
└── README.md              # 英文文档
```

## model_config_train（训练配置）

训练配置文件用于训练不同的路由模型。每个路由器对应一个配置文件。

### 支持的路由器类型

- `automix.yaml` - AutoMix 路由器（基于 POMDP 的自适应路由）
- `knnrouter.yaml` - K近邻路由器
- `mlprouter.yaml` - 多层感知机路由器
- `svmrouter.yaml` - 支持向量机路由器
- `mfrouter.yaml` - 矩阵分解路由器
- `elorouter.yaml` - Elo 评级路由器
- `dcrouter.yaml` - 深度分类路由器
- `graphrouter.yaml` - 图路由器
- `causallm_router.yaml` - 因果语言模型路由器
- `gmtrouter.yaml` - 图神经路由器
- `knnmultiroundrouter.yaml` - KNN 多轮路由器
- `llmmultiroundrouter.yaml` - LLM 多轮路由器
- `personalizedrouter.yaml` - 个性化路由器
- `hybrid_llm.yaml` - 混合 LLM 路由器

### 训练配置文件结构

#### 1. data_path - 数据路径配置

```yaml
data_path:
  query_data_train: 'path/to/query_train.jsonl'           # 训练查询数据
  query_data_test: 'path/to/query_test.jsonl'             # 测试查询数据
  query_embedding_data: 'path/to/embeddings.pt'          # 查询嵌入数据（可选）
  routing_data_train: 'path/to/routing_train.jsonl'      # 路由训练数据
  routing_data_test: 'path/to/routing_test.jsonl'        # 路由测试数据
  llm_data: 'path/to/llm.json'                           # LLM 候选模型信息
  llm_embedding_data: 'path/to/llm_embeddings.json'      # LLM 嵌入数据
```

#### 2. model_path - 模型路径配置

```yaml
model_path:
  ini_model_path: ''                     # 初始模型路径（预训练模型）
  save_model_path: 'path/to/save.pkl'    # 保存模型路径
```

#### 3. metric - 评估指标配置

```yaml
metric:
  weights:
    performance: 1    # 性能权重
    cost: 0           # 成本权重
    llm_judge: 0      # LLM 评分权重
```

#### 4. hparam - 超参数配置

超参数根据路由器类型而异。以下是不同路由器的常见超参数：

**AutoMix 路由器：**
```yaml
hparam:
  routing_method: "POMDP"           # 路由方法: "Threshold", "SelfConsistency", "POMDP"
  num_bins: 8                       # 离散化箱数
  small_model_cost: 1               # 小模型成本
  large_model_cost: 50              # 大模型成本
  verifier_cost: 1                  # 验证器成本
  device: "cpu"                     # 计算设备: "cpu" 或 "cuda"
  verbose: true                     # 是否打印详细输出
  cost_constraint: null             # 成本约束 (min_cost, max_cost)
  num_inference_samples: 2          # 推理采样数量
  max_workers: 1                    # 并行工作进程数
```

**KNN 路由器：**
```yaml
hparam:
  n_neighbors: 5        # 邻居数量 (K 值)
  weights: "uniform"    # 权重函数: "uniform" 或 "distance"
  algorithm: "auto"     # 邻近算法: "auto", "ball_tree", "kd_tree", "brute"
  leaf_size: 30         # BallTree/KDTree 叶子大小
  p: 2                  # Minkowski 距离幂参数 (1: 曼哈顿, 2: 欧几里得)
  metric: "minkowski"   # 距离度量: "minkowski", "cosine" 等
  n_jobs: -1            # 并行任务数 (-1: 使用所有 CPU 核心)
```

**MLP 路由器：**
```yaml
hparam:
  hidden_layer_sizes: [128, 64]   # 隐藏层神经元数量
  activation: "relu"              # 激活函数: "relu", "tanh", "logistic", "identity"
  lr: 0.001                       # 学习率
  epochs: 100                     # 训练轮数
  batch_size: 32                  # 批次大小
  alpha: 0.0001                   # L2 正则化系数
```

## model_config_test（测试配置）

测试配置文件用于评估训练好的路由模型。结构类似训练配置，主要区别在于：

### 测试配置文件结构

```yaml
data_path:
  # 与训练配置相同的数据路径
  ...

model_path:
  load_model_path: 'path/to/saved_model.pkl'  # 加载训练好的模型

metric:
  weights:
    performance: 1
    cost: 0
    llm_judge: 0

hparam:
  # 与训练配置相同的超参数
  inference_mode: true    # 推理模式标志，跳过数据预处理
  ...
```

### 主要区别

| 配置项 | 训练配置 | 测试配置 |
|--------|---------|---------|
| `model_path.ini_model_path` | 初始模型路径 | 无 |
| `model_path.save_model_path` | 保存路径 | 无 |
| `model_path.load_model_path` | 无 | 加载路径 |
| `hparam.inference_mode` | 无或 false | true |

### 测试配置中的额外路由器

测试配置目录还包含以下额外的路由器配置：
- `largest_llm.yaml` - 最大LLM路由器（始终选择最大的模型）
- `smallest_llm.yaml` - 最小LLM路由器（始终选择最小的模型）
- `router_r1.yaml` - R1 路由器

## openclaw_example.yaml（OpenClaw Router 示例）

这是 OpenClaw Router 的完整配置示例，用于在生产环境中部署路由服务。

### 主要配置部分

#### 1. 服务器设置

```yaml
serve:
  host: "0.0.0.0"               # 监听地址
  port: 8000                    # 监听端口
  show_model_prefix: true       # 在响应中添加模型名称前缀
```

#### 2. 路由策略配置

支持的路由策略：
- `random` - 随机选择模型（可选权重）
- `round_robin` - 轮询模型
- `rules` - 基于关键词的规则路由
- `llm` - 使用 LLM 决定路由
- `llmrouter` - 使用 ML 路由器

```yaml
router:
  strategy: random              # 路由策略
  weights:                      # random 策略的权重
    model1: 3
    model2: 1

  # 或使用规则路由
  # strategy: rules
  # rules:
  #   - keywords: ["code", "python"]
  #     model: model1
  #   - default: model2

  # 或使用 ML 路由器
  # strategy: llmrouter
  # llmrouter:
  #   name: knnrouter
  #   config_path: configs/model_config_train/knnrouter.yaml
  #   model_path: saved_models/knnrouter.pt
```

#### 3. API 密钥配置

```yaml
api_keys:
  nvidia:
    - nvapi-xxx...
  openai: ${OPENAI_API_KEY}      # 支持环境变量
  anthropic: ${ANTHROPIC_API_KEY}
```

#### 4. 路由记忆（可选）

```yaml
memory:
  enabled: false                 # 是否启用记忆功能
  top_k: 10                      # 检索相似历史查询数量
  retriever_model: "facebook/contriever-msmarco"  # 检索模型
  device: "cpu"                  # 计算设备
  max_length: 256                # 最大长度
  per_user: false                # 是否按用户隔离
```

#### 5. LLM 后端配置

```yaml
llms:
  model_name:
    provider: nvidia             # 提供商
    model: meta/llama-3.1-8b-instruct
    base_url: https://integrate.api.nvidia.com/v1
    description: "模型描述"
    max_tokens: 1024             # 最大输出令牌数
    context_limit: 128000        # 上下文窗口大小
    input_price: 0.2             # 输入价格 (每 1M 令牌)
    output_price: 0.2            # 输出价格 (每 1M 令牌)
```

## 使用方法

### 训练模型

```bash
python train.py --config configs/model_config_train/automix.yaml
```

### 测试模型

```bash
python test.py --config configs/model_config_test/automix.yaml
```

### 启动 OpenClaw Router 服务

```bash
llmrouter serve --config configs/openclaw_example.yaml
```

## 关键参数说明

### 通用参数

| 参数 | 说明 | 默认值 |
|-----|------|--------|
| `device` | 计算设备 ("cpu" 或 "cuda") | "cpu" |
| `verbose` | 是否打印详细输出 | true/false |
| `max_workers` | 并行工作进程数 | 1 |

### 评估指标权重

| 权重 | 说明 |
|-----|------|
| `performance` | 模型性能权重（如准确率） |
| `cost` | 成本权重（如 API 调用成本） |
| `llm_judge` | LLM 评分权重（使用另一个 LLM 评估质量） |

### 成本配置

| 参数 | 说明 |
|-----|------|
| `small_model_cost` | 小模型的相对成本 |
| `large_model_cost` | 大模型的相对成本 |
| `verifier_cost` | 验证器的相对成本 |

## 配置文件示例

以下是一个完整的训练配置示例（以 AutoMix 为例）：

```yaml
# Config parameters for automix training:

data_path:
  query_data_train: 'data/example_data/query_data/default_query_train.jsonl'
  query_data_test: 'data/example_data/query_data/default_query_test.jsonl'
  routing_data_train: 'data/example_data/routing_data/default_routing_train_data.jsonl'
  routing_data_test: 'data/example_data/routing_data/default_routing_test_data.jsonl'
  llm_data: 'data/example_data/llm_candidates/default_llm.json'
  llm_embedding_data: 'data/example_data/llm_candidates/default_llm_embeddings.json'

model_path:
  ini_model_path: ''
  save_model_path: 'saved_models/automix/automix_model.pkl'

metric:
  weights:
    performance: 1
    cost: 0
    llm_judge: 0

hparam:
  routing_method: "POMDP"
  num_bins: 8
  small_model_cost: 1
  large_model_cost: 50
  verifier_cost: 1
  device: "cpu"
  verbose: true
  cost_constraint: null
  num_inference_samples: 2
  max_workers: 1
```

## 注意事项

1. **路径配置**：所有路径应使用相对路径或绝对路径，建议使用正斜杠 `/`
2. **数据格式**：确保数据文件格式与配置文件中的格式一致
3. **模型保存**：训练配置中的 `save_model_path` 应与测试配置中的 `load_model_path` 匹配
4. **设备选择**：使用 `cuda` 需要安装 CUDA 支持的 PyTorch
5. **API 密钥**：OpenClaw 配置中的 API 密钥建议使用环境变量

## 更多信息

- 项目主页：[LLMRouter GitHub](https://github.com/LLMRouter)
- 路由器详细说明：请参考项目文档
- OpenClaw 集成：请参考 `openclaw_example.yaml` 中的说明
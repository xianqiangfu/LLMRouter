# LLMRouter Models 模块

本目录包含 LLMRouter 框架中所有的路由器（Router）实现及其训练器（Trainer）。

## 目录

- [MetaRouter 基类](#metarouter-基类)
- [BaseTrainer 训练器基类](#basetrainer-训练器基类)
- [路由器实现列表](#路由器实现列表)
- [路由器继承关系图](#路由器继承关系图)
- [训练与推理接口](#训练与推理接口)

---

## MetaRouter 基类

`MetaRouter` 是所有路由器的抽象基类，定义了统一的接口规范。

### 核心职责

1. **模型管理**：持有底层的 PyTorch 模型（`nn.Module`）
2. **配置加载**：可选地从 YAML 配置文件加载配置和数据
3. **路由接口**：提供标准化的路由方法（`route_batch()`、`route_single()`）
4. **工具方法**：提供度量计算、模型保存/加载等通用功能

### 核心方法

| 方法 | 类型 | 说明 |
|------|------|------|
| `__init__(model, yaml_path, resources)` | 构造函数 | 初始化路由器，可选加载 YAML 配置和数据 |
| `route_batch(batch)` | 抽象方法 | 批量路由查询，每个子类必须实现 |
| `route_single(batch)` | 抽象方法 | 单个查询路由，每个子类必须实现 |
| `forward(batch)` | 实例方法 | PyTorch 兼容的前向传播，委托给 `route_batch()` |
| `compute_metrics(outputs, batch)` | 实例方法 | 可选的度量计算方法 |
| `save_router(path)` | 实例方法 | 保存路由器状态到磁盘 |
| `load_router(path)` | 实例方法 | 从磁盘加载路由器状态 |

### 初始化流程

当提供 `yaml_path` 时，MetaRouter 会自动执行以下步骤：

1. 加载 YAML 配置文件
2. 通过 `DataLoader` 加载训练和测试数据
3. 加载度量权重（如果配置中指定）

---

## BaseTrainer 训练器基类

`BaseTrainer` 是所有训练器的抽象基类，定义了统一的训练接口。

### 核心方法

| 方法 | 类型 | 说明 |
|------|------|------|
| `__init__(router, optimizer, device)` | 构造函数 | 初始化训练器，设置路由器、优化器和设备 |
| `loss_func(outputs, batch)` | 抽象方法 | 计算损失函数，每个子类必须实现 |
| `train(dataloader)` | 抽象方法 | 执行训练循环，每个子类必须实现 |

### 设计理念

训练逻辑与路由器逻辑**解耦**，每个路由器都有对应的训练器类：

- `KNNRouter` → `KNNRouterTrainer`
- `MLPRouter` → `MLPTrainer`
- `SVMRouter` → `SVMRouterTrainer`
- `MFRouter` → `MFRouterTrainer`
- `EloRouter` → `EloRouterTrainer`
- `AutomixRouter` → `AutomixRouterTrainer`
- `DCRouter` → `DCTrainer`
- `HybridLLMRouter` → `HybridLLMTrainer`

---

## 路由器实现列表

### 1. 基线路由器（Baseline）

| 路由器 | 类名 | 说明 | 是否需要训练 |
|--------|------|------|--------------|
| SmallestLLM | `SmallestLLM` | 始终选择最小的 LLM | 否 |
| LargestLLM | `LargestLLM` | 始终选择最大的 LLM | 否 |

### 2. 传统机器学习路由器

| 路由器 | 类名 | 核心算法 | 是否需要训练 |
|--------|------|----------|--------------|
| KNN Router | `KNNRouter` | K-近邻分类 | 是 |
| SVM Router | `SVMRouter` | 支持向量机 | 是 |
| MLP Router | `MLPRouter` | 多层感知机（基于 PyTorch） | 是 |
| MF Router | `MFRouter` | 双线性矩阵分解 | 是 |

### 3. 排名与评分路由器

| 路由器 | 类名 | 核心算法 | 是否需要训练 |
|--------|------|----------|--------------|
| Elo Router | `EloRouter` | Elo 评分系统 | 是 |

### 4. 自适应路由器

| 路由器 | 类名 | 核心算法 | 是否需要训练 |
|--------|------|----------|--------------|
| Automix Router | `AutomixRouter` | 自验证路由（支持 POMDP、Threshold、SelfConsistency） | 是 |
| Hybrid LLM Router | `HybridLLMRouter` | 混合 LLM 路由 | 是 |
| DC Router | `DCRouter` | 动态聚类路由 | 是 |

### 5. 图神经网络路由器

| 路由器 | 类名 | 核心算法 | 是否需要训练 |
|--------|------|----------|--------------|
| Graph Router | `GraphRouter` | 图神经网络路由 | 是 |
| GMT Router | `GMTRouter` | GMT 路由 | 是 |

### 6. 特殊路由器

| 路由器 | 类名 | 核心算法 | 是否需要训练 |
|--------|------|----------|--------------|
| CausalLM Router | `CausalLMRouter` | 因果语言模型路由 | 是 |
| Router R1 | `RouterR1` | R1 路由器 | 是 |
| Personalized Router | `PersonalizedRouter` | 个性化路由 | 是 |

### 7. 多轮路由器

| 路由器 | 类名 | 核心算法 | 是否需要训练 |
|--------|------|----------|--------------|
| KNN Multi-round Router | `KNNMultiRoundRouter` | 多轮 KNN 路由 | 是 |
| LLM Multi-round Router | `LLMMultiRoundRouter` | 多轮 LLM 路由 | 是 |

---

## 路由器继承关系图

```
MetaRouter (基类)
├── SmallestLLM
├── LargestLLM
├── KNNRouter
├── SVMRouter
├── MLPRouter
├── MFRouter
├── EloRouter
├── AutomixRouter
├── DCRouter
├── HybridLLMRouter
├── GraphRouter
├── GMTRouter
├── CausalLMRouter
├── RouterR1
├── PersonalizedRouter
├── KNNMultiRoundRouter
└── LLMMultiRoundRouter
```

---

## 训练与推理接口

### 推理接口

所有路由器都提供统一的推理接口：

#### 1. 单查询路由

```python
router = Router(yaml_path="config/router.yaml")
query = {"query": "你的问题"}
result = router.route_single(query)
print(result["model_name"])  # 输出: 选中的模型名称
```

#### 2. 批量路由

```python
# 方式 1: 使用传入的批次
batch = [
    {"query": "问题1", "task_name": "mmlu"},
    {"query": "问题2", "task_name": "gsm8k"}
]
results = router.route_batch(batch=batch, task_name=None)

# 方式 2: 使用测试集数据
results = router.route_batch()  # 自动使用 self.query_data_test
```

#### 3. 输出格式

每个查询的返回结果包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `query` | str | 原始查询文本 |
| `formatted_query` | str | 任务格式化后的查询（可选） |
| `model_name` | str | 选中的模型名称 |
| `response` | str | 模型生成的响应 |
| `prompt_tokens` | int | 输入 token 数 |
| `completion_tokens` | int | 输出 token 数 |
| `input_token` | int | 输入 token 数（别名） |
| `output_token` | int | 输出 token 数（别名） |
| `success` | bool | API 调用是否成功 |
| `task_performance` | float | 任务性能指标（如果有 ground truth） |

### 训练接口

每个路由器都有对应的训练器，通用训练流程如下：

```python
from llmrouter.models import MLPRouter, MLPTrainer
import torch.optim as optim

# 1. 初始化路由器
router = MLPRouter(yaml_path="config/mlp_router.yaml")

# 2. 初始化训练器
optimizer = optim.Adam(router.parameters(), lr=0.001)
trainer = MLPTrainer(router, optimizer=optimizer, device="cuda")

# 3. 执行训练
trainer.train()

# 4. 保存模型
router.save_router("models/mlp_router.pth")
```

### 任务格式化支持

路由器支持常见任务类型的格式化，包括：

- `mmlu`: 多项选择题
- `gsm8k`: 数学问题
- `commonsense_qa`: 常识问答
- 其他自定义任务

```python
results = router.route_batch(batch=batch, task_name="mmlu")
# 查询会自动格式化为选择题格式
```

---

## 使用示例

### 完整的推理流程

```python
from llmrouter.models import MLPRouter

# 初始化路由器
router = MLPRouter(yaml_path="configs/mlp_router.yaml")

# 准备查询
queries = [
    {"query": "What is the capital of France?", "task_name": "commonsense_qa"},
    {"query": "Solve: 2x + 5 = 15", "task_name": "gsm8k"}
]

# 执行批量路由
results = router.route_batch(batch=queries)

# 查看结果
for result in results:
    print(f"Query: {result['query']}")
    print(f"Model: {result['model_name']}")
    print(f"Response: {result['response']}")
    print(f"Performance: {result.get('task_performance', 'N/A')}")
    print("---")
```

### 完整的训练流程

```python
from llmrouter.models import KNNRouter, KNNRouterTrainer

# 初始化路由器
router = KNNRouter(yaml_path="configs/knn_router.yaml")

# 初始化训练器
trainer = KNNRouterTrainer(router, device="cuda")

# 训练路由器
trainer.train()

# 保存模型
router.save_router("models/knn_router.pkl")
```

---

## 配置示例

每个路由器都需要一个 YAML 配置文件，包含以下部分：

```yaml
# 模型路径
model_path:
  load_model_path: "models/router.pkl"

# 数据路径
data_path:
  llm_data: "data/llm_data.json"
  routing_data_train: "data/routing_train.jsonl"
  routing_data_test: "data/routing_test.jsonl"

# 超参数
hparam:
  n_neighbors: 5        # KNN 参数
  metric: "cosine"      # 距离度量

# 训练参数
train_param:
  epochs: 10
  batch_size: 32

# API 端点
api_endpoint: "https://api.example.com/v1"

# 度量配置
metric:
  weights:
    accuracy: 0.5
    cost: 0.3
    latency: 0.2
```

---

## 导入方式

```python
# 基类
from llmrouter.models import MetaRouter, BaseTrainer

# 基线路由器
from llmrouter.models import SmallestLLM, LargestLLM

# 传统机器学习路由器
from llmrouter.models import (
    KNNRouter, KNNRouterTrainer,
    SVMRouter, SVMRouterTrainer,
    MLPRouter, MLPTrainer,
    MFRouter, MFRouterTrainer
)

# 排名路由器
from llmrouter.models import EloRouter, EloRouterTrainer

# 自适应路由器
from llmrouter.models import (
    AutomixRouter, AutomixRouterTrainer,
    DCRouter, DCTrainer,
    HybridLLMRouter, HybridLLMTrainer
)

# 图神经网络路由器（可选）
try:
    from llmrouter.models import GraphRouter, GraphTrainer
except Exception:
    GraphRouter = None
    GraphTrainer = None

# 其他路由器（可选）
try:
    from llmrouter.models import CausalLMRouter, CausalLMTrainer
except Exception:
    CausalLMRouter = None
    CausalLMTrainer = None
```

---

## 注意事项

1. **延迟加载**：部分路由器（如 EloRouter、MFRouter、MLPRouter）采用延迟加载策略，只在推理时才加载模型参数。

2. **API 配置**：确保在 `llm_data.json` 或 YAML 配置中正确设置每个模型的 `api_endpoint`。

3. **设备支持**：基于 PyTorch 的路由器（如 MLPRouter、MFRouter）支持 CUDA 加速。

4. **异常处理**：部分高级路由器（如 GraphRouter、CausalLMRouter）可能有额外的依赖，使用时需要处理导入异常。

5. **任务格式化**：使用 `task_name` 参数时，确保任务类型在系统中已定义。
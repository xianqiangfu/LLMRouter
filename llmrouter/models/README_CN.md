# LLMRouter 路由器模型目录说明

## 简介

`llmrouter/models/` 目录包含了各种 LLM 路由器的实现，用于根据查询内容智能地将请求路由到最合适的语言模型。所有路由器都继承自统一的 `MetaRouter` 基类，提供一致的接口。

## 路由器模型分类

### 1. 单轮路由器 (Single-Round Routers)

单轮路由器为每个查询进行一次路由决策，选择最适合的模型。

| 路由器 | 特点 | 适用场景 |
|--------|------|----------|
| **KNNRouter** | 基于 K 近邻分类器，使用查询嵌入进行相似度匹配 | 数据集较小，需要快速原型开发 |
| **SVMRouter** | 基于支持向量机分类器 | 需要清晰的决策边界 |
| **MLPRouter** | 基于多层感知机神经网络，支持 CUDA 加速 | 需要深度学习，数据量较大 |
| **MFRouter** | 基于矩阵分解 | 需要捕捉用户-模型交互模式 |
| **EloRouter** | 基于 Elo 等级分系统 | 需要动态调整模型排名 |
| **DCRouter** | 基于深度聚类 | 需要对查询进行分组 |
| **HybridLLMRouter** | 混合模型路由策略 | 复杂场景，需要多种策略结合 |

### 2. 多轮路由器 (Multi-Round Routers)

多轮路由器支持查询分解和多步骤处理，适用于复杂问题。

| 路由器 | 特点 | 适用场景 |
|--------|------|----------|
| **KNNMultiRoundRouter** | 基于 KNN 的多轮路由，支持查询分解 | 需要将复杂问题分解为子问题 |
| **LLMMultiRoundRouter** | 使用 LLM 进行查询分解和路由（无训练） | 需要零样本多轮推理 |

### 3. 个性化路由器 (Personalized Routers)

考虑用户偏好和个性化因素的路由器。

| 路由器 | 特点 | 适用场景 |
|--------|------|----------|
| **PersonalizedRouter** | 基于图神经网络（GNN）建模用户-任务-模型关系 | 需要考虑用户个性化偏好 |

### 4. 代理路由器 (Agent Routers)

基于智能体推理的路由器。

| 路由器 | 特点 | 适用场景 |
|--------|------|----------|
| **RouterR1** | 基于 R1 风格的代理推理和路由，支持动态搜索 | 需要深度推理和信息检索 |

### 5. 图路由器 (Graph Routers)

基于图神经网络的路由器。

| 路由器 | 特点 | 适用场景 |
|--------|------|----------|
| **GraphRouter** | 使用 GNN 建模查询-模型关系 | 需要捕捉模型间的复杂关系 |

### 6. 自适应路由器 (Adaptive Routers)

根据输出质量动态调整路由决策。

| 路由器 | 特点 | 适用场景 |
|--------|------|----------|
| **AutomixRouter** | 基于自验证的自适应路由，在小模型和大模型间切换 | 需要在性能和成本之间平衡 |

### 7. 基准路由器 (Baseline Routers)

用于性能对比的简单基准路由器。

| 路由器 | 特点 | 适用场景 |
|--------|------|----------|
| **SmallestLLM** | 始终路由到最小模型 | 性能基准 |
| **LargestLLM** | 始终路由到最大模型 | 性能基准 |

### 8. 其他路由器

| 路由器 | 特点 | 适用场景 |
|--------|------|----------|
| **GMTRouter** | 基于 GPT 的路由器 | 需要语言模型理解 |
| **CausalLMRouter** | 因果语言模型路由 | 需要因果推理 |

## 核心基类

### MetaRouter

`MetaRouter` 是所有路由器的抽象基类，定义了统一的接口：

```python
class MetaRouter(nn.Module, ABC):
    """所有 LLM 路由器的统一抽象基类"""
    
    def __init__(self, model: nn.Module, yaml_path: str | None = None, resources=None)
    
    # 必须实现的抽象方法
    @abstractmethod
    def route_batch(self, batch)
    @abstractmethod
    def route_single(self, batch)
    
    # 可选方法
    def forward(self, batch)  # PyTorch 兼容的 forward 方法
    def compute_metrics(self, outputs, batch) -> dict
    def save_router(self, path: str)
    def load_router(self, path: str)
```

**职责：**
- 管理底层的 PyTorch 模型
- 加载配置和数据
- 提供标准的路由接口：`route()` / `forward()`
- 提供基础工具：指标计算、模型保存/加载

训练逻辑与路由器解耦，由 `Trainer` 类处理。

### BaseTrainer

`BaseTrainer` 是所有训练器的抽象基类，定义了统一的训练接口：

```python
class BaseTrainer(ABC):
    """所有路由器训练器的统一抽象基类"""
    
    def __init__(
        self,
        router: torch.nn.Module,
        optimizer: torch.optim.Optimizer | None = None,
        device: str = "cuda",
        **kwargs: Any,
    )
    
    # 必须实现的抽象方法
    @abstractmethod
    def loss_func(self, outputs: Any, batch: Any) -> torch.Tensor
    @abstractmethod
    def train(self, dataloader: Any = None)
```

**职责：**
- 定义损失计算逻辑
- 定义完整的训练循环
- 管理优化器和设备

## 路由器选择指南

### 根据场景选择

| 场景 | 推荐路由器 | 理由 |
|------|-----------|------|
| 快速原型开发 | KNNRouter | 实现简单，训练快速 |
| 大规模生产环境 | MLPRouter | 支持批量处理，性能优异 |
| 复杂问题分解 | LLMMultiRoundRouter / KNNMultiRoundRouter | 支持多步推理 |
| 个性化推荐 | PersonalizedRouter | 考虑用户偏好 |
| 性能与成本平衡 | AutomixRouter | 自适应在大小模型间切换 |
| 深度推理 | RouterR1 | 支持智能体推理和信息检索 |
| 需要模型关系建模 | GraphRouter | 使用 GNN 捕捉复杂关系 |
| 零样本部署 | LLMMultiRoundRouter | 无需训练，开箱即用 |

### 根据数据特点选择

| 数据特点 | 推荐路由器 | 理由 |
|---------|-----------|------|
| 数据量小 | KNNRouter, SVMRouter | 避免过拟合 |
| 数据量大 | MLPRouter, GraphRouter | 深度学习模型表现更好 |
| 有用户偏好 | PersonalizedRouter | 利用用户信息 |
| 需要实时更新 | EloRouter | 动态调整排名 |
| 成本敏感 | AutomixRouter | 优先使用小模型 |

### 根据性能需求选择

| 性能需求 | 推荐路由器 | 理由 |
|---------|-----------|------|
| 最高准确率 | LargestLLM (基准) | 始终选择最强模型 |
| 最佳性价比 | AutomixRouter, MLPRouter | 平衡性能和成本 |
| 最低延迟 | SmallestLLM (基准) | 始终选择最小模型 |
| 需要解释性 | KNNRouter, SVMRouter | 决策过程可解释 |

## 训练器

每个路由器通常配有对应的训练器：

| 路由器 | 训练器 |
|--------|--------|
| KNNRouter | KNNRouterTrainer |
| SVMRouter | SVMRouterTrainer |
| MLPRouter | MLPTrainer |
| MFRouter | MFRouterTrainer |
| EloRouter | EloRouterTrainer |
| DCRouter | DCTrainer |
| HybridLLMRouter | HybridLLMTrainer |
| AutomixRouter | AutomixRouterTrainer |
| GraphRouter | GraphTrainer |
| CausalLMRouter | CausalLMTrainer |
| PersonalizedRouter | PersonalizedRouterTrainer |
| GMTRouter | GMTRouterTrainer |

## 使用示例

### 基本使用

```python
from llmrouter.models import KNNRouter, KNNRouterTrainer

# 初始化路由器
router = KNNRouter(yaml_path="configs/knn_router.yaml")

# 训练路由器
trainer = KNNRouterTrainer(router)
trainer.train()

# 单次路由
query = {"query": "What is machine learning?"}
result = router.route_single(query)
print(f"Selected model: {result['model_name']}")

# 批量路由
queries = [
    {"query": "Explain neural networks"},
    {"query": "What is deep learning?"}
]
results = router.route_batch(queries)
```

### 批量路由并执行

```python
from llmrouter.models import MLPRouter

router = MLPRouter(yaml_path="configs/mlp_router.yaml")

# 加载训练好的模型
router.load_router("models/mlp_router.pt")

# 批量路由并自动执行 API 调用
queries = [
    {"query": "What is Python?", "task_name": "mmlu"},
    {"query": "Explain machine learning", "task_name": "commonsense_qa"}
]
results = router.route_batch(queries)

for result in results:
    print(f"Query: {result['query']}")
    print(f"Model: {result['model_name']}")
    print(f"Response: {result['response']}")
    print(f"Performance: {result.get('task_performance', 'N/A')}")
    print("---")
```

## 配置文件

每个路由器需要对应的 YAML 配置文件，通常包含以下部分：

```yaml
# 数据路径
data_path:
  routing_data_train: "data/train.csv"
  routing_data_test: "data/test.csv"
  llm_data: "data/llm_data.json"
  query_embedding_data: "data/query_embeddings.pkl"

# 模型路径
model_path:
  save_model_path: "models/router.pt"
  load_model_path: "models/router.pt"

# 超参数
hparam:
  learning_rate: 0.001
  batch_size: 32
  epochs: 100

# LLM 数据
llm_data:
  GPT4:
    size: "175B"
    embedding: [0.12, 0.33, 0.78, 0.44]
  Claude3:
    size: "52B"
    embedding: [0.10, 0.25, 0.70, 0.50]

# 指标权重
metric:
  weights:
    performance: 0.7
    cost: 0.2
    latency: 0.1
```

## 扩展新路由器

要创建新的路由器：

1. 创建新的子目录 `llmrouter/models/your_router/`
2. 实现 `router.py`，继承 `MetaRouter`
3. 实现 `trainer.py`，继承 `BaseTrainer`（如果需要训练）
4. 创建 `__init__.py`，导出路由器和训练器
5. 在 `llmrouter/models/__init__.py` 中注册新路由器

```python
# llmrouter/models/your_router/router.py
from llmrouter.models.meta_router import MetaRouter
import torch.nn as nn

class YourRouter(MetaRouter):
    def __init__(self, yaml_path: str):
        dummy_model = nn.Identity()
        super().__init__(model=dummy_model, yaml_path=yaml_path)
        # 初始化逻辑
    
    def route_single(self, batch):
        # 实现单次路由
        pass
    
    def route_batch(self, batch):
        # 实现批量路由
        pass
```

## 注意事项

1. **依赖管理**：某些路由器需要可选依赖（如 `vllm`），使用前请确保已安装
2. **GPU 支持**：深度学习路由器（如 MLPRouter, GraphRouter）支持 CUDA 加速
3. **数据格式**：确保输入数据包含所需的字段（query, query_embedding 等）
4. **模型加载**：使用 `load_router()` 加载预训练模型，使用 `save_router()` 保存训练结果
5. **API 配置**：配置正确的 API 端点和密钥以支持自动执行

## 相关文档

- [数据目录说明](../data/README_CN.md)
- [ComfyUI 目录说明](../ComfyUI/README_CN.md)
- [自定义路由器目录说明](../custom_routers/README_CN.md)
- [脚本目录说明](../scripts/README_CN.md)
# LLMRouter 核心包

LLMRouter 是一个智能大语言模型路由框架，能够根据查询内容自动选择最合适的 LLM 模型，实现性能与成本的最佳平衡。

## 目录

- [核心架构](#核心架构)
- [子模块概述](#子模块概述)
- [核心类和接口](#核心类和接口)
- [快速开始](#快速开始)
- [API 参考](#api-参考)

---

## 核心架构

LLMRouter 核心包采用模块化设计，主要包含以下四个核心模块：

```
llmrouter/
├── cli/              # 命令行接口
├── data/             # 数据处理模块
├── evaluation/       # 评估模块
├── models/           # 路由器模型和训练器
└── __init__.py       # 包初始化
```

### 设计理念

1. **统一抽象**：通过 `MetaRouter` 基类为所有路由器提供统一接口
2. **关注点分离**：路由逻辑与训练逻辑解耦（Router 与 Trainer 分离）
3. **可扩展性**：支持自定义路由器、训练器和评估指标
4. **模块化**：各子模块职责清晰，可独立使用或组合使用

---

## 子模块概述

### 1. CLI 模块 (`cli/`)

提供完整的命令行界面，支持训练、推理、聊天和服务功能。

**核心文件：**

| 文件 | 功能 |
|------|------|
| `router_main.py` | 主 CLI 入口，包含所有子命令（train/infer/chat/serve/list-routers/version） |
| `router_train.py` | 训练子命令实现，路由器训练注册表 |
| `router_inference.py` | 推理子命令实现，路由器推理注册表 |
| `router_chat.py` | 聊天子命令实现，基于 Gradio 的交互界面 |

**支持的命令：**

- `llmrouter train` - 训练路由器模型
- `llmrouter infer` - 执行路由推理
- `llmrouter chat` - 启动交互式聊天界面
- `llmrouter serve` - 启动 OpenAI 兼容的 API 服务器
- `llmrouter list-routers` - 列出所有可用的路由器
- `llmrouter version` - 显示版本信息

### 2. Data 模块 (`data/`)

提供数据生成、加载和验证功能，是路由器训练和评估的数据基础。

**核心文件：**

| 文件 | 功能 |
|------|------|
| `data.py` | 数据格式定义和验证（StandardQueryData、GMTRouterInteraction） |
| `data_loader.py` | 数据加载器，支持从 YAML 配置加载数据 |
| `data_generation.py` | 从基准数据集生成查询数据（11 个数据集支持） |
| `generate_llm_embeddings.py` | 为 LLM 候选模型生成嵌入向量 |
| `api_calling_evaluation.py` | 调用 LLM API 并评估响应，生成路由数据 |
| `multimodal_generation.py` | 多模态数据生成支持 |

**数据流程：**

```
配置 (YAML)
  ↓
步骤 2a: 生成查询数据 → query_data_train.jsonl + query_data_test.jsonl
  ↓
步骤 2b: 生成 LLM 嵌入 → default_llm_embeddings.json
  ↓
步骤 3: API 调用与评估 → query_embeddings_longformer.pt + routing_data
```

**支持的数据集：**

- Natural QA
- Trivia QA
- MMLU
- GPQA
- MBPP
- HumanEval
- GSM8K
- CommonsenseQA
- MATH
- OpenbookQA
- ARC-Challenge

### 3. Evaluation 模块 (`evaluation/`)

提供高层次的批量评估接口，采用装饰器模式支持自定义评估指标。

**核心文件：**

| 文件 | 功能 |
|------|------|
| `batch_evaluator.py` | 批量评估器，支持多种评估指标 |
| `__init__.py` | 导出核心函数和注册表 |
| `example.py` | 使用示例和教程 |

**内置评估指标：**

- `em` - 精确匹配
- `em_mc` - 多选题精确匹配
- `cem` - 包含精确匹配
- `cemf1` - 包含精确匹配 + F1 回退
- `f1` - F1 分数
- `bert_score` - BERT 语义相似度
- `gsm8k` - GSM8K 数学问题评估
- `code_eval` - 代码执行评估

**自定义指标注册：**

```python
from llmrouter.evaluation import evaluation_metric

@evaluation_metric('my_custom_metric')
def my_metric(prediction: str, ground_truth: str, **kwargs) -> float:
    # 自定义评估逻辑
    return 0.5
```

### 4. Models 模块 (`models/`)

包含所有路由器实现及其训练器，是 LLMRouter 的核心算法库。

**核心文件：**

| 文件 | 功能 |
|------|------|
| `meta_router.py` | 所有路由器的抽象基类 MetaRouter |
| `base_trainer.py` | 所有训练器的抽象基类 BaseTrainer |

**路由器类型：**

1. **基线路由器**
   - `SmallestLLM` - 始终选择最小模型
   - `LargestLLM` - 始终选择最大模型

2. **传统机器学习路由器**
   - `KNNRouter` - K-近邻分类
   - `SVMRouter` - 支持向量机
   - `MLPRouter` - 多层感知机
   - `MFRouter` - 双线性矩阵分解

3. **排名与评分路由器**
   - `EloRouter` - Elo 评分系统

4. **自适应路由器**
   - `AutomixRouter` - 自验证路由（支持 POMDP、Threshold、SelfConsistency）
   - `HybridLLMRouter` - 混合 LLM 路由
   - `DCRouter` - 动态聚类路由

5. **图神经网络路由器**
   - `GraphRouter` - 图神经网络路由
   - `GMTRouter` - GMT 路由

6. **特殊路由器**
   - `CausalLMRouter` - 因果语言模型路由
   - `RouterR1` - R1 路由器
   - `PersonalizedRouter` - 个性化路由

7. **多轮路由器**
   - `KNNMultiRoundRouter` - 多轮 KNN 路由
   - `LLMMultiRoundRouter` - 多轮 LLM 路由

---

## 核心类和接口

### MetaRouter 类

所有路由器的抽象基类，定义了统一的接口规范。

**核心方法：**

```python
class MetaRouter(nn.Module, ABC):
    def __init__(self, model: nn.Module, yaml_path: str | None = None, resources=None)

    @abstractmethod
    def route_batch(self, batch) -> Any:
        """批量路由查询"""

    @abstractmethod
    def route_single(self, batch) -> Any:
        """单个查询路由"""

    def forward(self, batch) -> Any:
        """PyTorch 兼容的前向传播"""

    def compute_metrics(self, outputs, batch) -> dict:
        """计算评估指标"""

    def save_router(self, path: str):
        """保存路由器状态"""

    def load_router(self, path: str):
        """加载路由器状态"""
```

### BaseTrainer 类

所有训练器的抽象基类，定义了统一的训练接口。

**核心方法：**

```python
class BaseTrainer(ABC):
    def __init__(self, router: torch.nn.Module, optimizer: torch.optim.Optimizer | None, device: str, **kwargs)

    @abstractmethod
    def loss_func(self, outputs: Any, batch: Any) -> torch.Tensor:
        """计算损失函数"""

    @abstractmethod
    def train(dataloader) -> None:
        """执行训练循环"""
```

### DataLoader 类

数据加载器，支持从 YAML 配置加载数据。

```python
class DataLoader:
    def __init__(self, project_root: str)

    def load_data(self, cfg: dict, router: Any) -> None:
        """从配置加载数据到路由器"""

    @staticmethod
    def to_abs(path: str, project_root: str) -> str:
        """将相对路径转换为绝对路径"""
```

### Evaluation API

评估模块的核心函数。

```python
# 批量评估
def evaluate_batch(data: List[dict], default_metric: str = None) -> List[dict]:
    """对批量数据进行评估"""

# 装饰器注册指标
def evaluation_metric(name: str):
    """注册自定义评估指标"""

# 程序化注册指标
def register_custom_metric(name: str, func: Callable):
    """程序化注册自定义指标"""

# 获取可用指标
def get_available_metrics() -> List[str]:
    """返回所有已注册的评估指标列表"""
```

---

## 快速开始

### 安装依赖

```bash
# 安装核心依赖
pip install torch pyyaml
pip install litellm  # 用于 API 调用

# 可选依赖
pip install gradio   # 用于聊天界面
pip install fastapi uvicorn httpx  # 用于 API 服务器
```

### 设置 API 密钥

```bash
# 服务特定格式（推荐用于多个提供商）
export API_KEYS='{"NVIDIA": "key1,key2", "OpenAI": ["key3", "key4"]}'

# 或使用传统格式
export API_KEYS='["your-key-1", "your-key-2"]'
```

### 训练路由器

```bash
llmrouter train --router knnrouter \
  --config configs/model_config_train/knnrouter.yaml \
  --device cuda
```

### 执行推理

```bash
# 单查询推理
llmrouter infer --router knnrouter \
  --config config.yaml \
  --query "What is AI?"

# 批量推理
llmrouter infer --router knnrouter \
  --config config.yaml \
  --input queries.jsonl \
  --output results.json \
  --output-format jsonl
```

### 启动聊天界面

```bash
llmrouter chat --router knnrouter \
  --config config.yaml \
  --port 8001
```

### 启动 API 服务器

```bash
llmrouter serve --config configs/openclaw_example.yaml --port 8000
```

### 列出可用路由器

```bash
llmrouter list-routers
```

---

## API 参考

### Python API 使用示例

#### 1. 路由器推理

```python
from llmrouter.models import MLPRouter

# 初始化路由器
router = MLPRouter(yaml_path="configs/mlp_router.yaml")

# 单查询路由
result = router.route_single({"query": "What is the capital of France?"})
print(f"Selected model: {result['model_name']}")

# 批量路由
batch = [
    {"query": "Question 1", "task_name": "mmlu"},
    {"query": "Question 2", "task_name": "gsm8k"}
]
results = router.route_batch(batch=batch)
```

#### 2. 路由器训练

```python
from llmrouter.models import KNNRouter, KNNRouterTrainer

# 初始化路由器
router = KNNRouter(yaml_path="configs/knn_router.yaml")

# 初始化训练器
trainer = KNNRouterTrainer(router, device="cuda")

# 执行训练
trainer.train()

# 保存模型
router.save_router("models/knn_router.pkl")
```

#### 3. 数据加载

```python
from llmrouter.data import DataLoader

# 初始化数据加载器
loader = DataLoader(project_root="/path/to/project")

# 加载数据到路由器
loader.load_data(cfg=config_dict, router=router)
```

#### 4. 批量评估

```python
from llmrouter.evaluation import evaluate_batch

# 准备数据
data = [
    {'prediction': 'hello world', 'ground_truth': 'hello', 'metric': 'f1'},
    {'prediction': 'exact match', 'ground_truth': 'exact match', 'metric': 'em'}
]

# 执行评估
results = evaluate_batch(data)

# 查看结果
for result in results:
    print(f"Score: {result['score']}")
```

#### 5. 自定义评估指标

```python
from llmrouter.evaluation import evaluation_metric

@evaluation_metric('length_score')
def length_metric(prediction: str, ground_truth: str, min_length: int = 10, **kwargs) -> float:
    """基于长度的自定义评估指标"""
    return 1.0 if len(prediction) >= min_length else 0.0

# 使用自定义指标
data = [
    {'prediction': 'This is a long text', 'ground_truth': 'short', 'metric': 'length_score', 'min_length': 10}
]
results = evaluate_batch(data)
```

---

## 更多信息

- [数据处理文档](data/README.md) - 详细的数据生成和加载指南
- [评估模块文档](evaluation/README.md) - 评估指标和自定义方法
- [路由器模块文档](models/README.md) - 所有路由器实现和训练接口
- [主项目 README](../README.md) - 项目概述和完整文档

---

## 版本信息

当前版本：0.1.0

可通过以下命令查看版本：

```bash
llmrouter version
```

或在 Python 中：

```python
import llmrouter
print(llmrouter.__version__)
```
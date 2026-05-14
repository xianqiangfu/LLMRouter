# LLMRouter 模块文档

LLMRouter 是一个智能模型路由系统，用于根据查询特征自动选择最合适的大语言模型（LLM）来处理请求。

## 目录

- [模块结构](#模块结构)
- [模块间调用关系](#模块间调用关系)
- [数据流转](#数据流转)
- [核心类说明](#核心类说明)
- [代码示例](#代码示例)

---

## 模块结构

### 1. `cli` - 命令行接口模块

提供统一的命令行工具，支持训练、推理、聊天交互等功能。

**主要文件：**
- `router_main.py` - 主 CLI 入口点，支持子命令
- `router_train.py` - 训练命令处理
- `router_inference.py` - 推理命令处理
- `router_chat.py` - 聊天界面处理

**可用命令：**
```bash
llmrouter train --router knnrouter --config config.yaml    # 训练路由器
llmrouter infer --router knnrouter --config config.yaml    # 执行推理
llmrouter chat --router knnrouter --config config.yaml     # 启动聊天界面
llmrouter serve --config config.yaml                       # 启动 API 服务器
llmrouter list-routers                                     # 列出所有可用路由器
```

### 2. `data` - 数据处理模块

负责数据的加载、验证和格式处理。

**主要文件：**
- `data.py` - 数据格式定义和验证（支持标准格式和 GMTRouter 格式）
- `data_loader.py` - 数据加载器
- `data_generation.py` - 数据生成工具
- `generate_llm_embeddings.py` - 生成 LLM 嵌入
- `multimodal_generation.py` - 多模态数据生成
- `api_calling_evaluation.py` - API 调用评估数据

**支持的数据格式：**
- **标准格式**：查询-响应对格式
- **GMTRouter 格式**：包含嵌入和评分的 JSONL 格式

### 3. `models` - 路由模型模块

包含各种路由算法的实现，都继承自 `MetaRouter` 基类。

**主要路由器：**

| 路由器 | 描述 | 特点 |
|--------|------|------|
| `knnrouter` | K近邻路由器 | 基于查询嵌入相似度 |
| `mlprouter` | 多层感知机路由器 | 神经网络分类 |
| `svmrouter` | 支持向量机路由器 | 传统机器学习方法 |
| `elorouter` | Ensemble Learning 路由器 | 集成学习方法 |
| `gmtrouter` | 图匹配路由器 | 基于图神经网络 |
| `graphrouter` | 图路由器 | 图结构建模 |
| `causallm_router` | 因果 LLM 路由器 | 因果推理 |
| `automix` | 自动混合路由器 | 动态模型选择 |
| `knnmultiroundrouter` | 多轮 KNN 路由器 | 支持多轮对话 |
| `llmmultiroundrouter` | 多轮 LLM 路由器 | LLM 驱动的多轮路由 |

**基类：**
- `meta_router.py` - 所有路由器的基类
- `base_trainer.py` - 训练器基类

### 4. `evaluation` - 评估模块

提供批量评估功能和多种评估指标。

**主要文件：**
- `batch_evaluator.py` - 批量评估器，支持装饰器式指标注册
- `example.py` - 评估示例

**支持的评估指标：**
- `em` - 精确匹配
- `em_mc` - 多选题精确匹配
- `f1` - F1 分数
- `cem` - 包含精确匹配
- `cemf1` - 包含精确匹配 + F1 回退
- `bert_score` - BERT 分数
- `gsm8k` - 数学问题评估

### 5. `utils` - 工具模块

提供各种辅助功能。

**主要文件：**
- `api_calling.py` - API 调用工具（使用 LiteLLM）
- `embeddings.py` - 嵌入生成工具（Longformer）
- `model_loader.py` - 模型加载工具
- `data_processing.py` - 数据处理工具
- `data_loader.py` - 数据加载工具
- `prompting.py` - 提示词处理
- `router_helpers.py` - 路由器辅助函数
- `evaluation.py` - 评估指标工具
- `constants.py` - 常量定义

### 6. `serve` - 服务模块

提供 OpenAI 兼容的 API 服务器。

**主要文件：**
- `server.py` - API 服务器实现
- `config.py` - 服务配置

### 7. `prompts` - 提示词模块

包含各种任务的提示词模板。

### 8. `plugin_system.py` - 插件系统

支持动态发现和注册自定义路由器。

---

## 模块间调用关系

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI (命令行接口)                      │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │  train   │  infer   │   chat   │  serve   │   list   │  │
│  └────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘  │
└───────┼───────────┼──────────┼──────────┼──────────┼────────┘
        │           │          │          │          │
        ▼           ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Models (路由模型)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              MetaRouter (基类)                       │   │
│  │  ┌────────┬────────┬────────┬────────┬────────┐    │   │
│  │  │  KNN   │  MLP   │  SVM   │  ELA   │  GMT   │    │   │
│  │  │ Router │ Router │ Router │ Router │ Router │    │   │
│  │  └───┬────┴───┬────┴───┬────┴───┬────┴───┬────┘    │   │
│  │      │        │        │        │        │         │   │
│  │      ▼        ▼        ▼        ▼        ▼         │   │
│  │  ┌──────────────────────────────────────────┐      │   │
│  │  │         BaseTrainer (训练器基类)          │      │   │
│  │  └──────────────────────────────────────────┘      │   │
│  └─────────────────────────────────────────────────────┘   │
└───────┬────────────────────────────────────────────────────┘
        │
        ├───────────────────┬───────────────────┬───────────┐
        ▼                   ▼                   ▼           ▼
┌────────────────┐  ┌────────────────┐  ┌─────────┐  ┌──────────┐
│     Data       │  │    Utils       │  │  Serve  │  │Evaluation│
│  ┌──────────┐  │  │  ┌──────────┐  │  └─────────┘  └──────────┘
│  │DataLoader│  │  │  │api_calling│ │
│  │data.py   │  │  │  │embeddings│ │
│  │etc.      │  │  │  │model_load│ │
│  └──────────┘  │  │  │etc.      │ │
└────────────────┘  │  └──────────┘  │
                    └────────────────┘
```

### 调用关系说明

1. **CLI → Models**：命令行工具直接调用具体的路由器类
2. **Models → Data**：路由器通过 `DataLoader` 加载训练和测试数据
3. **Models → Utils**：路由器使用工具函数进行 API 调用、嵌入生成等
4. **Models → Evaluation**：路由器使用评估模块计算性能指标
5. **CLI → Serve**：CLI 启动 API 服务器，服务器内部使用路由器

---

## 数据流转

### 训练流程数据流

```
┌─────────────┐
│  配置文件    │ (YAML 配置)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│            DataLoader               │
│  ┌─────────────────────────────┐    │
│  │ 1. 加载查询数据 (query_data) │    │
│  │ 2. 加载路由数据 (routing_data) │  │
│  │ 3. 加载 LLM 数据 (llm_data)  │    │
│  │ 4. 加载嵌入数据 (embeddings) │    │
│  └─────────────────────────────┘    │
└───────┬─────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│        Router 初始化                │
│  - 加载配置                          │
│  - 准备训练数据                      │
│  - 初始化底层模型                    │
└───────┬─────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│        Trainer 训练                 │
│  - 前向传播                          │
│  - 计算损失                          │
│  - 反向传播                          │
│  - 参数更新                          │
└───────┬─────────────────────────────┘
        │
        ▼
┌─────────────┐
│  保存模型    │
└─────────────┘
```

### 推理流程数据流

```
┌─────────────┐
│  输入查询    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│        Router.route_single()        │
│                                     │
│  1. 生成查询嵌入                    │
│     ┌──────────────────────────┐   │
│     │  Utils.get_longformer    │   │
│     │  _embedding(query)       │   │
│     └──────────────────────────┘   │
│             │                      │
│             ▼                      │
│  2. 路由决策                        │
│     ┌──────────────────────────┐   │
│     │  根据嵌入选择最佳模型     │   │
│     │  (KNN/MLP/SVM等算法)     │   │
│     └──────────────────────────┘   │
└───────┬─────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│        API 调用                      │
│  ┌──────────────────────────┐       │
│  │  Utils.call_api()        │       │
│  │  - 获取 API 端点         │       │
│  │  - 轮询选择 API Key      │       │
│  │  - 调用 LLM 服务         │       │
│  └──────────────────────────┘       │
└───────┬─────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│        返回结果                      │
│  - 选中的模型名称                    │
│  - LLM 响应内容                     │
│  - Token 使用统计                   │
└─────────────────────────────────────┘
```

### 评估流程数据流

```
┌─────────────────────────────────────┐
│        批量推理结果                  │
│  - 预测结果                         │
│  - 真实标签                         │
└───────┬─────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│    Evaluation.evaluate_batch()      │
│                                     │
│  1. 选择评估指标                    │
│     (em/f1/bert_score/gsm8k等)      │
│                                     │
│  2. 计算每个样本的分数              │
│     ┌──────────────────────────┐   │
│     │  evaluation_metric(name) │   │
│     │  → 计算预测与标签的匹配度│   │
│     └──────────────────────────┘   │
│                                     │
│  3. 汇总统计信息                    │
└───────┬─────────────────────────────┘
        │
        ▼
┌─────────────┐
│  评估报告    │
└─────────────┘
```

---

## 核心类说明

### 1. MetaRouter (基类)

**位置**：`llmrouter/models/meta_router.py`

**描述**：所有路由器的抽象基类，定义了统一的路由接口。

**核心方法**：
```python
class MetaRouter(nn.Module, ABC):
    @abstractmethod
    def route_single(self, batch) -> Dict[str, Any]:
        """路由单个查询"""
        pass

    @abstractmethod
    def route_batch(self, batch) -> List[Dict[str, Any]]:
        """批量路由查询"""
        pass

    def forward(self, batch):
        """PyTorch 前向传播，委托给 route_batch"""
        return self.route_batch(batch)

    def save_router(self, path: str):
        """保存路由器状态"""

    def load_router(self, path: str):
        """加载路由器状态"""
```

**初始化参数**：
- `model` (nn.Module)：底层 PyTorch 模型
- `yaml_path` (str)：配置文件路径（可选）
- `resources`：可选的共享资源

---

### 2. KNNRouter (K近邻路由器)

**位置**：`llmrouter/models/knnrouter/router.py`

**描述**：使用 K近邻算法根据查询嵌入相似度选择模型。

**工作原理**：
1. 训练时：为每个查询找到最佳模型，存储查询嵌入和模型标签
2. 推理时：计算查询嵌入，使用 KNN 找到最相似的训练样本，选择对应模型

**配置示例** (YAML)：
```yaml
hparam:
  n_neighbors: 5        # K值
  weights: "uniform"    # 权重函数
  algorithm: "auto"     # 算法类型
  metric: "cosine"      # 距离度量
  n_jobs: -1            # 并行任务数
```

---

### 3. BaseTrainer (训练器基类)

**位置**：`llmrouter/models/base_trainer.py`

**描述**：所有训练器的基类，提供训练循环的基础功能。

**核心方法**：
```python
class BaseTrainer:
    def __init__(self, router, optimizer=None, device="cpu"):
        pass

    def train(self):
        """执行训练"""
        pass

    def evaluate(self):
        """执行评估"""
        pass

    def save_model(self, path):
        """保存模型"""

    def load_model(self, path):
        """加载模型"""
```

---

### 4. DataLoader (数据加载器)

**位置**：`llmrouter/data/data_loader.py`

**描述**：负责加载和预处理各种格式的训练数据。

**功能**：
- 加载查询数据
- 加载路由数据
- 加载 LLM 候选模型信息
- 加载嵌入数据

---

### 5. PluginRegistry (插件注册表)

**位置**：`llmrouter/plugin_system.py`

**描述**：支持动态发现和注册自定义路由器。

**使用方法**：
```python
from llmrouter.plugin_system import discover_and_register_plugins

# 自动发现插件
registry = discover_and_register_plugins(verbose=True)

# 获取发现的路由器
router_names = registry.get_router_names()
```

---

### 6. call_api (API 调用工具)

**位置**：`llmrouter/utils/api_calling.py`

**描述**：使用 LiteLLM 进行 API 调用，支持负载均衡。

**功能**：
- 支持多个 API Key 轮询
- 支持批处理请求
- 自动 token 统计
- 错误处理和重试

**使用示例**：
```python
from llmrouter.utils import call_api

request = {
    "api_endpoint": "https://api.example.com/v1",
    "query": "What is AI?",
    "model_name": "gpt-4",
    "api_name": "gpt-4"
}

result = call_api(request)
```

---

### 7. get_longformer_embedding (嵌入生成)

**位置**：`llmrouter/utils/embeddings.py`

**描述**：使用 Longformer 模型生成文本嵌入。

**特点**：
- 支持长文本（最多 4096 tokens）
- 自动设备选择（GPU/MPS/CPU）
- 均值池化生成句子嵌入

**使用示例**：
```python
from llmrouter.utils import get_longformer_embedding

embedding = get_longformer_embedding("Your text here")
```

---

### 8. evaluate_batch (批量评估)

**位置**：`llmrouter/evaluation/batch_evaluator.py`

**描述**：批量评估预测结果，支持装饰器式指标注册。

**支持的指标**：`em`, `f1`, `cem`, `bert_score`, `gsm8k` 等

**使用示例**：
```python
from llmrouter.evaluation import evaluate_batch

data = [
    {'prediction': 'hello', 'ground_truth': 'hello', 'metric': 'em'},
    {'prediction': 'world', 'ground_truth': 'word', 'metric': 'f1'}
]

results = evaluate_batch(data)
```

**自定义指标注册**：
```python
from llmrouter.evaluation import evaluation_metric

@evaluation_metric('custom_metric')
def my_eval_func(prediction, ground_truth, **kwargs):
    # 自定义评估逻辑
    return 1.0 if prediction == ground_truth else 0.0
```

---

## 代码示例

### 示例 1：训练 KNN 路由器

```python
from llmrouter.cli.router_train import train_router, get_device

# 获取设备
device = get_device(None)  # 自动检测

# 训练路由器
train_router(
    router_name="knnrouter",
    config_path="configs/model_config_train/knnrouter.yaml",
    device=device,
    verbose=True
)
```

**命令行方式**：
```bash
llmrouter train --router knnrouter --config configs/model_config_train/knnrouter.yaml
```

---

### 示例 2：使用训练好的路由器进行推理

```python
from llmrouter.models.knnrouter import KNNRouter

# 初始化路由器
router = KNNRouter(yaml_path="configs/model_config_test/knnrouter.yaml")

# 路由单个查询
query = {"query": "什么是机器学习？"}
result = router.route_single(query)
print(f"Selected model: {result['model_name']}")

# 批量路由
queries = [
    {"query": "写一个Python函数"},
    {"query": "解释量子计算"}
]
results = router.route_batch(queries, task_name="commonsense_qa")

for res in results:
    print(f"Query: {res['query']}")
    print(f"Model: {res['model_name']}")
    print(f"Response: {res['response']}")
    print("-" * 50)
```

**命令行方式**：
```bash
# 单次推理
llmrouter infer --router knnrouter \
  --config config.yaml \
  --query "什么是机器学习？"

# 批量推理
llmrouter infer --router knnrouter \
  --config config.yaml \
  --input queries.jsonl \
  --output results.json
```

---

### 示例 3：使用嵌入生成工具

```python
from llmrouter.utils import get_longformer_embedding

# 生成单个文本的嵌入
text = "This is an example text."
embedding = get_longformer_embedding(text)
print(f"Embedding shape: {embedding.shape}")  # torch.Size([768])

# 批量生成嵌入
texts = ["First text.", "Second text.", "Third text."]
embeddings = get_longformer_embedding(texts)
print(f"Batch embeddings shape: {embeddings.shape}")  # torch.Size([3, 768])
```

---

### 示例 4：自定义路由器

```python
import torch.nn as nn
from llmrouter.models.meta_router import MetaRouter

class MyCustomRouter(MetaRouter):
    def __init__(self, yaml_path: str = None):
        # 创建底层模型
        dummy_model = nn.Linear(768, 5)  # 768维输入，5个模型选择
        super().__init__(model=dummy_model, yaml_path=yaml_path)

    def route_single(self, batch):
        """路由单个查询"""
        # 实现单查询路由逻辑
        query_embedding = get_longformer_embedding(batch["query"])
        with torch.no_grad():
            scores = self.model(query_embedding)
            model_idx = torch.argmax(scores).item()

        # 获取模型名称（需要从配置中获取）
        model_names = list(self.llm_data.keys())
        batch["model_name"] = model_names[model_idx]
        return batch

    def route_batch(self, batch):
        """批量路由"""
        results = []
        for item in batch:
            result = self.route_single(item.copy())
            results.append(result)
        return results
```

**将自定义路由器保存为插件**：
```
custom_routers/
└── my_custom_router/
    ├── __init__.py
    └── router.py  # 包含 MyCustomRouter 类
```

系统会自动发现并注册该路由器。

---

### 示例 5：使用评估模块

```python
from llmrouter.evaluation import evaluate_batch

# 准备评估数据
eval_data = [
    {
        "prediction": "Paris",
        "ground_truth": "Paris",
        "metric": "em"
    },
    {
        "prediction": "The capital of France is Paris",
        "ground_truth": "Paris",
        "metric": "f1"
    }
]

# 执行评估
results = evaluate_batch(eval_data)

# 查看结果
for res in results:
    print(f"Prediction: {res['prediction']}")
    print(f"Ground Truth: {res['ground_truth']}")
    print(f"Score: {res['score']}")
    print("-" * 40)
```

---

### 示例 6：注册自定义评估指标

```python
from llmrouter.evaluation import evaluation_metric, evaluate_batch

# 注册自定义指标
@evaluation_metric('exact_match_len')
def exact_match_len_score(prediction, ground_truth, min_len=0, **kwargs):
    """如果预测和真实匹配且长度超过阈值则返回 1"""
    if prediction == ground_truth and len(prediction) >= min_len:
        return 1.0
    return 0.0

# 使用自定义指标
data = [{
    "prediction": "hello world",
    "ground_truth": "hello world",
    "metric": "exact_match_len",
    "min_len": 5
}]

result = evaluate_batch(data)
print(f"Score: {result[0]['score']}")  # 输出: 1.0
```

---

### 示例 7：启动 OpenAI 兼容的 API 服务器

```python
from openclaw_router import create_app, OpenClawConfig

# 创建配置
config = OpenClawConfig()
config.host = "0.0.0.0"
config.port = 8000
config.router.strategy = "llmrouter"
config.router.llmrouter_name = "knnrouter"
config.router.llmrouter_config = "configs/knnrouter.yaml"

# 创建并运行应用
app = create_app(config=config)
from openclaw_router import run_server
run_server(app, host=config.host, port=config.port)
```

**命令行方式**：
```bash
llmrouter serve --config configs/openclaw_example.yaml
```

---

### 示例 8：使用 Gradio 聊天界面

```python
import gradio as gr
from llmrouter.cli.router_chat import load_router, predict

# 加载路由器
router = load_router("knnrouter", "config.yaml")

# 创建界面
interface = gr.ChatInterface(
    lambda msg, hist: predict(msg, hist, router, "knnrouter", 0.7, "current_only", 3),
    title="LLMRouter Chat",
    description="使用 KNN 路由器的智能对话"
)

interface.launch()
```

**命令行方式**：
```bash
llmrouter chat --router knnrouter --config config.yaml --port 8001
```

---

## 总结

LLMRouter 提供了一个完整的智能模型路由解决方案，具有以下特点：

1. **模块化设计**：清晰的模块划分，易于扩展和维护
2. **统一接口**：所有路由器继承 `MetaRouter`，提供一致的 API
3. **灵活配置**：通过 YAML 配置文件管理所有参数
4. **插件系统**：支持动态发现和注册自定义路由器
5. **完整工具链**：从数据处理、训练、推理到评估的全流程支持
6. **多种部署方式**：CLI、API 服务器、聊天界面等

通过合理使用各个模块，可以快速构建和部署自定义的模型路由系统。
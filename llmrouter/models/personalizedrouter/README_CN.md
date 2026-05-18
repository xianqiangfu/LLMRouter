# 个性化路由器（基于 GNN 的个性化路由器）

## 概述

**个性化路由器（Personalized Router）**使用图神经网络（GNN）为不同用户做出个性化的路由决策。它通过将用户特征集成到图结构中扩展了图路由器，使模型能够学习特定用户的选择偏好。

## 论文参考

此路由器实现了 **PersonalizedRouter** 方法：

- **[PersonalizedRouter: Personalized LLM Routing via Graph-based User Preference Modeling](https://arxiv.org/abs/2511.16883)**
  - Dai, Z., 等（2025）。arXiv:2511.16883。
  - 构建包含任务、查询、用户和 LLM 节点的异构图以实现个性化路由。
  - 通过个性化消息传递学习用户特定的路由模式。

## 重要提示

**PersonalizedRouter 使用专用的数据集和数据格式，与其他路由器不同。**

- **数据集来源**：PersonaRoute-Bench
- **下载链接**：
  ```text
  https://huggingface.co/datasets/ulab-ai/PersonaRoute-Bench
  ```
- **可用文件**：数据集提供单文件 CSV 和训练/验证/测试划分（例如 `router_user_data.csv`、`router_user_train_data.csv`、`router_user_val_data.csv`、`router_user_test_data.csv`）。

## 数据格式

PersonaRoute-Bench 以 **CSV** 格式提供。

### 列说明

| 列名 | 描述 |
|--------|-------------|
| `user_id` | 用于个性化的用户标识符。 |
| `performance_preference` | 用户在性能和成本之间的偏好权重。 |
| `task_id` | 任务标识符。 |
| `query` | 查询文本。 |
| `query_embedding` | 查询嵌入向量。 |
| `effect` | 查询-LLM 对的性能效应/得分。 |
| `cost` | 查询-LLM 对的成本信号。 |
| `ground_truth` | 真实结果或标签。 |
| `metric` | 该行的指标名称或类别。 |
| `llm` | 该行的 LLM 名称。 |
| `task_description` | 任务描述文本。 |
| `task_description_embedding` | 任务描述嵌入向量。 |
| `response` | 模型响应文本。 |
| `reward` | 奖励得分。 |
| `best_llm` | 该查询的最佳 LLM 指示器。 |

## 数据准备

### 步骤 1：下载数据集

使用以下方法之一：

```bash
# 使用 Hugging Face CLI（推荐）
huggingface-cli download ulab-ai/PersonaRoute-Bench --repo-type dataset --local-dir data/personaroute_bench
```

```python
# 使用 datasets 库
from datasets import load_dataset
ds = load_dataset("ulab-ai/PersonaRoute-Bench")
```

### 步骤 2：选择 CSV 文件

您可以使用：

- 单个 CSV 文件（例如 `router_user_data.csv`）
- 或训练/验证/测试划分（例如 `router_user_train_data.csv`、`router_user_val_data.csv`、`router_user_test_data.csv`）

数据集文件列表可在 Hugging Face 数据集页面上找到。

### 步骤 3：将配置指向数据

将 YAML 配置中的 `data_path` 字段设置为下载的 CSV（请参阅本 README 中的示例）。

## 工作原理

### 图结构

```
                      用户节点
                            |
                            |
        查询节点 ─── 边 ──→ LLM 节点
                            |
                            |
                      任务节点

              GNN 消息传递
                    ↓
         个性化预测
```

**节点类型：**
- **查询节点**：每个查询是一个具有嵌入特征的节点
- **LLM 节点**：每个 LLM 是一个具有学习/提供嵌入的节点
- **用户节点**：每个用户是一个节点，其嵌入代表用户的偏好特征
- **任务节点**：每个任务具有一个嵌入
- **边**：将查询连接到 LLM，按得分加权

### 路由机制

PersonalizedRouter 将 LLM 路由建模为一个异构图学习问题，使模型选择适应个人用户偏好。
- 构建包含用户、查询、任务和 LLM 的全局异构图
- 直接从交互数据学习潜在的用户偏好嵌入
- 使用异构 GNN 消息传递联合编码用户、任务和 LLM 特征
- 对于每个（用户，查询）对，估计候选 LLM 的个性化效用得分并路由到最合适的模型

这种表述使相同的查询可以在不同用户之间进行不同的路由，并支持跨用户和任务的高效泛化。

### 训练策略

使用**边掩码**进行个性化训练：
- 为每个用户掩码一部分边（例如 30%）
- 训练 GNN 以预测掩码边上的性能
- 在具有不同掩码边的验证集上进行评估
- 同一个查询可能在不同用户中有不同的最佳 LLM

## 配置参数

### 训练超参数（配置中的 `hparam`）

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `embedding_dim` | int | `64` | GNN 的隐藏层维度。控制模型容量。范围：32-256。 |
| `user_num` | int | `1000` | 用于个性化的用户数量。每个用户获得一个唯一的节点。 |
| `num_task` | int | `4` | 多任务学习的任务数量。 |
| `learning_rate` | float | `0.001` | AdamW 优化器的学习率。范围：0.0001-0.01。 |
| `weight_decay` | float | `0.0001` | L2 正则化权重衰减。防止过拟合。 |
| `train_epoch` | int | `100` | 训练周期数。对于更大的图增加。 |
| `batch_size` | int | `4` | 每个梯度步的掩码样本数。 |
| `train_mask_rate` | float | `0.3` | 训练期间掩码的边的比例（0.0-1.0）。 |
| `split_ratio` | list | `[0.6, 0.2, 0.2]` | 训练/验证/测试划分的比例。 |
| `llm_family` | list | `[]` | 用于附加边的 LLM 系列列表（例如 ["gpt", "claude"]）。 |
| `random_state` | int | `42` | 用于可重复性的随机种子。 |

### 数据路径

| 参数 | 描述 |
|-----------|-------------|
| `routing_data_path` | 路由数据 CSV 路径或包含单个 CSV 的目录。 |
| `routing_data_train` | 训练路由数据 CSV。 |
| `routing_data_val` | 验证路由数据 CSV。 |
| `routing_data_test` | 测试路由数据 CSV。 |
| `llm_data` | LLM 元数据（JSON）。 |
| `llm_embedding_data` | 预计算的 LLM 嵌入（pickle / `.pkl`）。 |

### 模型路径

| 参数 | 用途 |
|-----------|---------|
| `save_model_path` | 保存训练好的 GNN 模型的位置 |
| `load_model_path` | 加载用于推理的模型 |
| `ini_model_path` | 初始模型权重（可选） |

## CLI 使用

个性化路由器可以通过 `llmrouter` 命令行界面使用：

### 训练

```bash
# 训练个性化路由器（推荐使用 GPU）
llmrouter train --router personalizedrouter --config configs/model_config_train/personalizedrouter.yaml --device cuda

# 使用安静模式训练
llmrouter train --router personalizedrouter --config configs/model_config_train/personalizedrouter.yaml --device cuda --quiet
```

### 推理

```bash
# 使用 user_id 路由单个查询
llmrouter infer --router personalizedrouter --config configs/model_config_test/personalizedrouter.yaml \
    --query "解释量子力学"

# 从文件路由查询（每个查询中包含 user_id）
llmrouter infer --router personalizedrouter --config configs/model_config_test/personalizedrouter.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
llmrouter infer --router personalizedrouter --config configs/model_config_test/personalizedrouter.yaml \
    --query "什么是机器学习？" --route-only
```

### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router personalizedrouter --config configs/model_config_test/personalizedrouter.yaml

# 使用自定义端口启动
llmrouter chat --router personalizedrouter --config configs/model_config_test/personalizedrouter.yaml --port 8080

# 创建可公开分享的链接
llmrouter chat --router personalizedrouter --config configs/model_config_test/personalizedrouter.yaml --share
```

---

## 使用示例

### 训练

```python
from llmrouter.models import PersonalizedRouter
from llmrouter.models.personalizedrouter.trainer import PersonalizedRouterTrainer

router = PersonalizedRouter(yaml_path="configs/model_config_train/personalizedrouter.yaml")
trainer = PersonalizedRouterTrainer(router=router, device="cuda")
trainer.train()
```

### 推理

```python
from llmrouter.models import PersonalizedRouter

router = PersonalizedRouter(yaml_path="configs/model_config_test/personalizedrouter.yaml")

# 带有用户个性化的单个查询
query = {"query": "解释量子力学", "user_id": 0}
result = router.route_single(query)
print(f"为用户 0 选择：{result['model_name']}")

# 不同用户可能获得不同的推荐
query2 = {"query": "解释量子力学", "user_id": 1}
result2 = router.route_single(query2)
print(f"为用户 1 选择：{result2['model_name']}")
```

### 批量推理

```python
from llmrouter.models import PersonalizedRouter

router = PersonalizedRouter(yaml_path="configs/model_config_test/personalizedrouter.yaml")

# 不同用户的批量查询
batch = [
    {"query": "法国的首都是什么？", "user_id": 0},
    {"query": "谁写了罗密欧与朱丽叶？", "user_id": 1},
    {"query": "光合作用是如何工作的？", "user_id": 2},
]

results = router.route_batch(batch=batch)
for result in results:
    print(f"用户 {result.get('user_id')}: {result['query'][:30]}... -> {result['model_name']}")
```

## YAML 配置示例

```yaml
data_path:
  routing_data_path: 'data/personaroute_bench/router_user_data_v1.csv'
  routing_data_train: 'data/personaroute_bench/router_user_train_data_v1.csv'
  routing_data_val: 'data/personaroute_bench/router_user_val_data_v1.csv'
  routing_data_test: 'data/personaroute_bench/router_user_test_data_v1.csv'
  llm_data: 'data/personaroute_bench/LLM_Descriptions_large.json'
  llm_embedding_data: 'data/personaroute_bench/llm_description_embedding_large.pkl'

model_path:
  save_model_path: 'saved_models/personalizedrouter/personalizedrouter.pt'
  load_model_path: 'saved_models/personalizedrouter/personalizedrouter.pt'

hparam:
  embedding_dim: 64
  edge_dim: 1
  user_num: 1000
  num_task: 4
  learning_rate: 0.001
  weight_decay: 0.0001
  train_epoch: 100
  batch_size: 4
  train_mask_rate: 0.3
  split_ratio: [0.6, 0.2, 0.2]
  llm_family: []
  random_state: 42

metric:
  weights:
    performance: 1
```

## 优势

- ✅ **个性化**：为不同用户学习不同的路由策略
- ✅ **用户特征**：将用户特定信息纳入路由决策
- ✅ **多任务支持**：支持任务嵌入的多任务学习
- ✅ **关系学习**：按用户捕获复杂的查询-模型关系
- ✅ **图结构**：利用网络效应和传递性
- ✅ **灵活性**：可以结合额外的节点/边特征

## 局限性

- ❌ **计算成本**：GNN 训练比简单方法更慢
- ❌ **冷启动**：新用户需要添加到图中
- ❌ **内存使用**：需要存储所有用户的嵌入
- ❌ **超参数敏感性**：许多架构选择

## 何时使用个性化路由器

**良好使用场景：**
- 有多个具有不同偏好的用户
- 希望学习用户特定的路由模式
- 拥有用户交互历史数据
- 需要多任务学习支持
- 查询-模型关系因用户而异

**替代方案：**
- 单用户场景 → 使用图路由器
- 简单关系 → 使用 MLP/SVM 路由器
- 小数据集 → 使用 KNN 路由器
- 需要快速训练 → 使用 ELO 路由器

## 相关路由器

- **图路由器**：没有个性化的基础 GNN 路由器
- **RouterDC**：也使用结构化学习，但使用对比损失
- **MF 路由器**：学习潜在空间但没有图结构
- **MLP 路由器**：标准神经网络，没有图

---

如有问题或建议，请参阅主要的 LLMRouter 文档或在 GitHub 上提出 issue。

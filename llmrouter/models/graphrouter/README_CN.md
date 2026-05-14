# 图神经路由器（Graph Router）

## 概述

**图神经路由器** 使用图神经网络（GNN）通过将查询和 LLM 建模为异构图中的节点来进行路由决策。它通过图结构传播信息来学习路由模式，捕获查询、LLM 及其性能特征之间的复杂关系。

## 论文参考

本路由器实现了 **GraphRouter** 方法：

- **[GraphRouter: A Graph-based Router for LLM Selections](https://arxiv.org/abs/2410.03834)**
  - (2024). arXiv:2410.03834.
  - 构建包含任务、查询和 LLM 节点的异构图进行路由。

- **GNN 基础**：Kipf, T. N., & Welling, M. (2017). "Semi-supervised classification with graph convolutional networks." ICLR.
- **应用**：将 LLM 路由视为二分查询-模型图中的链路预测问题。

## 工作原理

### 图结构

```
查询节点 ─── 边(性能分数) ──→ LLM 节点

        GNN 消息传递
              ↓
           预测结果
```

**节点类型：**
- **查询节点**：每个查询是一个节点，具有 Longformer 嵌入特征
- **LLM 节点**：每个 LLM 是一个节点，具有学习/提供的嵌入
- **边**：将每个查询连接到所有 LLM，按性能分数加权

### 路由机制

1. **图构建**：
   - 创建二分图：查询在一侧，LLM 在另一侧
   - 从每个查询添加边到所有 LLM
   - 边特征：性能分数（新查询为 0）

2. **GNN 前向传播**：
   - 聚合来自相邻节点的信息
   - 使用消息传递更新节点表示
   - 应用图注意力或卷积层

3. **预测**：
   - 对每个查询-LLM 边预测适用性分数
   - 选择预测分数最高的 LLM

### 训练策略

使用**边掩码**进行训练：
- 掩码部分边（例如 30%）
- 训练 GNN 预测掩码边的性能
- 在具有不同掩码边的验证集上进行评估

## 模型结构

### 核心组件

#### 1. FeatureAlign（特征对齐模块）
```python
FeatureAlign(query_feature_dim, llm_feature_dim, common_dim)
```
- 将查询和 LLM 特征映射到同一维度
- 使用线性变换对齐特征空间

#### 2. EncoderDecoderNet（编解码器网络）
```python
EncoderDecoderNet(query_feature_dim, llm_feature_dim, hidden_features, in_edges=1)
```
- 双层 GNN 编码器
- 使用 GeneralConv 进行消息传递
- 边特征 MLP 用于边权重变换
- 预测查询-LLM 边的适用性分数

#### 3. FormData（数据格式化）
```python
FormData(device)
```
- 将原始数据转换为 PyG Data 对象
- 构建边索引、节点特征和掩码

#### 4. GNNPredictor（GNN 预测器）
```python
GNNPredictor(query_feature_dim, llm_feature_dim, hidden_features_size,
             in_edges_size, config, device)
```
- 封装模型训练、验证和预测逻辑
- 使用 AdamW 优化器和 BCE 损失
- 支持边掩码训练

### 消息传递机制

```
1. 特征对齐：
   query_features → Linear → hidden_dim
   llm_features → Linear → hidden_dim
   concat → x_ini

2. GNN 传播：
   x1 = GNN_Conv1(x_ini, edge_index, edge_attr)
   x1 = BatchNorm(LeakyReLU(x1))

   x2 = GNN_Conv2(x1, edge_index, edge_attr)
   x2 = BatchNorm(x2)

3. 边预测：
   edge_score = sigmoid(dot(x_ini[src], x2[dst]))
```

## 配置参数

### 训练超参数（配置中的 `hparam`）

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `hidden_dim` | int | `64` | GNN 隐藏层维度，控制模型容量。范围：32-256。 |
| `learning_rate` | float | `0.001` | AdamW 优化器的学习率。范围：0.0001-0.01。 |
| `weight_decay` | float | `0.0001` | L2 正则化权重衰减，防止过拟合。 |
| `train_epoch` | int | `100` | 训练轮数，较大图可增加此值。 |
| `batch_size` | int | `4` | 每个梯度步的掩码样本数。 |
| `train_mask_rate` | float | `0.3` | 训练时掩码边的比例（0.0-1.0）。 |
| `val_split_ratio` | float | `0.2` | 用于验证的训练数据比例。 |
| `random_state` | int | `42` | 用于可重复性的随机种子。 |

### 数据路径

| 参数 | 描述 |
|-----------|-------------|
| `routing_data_train` | 训练查询-LLM 性能数据（JSONL 格式） |
| `query_embedding_data` | 预计算的 Longformer 查询嵌入（PyTorch tensor） |
| `llm_data` | LLM 信息，可选包含嵌入（JSON 格式） |

### 模型路径

| 参数 | 用途 |
|-----------|---------|
| `save_model_path` | 保存训练好的 GNN 模型位置 |
| `load_model_path` | 加载用于推理的模型位置 |
| `ini_model_path` | 初始模型权重（可选） |

## 使用示例

### 命令行使用

图神经路由器可以通过 `llmrouter` 命令行界面使用：

#### 训练

```bash
# 训练图路由器（推荐使用 GPU）
llmrouter train --router graphrouter --config configs/model_config_train/graphrouter.yaml --device cuda

# 使用安静模式训练
llmrouter train --router graphrouter --config configs/model_config_train/graphrouter.yaml --device cuda --quiet
```

#### 推理

```bash
# 路由单个查询
llmrouter infer --router graphrouter --config configs/model_config_test/graphrouter.yaml \
    --query "解释量子力学"

# 从文件路由查询
llmrouter infer --router graphrouter --config configs/model_config_test/graphrouter.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
llmrouter infer --router graphrouter --config configs/model_config_test/graphrouter.yaml \
    --query "什么是机器学习？" --route-only
```

#### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router graphrouter --config configs/model_config_test/graphrouter.yaml

# 使用自定义端口启动
llmrouter chat --router graphrouter --config configs/model_config_test/graphrouter.yaml --port 8080

# 创建可公开分享的链接
llmrouter chat --router graphrouter --config configs/model_config_test/graphrouter.yaml --share
```

### Python API 使用

#### 训练

```python
from llmrouter.models.graphrouter import GraphRouter
from llmrouter.models.graphrouter.trainer import GraphTrainer

# 创建路由器实例
router = GraphRouter(yaml_path="configs/model_config_train/graphrouter.yaml")

# 创建训练器
trainer = GraphTrainer(router=router, device="cuda")

# 开始训练
best_result = trainer.train()
print(f"最佳验证结果: {best_result:.4f}")
```

#### 推理

```python
from llmrouter.models.graphrouter import GraphRouter

# 创建路由器实例
router = GraphRouter(yaml_path="configs/model_config_test/graphrouter.yaml")

# 单查询路由
query = {"query": "解释量子力学"}
result = router.route_single(query)
print(f"选择的模型: {result['model_name']}")

# 批量路由
queries = [
    {"query": "什么是机器学习？"},
    {"query": "Python 和 Java 有什么区别？"}
]
results = router.route_batch(batch=queries)
for res in results:
    print(f"查询: {res['query']}, 模型: {res['model_name']}")
```

### YAML 配置示例

```yaml
# 配置文件路径：configs/model_config_train/graphrouter.yaml

data_path:
  # 训练数据路径
  routing_data_train: 'data/example_data/routing_data/default_routing_train_data.jsonl'
  # 查询嵌入路径（预计算的 Longformer 嵌入）
  query_embedding_data: 'data/example_data/routing_data/query_embeddings_longformer.pt'
  # LLM 信息路径
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

model_path:
  # 保存训练模型的路径
  save_model_path: 'saved_models/graphrouter/graphrouter.pt'
  # 加载模型的路径（推理时使用）
  load_model_path: 'saved_models/graphrouter/graphrouter.pt'
  # 初始模型权重（可选）
  ini_model_path: 'models/gnn_model_init.pt'

# 超参数配置
hparam:
  # 隐藏层维度
  hidden_dim: 64
  # 学习率
  learning_rate: 0.001
  # 权重衰减
  weight_decay: 0.0001
  # 训练轮数
  train_epoch: 100
  # 批次大小
  batch_size: 4
  # 训练边掩码比例
  train_mask_rate: 0.3
  # 验证集比例
  val_split_ratio: 0.2

# 评估指标权重
metric:
  weights:
    performance: 1
```

### LLM 数据格式

`llm_data` JSON 文件示例：

```json
{
  "gpt-3.5-turbo": {
    "model": "gpt-3.5-turbo",
    "api_endpoint": "https://api.openai.com/v1/chat/completions",
    "service": "openai",
    "embedding": [0.1, 0.2, 0.3, ...]
  },
  "claude-3-opus": {
    "model": "claude-3-opus-20240229",
    "api_endpoint": "https://api.anthropic.com/v1/messages",
    "service": "anthropic",
    "embedding": [0.4, 0.5, 0.6, ...]
  }
}
```

### 训练数据格式

`routing_data_train` JSONL 文件示例：

```json
{"query": "什么是量子力学？", "model_name": "gpt-3.5-turbo", "performance": 0.85, "embedding_id": 0}
{"query": "什么是量子力学？", "model_name": "claude-3-opus", "performance": 0.92, "embedding_id": 0}
{"query": "解释机器学习", "model_name": "gpt-3.5-turbo", "performance": 0.78, "embedding_id": 1}
{"query": "解释机器学习", "model_name": "claude-3-opus", "performance": 0.88, "embedding_id": 1}
```

## 适用场景

### 适用场景

- **具有丰富关系结构的大型数据集**
  - 当查询-模型关系表现出网络效应时
  - 当可以利用传递性信息时

- **具有 LLM 嵌入或除性能外的特征**
  - LLM 有预计算的特征向量
  - 需要利用模型的语义信息

- **需要建模高阶交互**
  - 查询和模型之间存在复杂关系
  - 需要考虑全局图结构

### 不适用场景

- **关系简单**
  - 查询-模型关系较为线性
  - 建议：使用 MLP/SVM Router

- **数据集较小**
  - 训练数据不足
  - 建议：使用 KNN Router

- **需要快速训练**
  - 对训练时间有严格要求
  - 建议：使用 ELO Router

## 优势与局限

### 优势

- ✅ **关系学习**：捕获复杂的查询-模型关系
- ✅ **图结构**：利用网络效应和传递性
- ✅ **灵活性**：可纳入额外的节点/边特征
- ✅ **半监督**：可以在部分观察的数据上进行预测
- ✅ **可扩展性**：支持添加新的节点类型和特征

### 局限

- ❌ **计算成本**：GNN 训练比简单方法更慢
- ❌ **图构建**：需要构建完整的二分图
- ❌ **冷启动**：新查询/模型需要重构图
- ❌ **超参数敏感**：许多架构选择需要调优
- ❌ **内存消耗**：大规模图可能占用较多内存

## 相关路由器

- **RouterDC**：也使用结构化学习，但使用对比损失
- **MF Router**：学习潜在空间，但没有图结构
- **MLP Router**：标准神经网络，无图结构
- **KNN Router**：基于邻居的简单路由

## 文件结构

```
graphrouter/
├── __init__.py          # 模块初始化
├── graph_nn.py          # GNN 模型定义
│   ├── FeatureAlign     # 特征对齐模块
│   ├── EncoderDecoderNet # 编解码器网络
│   ├── FormData        # 数据格式化
│   └── GNNPredictor    # GNN 预测器
├── router.py            # GraphRouter 主类
│   ├── _prepare_training_data() # 准备训练数据
│   ├── _prepare_llm_embeddings() # 准备 LLM 嵌入
│   ├── _build_graph_data() # 构建图数据
│   ├── route_single()  # 单查询路由
│   └── route_batch()   # 批量路由
├── trainer.py           # 训练器
│   └── GraphTrainer    # 图路由训练器
├── README.md            # 英文文档
└── README_CN.md         # 中文文档（本文件）
```

## 参考文献

1. [GraphRouter: A Graph-based Router for LLM Selections](https://arxiv.org/abs/2410.03834)
2. Kipf, T. N., & Welling, M. (2017). "Semi-supervised classification with graph convolutional networks." ICLR.
3. PyTorch Geometric: https://pyg.org/

如有问题或建议，请参考 LLMRouter 主文档或在 GitHub 上提交 Issue。
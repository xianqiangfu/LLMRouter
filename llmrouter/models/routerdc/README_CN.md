# RouterDC (双重对比学习路由器)

## 概述

**RouterDC** 是一种复杂的路由方法，使用双重对比学习来做出路由决策。它结合了预训练编码器（mDeBERTa）和可学习的 LLM 嵌入，并采用三种互补的对比学习目标来学习有效的路由表示。

## 论文参考

此路由器实现了以下论文中的 **RouterDC** 方法：

- **[RouterDC: Query-Based Router by Dual Contrastive Learning for Assembling Large Language Models](https://arxiv.org/abs/2409.19886)**
  - Chen, S., Jiang, W., Lin, B., Kwok, J., & Zhang, Y. (2024). arXiv:2409.19886. 发表于 NeurIPS 2024。
  - 提出了用于查询到 LLM 路由的双重对比学习。

该路由器使用三种类型的对比学习：
1. **样本-LLM 对比损失**：学习查询到模型的亲和度
2. **样本-样本 对比损失**：将相似的查询分组在一起（任务级别）
3. **聚类对比损失**：利用查询聚类以获得更好的表示

## 工作原理

### 架构

```
查询 → mDeBERTa 编码器 → 隐藏状态 → 相似度计算 → LLM 选择
                                            ↓
                                   可学习的 LLM 嵌入
```

### 路由机制

1. **查询编码**：使用 mDeBERTa（多语言 DeBERTa v3）对输入查询进行编码
2. **LLM 嵌入**：每个 LLM 都有一个可学习的嵌入向量
3. **相似度计算**：计算查询编码和 LLM 嵌入之间的余弦相似度或内积
4. **评分**：应用温度缩放的 softmax 获得路由分数
5. **选择**：选择得分最高的 LLM

### 训练过程

模型使用三种对比学习目标进行训练：

#### 1. 样本-LLM 对比损失
- 将查询嵌入拉向表现良好的 LLM 的嵌入
- 将查询嵌入推离表现不佳的 LLM 的嵌入
- 使用前 k 个 LLM 作为正样本，后 k 个作为负样本

#### 2. 样本-样本 对比损失（任务级别）
- 将来自同一任务的查询分组在一起
- 将来自不同任务的查询分离
- 帮助学习任务特定的路由模式

#### 3. 聚类对比损失
- 使用 K-means 对训练查询进行聚类
- 学习感知聚类的表示
- 提高对不同查询类型的泛化能力

### 双重对比策略

RouterDC 中的"双重"指的是两种互补的对比机制：
1. **查询-模型对比**：将查询与合适的模型对齐
2. **查询-查询对比**：将相似的查询分组（通过任务和聚类）

这种双重方法确保路由器学习到：
- 哪些模型对哪些查询效果良好
- 什么使查询相似或不同

## 配置参数

### 训练超参数（配置中的 `hparam`）

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `hidden_state_dim` | int | `768` | 主干编码器的隐藏状态维度（mDeBERTa base = 768）。 |
| `similarity_function` | str | `"cos"` | 用于计算查询-LLM 亲和度的相似度函数。选项：`"cos"`（余弦相似度）、`"inner"`（内积）。推荐使用余弦。 |
| `batch_size` | int | `32` | 训练批次大小。较大的值可以提高训练稳定性，但需要更多内存。 |
| `training_steps` | int | `500` | 总训练步数。对于更大的数据集，增加此值。 |
| `learning_rate` | float | `5.0e-5` | AdamW 优化器的学习率。对于更大的模型，使用较低的值（1e-5）。 |
| `top_k` | int | `3` | 作为正样本使用的表现最好的 LLM 数量。 |
| `last_k` | int | `3` | 作为负样本使用的表现最差的 LLM 数量。 |
| `temperature` | float | `1.0` | 对比损失中 softmax 的温度。较低的值（0.1-0.5）使分布更尖锐。 |
| `sample_loss_weight` | float | `0.0` | 样本-样本对比损失的权重。设置为 1.0 以启用任务级别分组。 |
| `cluster_loss_weight` | float | `1.0` | 聚类对比损失的权重。较高的值强调感知聚类的学习。 |
| `H` | int | `3` | 对比损失中每个正样本的负样本数量。 |
| `gradient_accumulation` | int | `1` | 用于获得更大有效批次大小的梯度累积步数。 |
| `n_clusters` | int | `3` | 用于对训练查询进行 K-means 聚类的聚类数量。 |
| `max_test_samples` | int | `500` | 使用的最大测试样本数量（null 表示全部）。适用于快速评估。 |
| `source_max_token_len` | int | `512` | 查询的最大 token 长度。较长的查询将被截断。 |
| `target_max_token_len` | int | `512` | LLM 名称/描述的最大 token 长度。 |
| `device` | str | `"cpu"` | 训练设备：`"cpu"` 或 `"cuda"`。强烈推荐使用 GPU。 |
| `seed` | int | `1` | 用于可重复性的随机种子。 |
| `eval_steps` | int | `50`` | 每 N 个训练步评估模型一次。 |

### 推理参数

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `inference_batch_size` | int | `64` | 推理的批次大小。较大的值可以加速批量路由。 |
| `inference_temperature` | float | `1.0` | 推理期间路由分数的温度。使用 1.0 进行标准 softmax。 |

### 数据路径

| 参数 | 描述 |
|-----------|-------------|
| `routing_data_train` | 包含查询-LLM 性能对的训练数据（JSONL 格式） |
| `routing_data_test` | 用于评估的测试数据 |
| `llm_data` | LLM 候选信息 |

### 模型路径

| 参数 | 用途 | 使用方式 |
|-----------|---------|-------|
| `backbone_model` | 用于初始化的预训练编码器 | 通常为 `"microsoft/mdeberta-v3-base"` |
| `save_model_path` | 保存训练模型的位置 | 训练：保存最佳模型检查点 |
| `load_model_path` | 用于推理的加载模型 | 测试：加载训练好的模型权重 |

## CLI 使用方法

可以通过 `llmrouter` 命令行界面使用 RouterDC：

### 训练

```bash
# 训练 RouterDC（推荐使用 GPU）
llmrouter train --router routerdc --config configs/model_config_train/dcrouter.yaml --device cuda

# 以静默模式训练
llmrouter train --router routerdc --config configs/model_config_train/dcrouter.yaml --device cuda --quiet
```

### 推理

```bash
# 路由单个查询
llmrouter infer --router routerdc --config configs/model_config_test/dcrouter.yaml \
    --query "解释机器学习的概念"

# 从文件路由查询
llmrouter infer --router routerdc --config configs/model_config_test/dcrouter.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
llmrouter infer --router routerdc --config configs/model_config_test/dcrouter.yaml \
    --query "什么是深度学习？" --route-only
```

### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router routerdc --config configs/model_config_test/dcrouter.yaml

# 使用自定义端口启动
llmrouter chat --router routerdc --config configs/model_config_test/dcrouter.yaml --port 8080

# 创建公开可共享的链接
llmrouter chat --router routerdc --config configs/model_config_test/dcrouter.yaml --share
```

---

## 使用示例

### 训练 RouterDC

```python
from llmrouter.models import DCRouter, DCRouterTrainer

# 使用训练配置初始化路由器
router = DCRouter(yaml_path="configs/model_config_train/dcrouter.yaml")

# 创建训练器
trainer = DCRouterTrainer(router=router, device="cuda")

# 训练模型
trainer.train()
# 最佳模型将保存到 save_model_path
```

**命令行训练：**
```bash
python tests/train_test/test_dcrouter.py --yaml_path configs/model_config_train/dcrouter.yaml
```

### 推理：路由单个查询

```python
from llmrouter.models import DCRouter

# 使用测试配置初始化路由器（加载训练好的模型）
router = DCRouter(yaml_path="configs/model_config_test/dcrouter.yaml")

# 路由单个查询
query = {"query": "解释机器学习的概念"}
result = router.route_single(query)

print(f"选择的模型：{result['model_name']}")
```

### 推理：批量路由与 API 执行

```python
from llmrouter.models import DCRouter

# 初始化路由器
router = DCRouter(yaml_path="configs/model_config_test/dcrouter.yaml")

# 准备批量查询
queries = [
    {"query": "什么是深度学习？", "ground_truth": "..."},
    {"query": "求解 2x + 5 = 15", "ground_truth": "x = 5"},
    {"query": "编写一个计算阶乘的 Python 函数", "ground_truth": "..."}
]

# 路由并执行查询
results = router.route_batch(batch=queries, task_name="general")

for result in results:
    print(f"查询：{result['query']}")
    print(f"路由到：{result['model_name']}")
    print(f"响应：{result['response']}")
    print(f"性能：{result.get('task_performance', 'N/A')}")
    print("-" * 80)
```

## YAML 配置示例

**训练配置**（`configs/model_config_train/dcrouter.yaml`）：

```yaml
data_path:
  routing_data_train: 'data/example_data/routing_data/default_routing_train_data.jsonl'
  routing_data_test: 'data/example_data/routing_data/default_routing_test_data.jsonl'
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

model_path:
  save_model_path: 'saved_models/dcrouter/dcrouter_model.pth'
  backbone_model: 'microsoft/mdeberta-v3-base'

hparam:
  # 模型架构
  hidden_state_dim: 768
  similarity_function: "cos"

  # 训练
  batch_size: 32
  training_steps: 500
  learning_rate: 5.0e-5

  # 对比损失配置
  top_k: 3                          # 表现最好的作为正样本
  last_k: 3                         # 表现最差的作为负样本
  temperature: 1.0
  sample_loss_weight: 0.0           # 禁用任务级别损失
  cluster_loss_weight: 1.0          # 启用聚类损失
  H: 3                              # 每个正样本的负样本数

  # 数据预处理
  n_clusters: 3
  max_test_samples: 500

  # 设备
  device: "cuda"                    # 推荐 GPU

metric:
  weights:
    performance: 1
    cost: 0
    llm_judge: 0
```

**测试配置**（`configs/model_config_test/dcrouter.yaml`）：

```yaml
data_path:
  query_data_test: 'data/example_data/query_data/default_query_test.jsonl'
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

model_path:
  load_model_path: 'saved_models/dcrouter/best_model.pth'
  backbone_model: 'microsoft/mdeberta-v3-base'

hparam:
  hidden_state_dim: 768
  similarity_function: "cos"
  inference_batch_size: 64
  inference_temperature: 1.0
  device: "cuda"
```

## 优势

- ✅ **最先进的编码器**：使用 mDeBERTa，一个强大的多语言预训练模型
- ✅ **多级别学习**：结合样本、任务和聚类级别的对比信号
- ✅ **灵活的相似度**：支持余弦相似度和内积
- ✅ **感知聚类**：利用查询聚类以获得更好的泛化
- ✅ **多语言**：mDeBERTa 支持 100+ 种语言
- ✅ **端到端可学习**：联合学习查询和 LLM 嵌入

## 局限性

- ❌ **需要 GPU**：由于 transformer 编码器，在 CPU 上训练很慢
- ❌ **超参数敏感**：许多超参数需要调优（损失权重、温度、k 值）
- ❌ **需要训练数据**：需要大量路由性能数据
- ❌ **模型大小较大**：mDeBERTa-base 有约 280M 参数
- ❌ **复杂架构**：比 KNN 或 SVM 等简单方法更复杂
- ❌ **冷启动**：新的 LLM 需要重新训练以获得嵌入

## 何时使用 RouterDC

**适用场景：**
- 有 GPU 资源的大规模路由应用
- 多语言路由场景
- 拥有充足的训练数据（1000+ 样本）
- 需要最先进的路由性能
- 查询分布有明显的聚类/组

**考虑替代方案的情况：**
- GPU 资源有限 → 使用 MLP/SVM/KNN 路由器
- 训练数据集较小（<500 样本）→ 使用 KNN 路由器
- 需要快速训练 → 使用 ELO 路由器或启发式方法
- 可解释性至关重要 → 使用更简单的模型
- 单语言路由 → 标准 BERT 可能足够

## 超参数调优技巧

1. **损失权重**：
   - 从 `cluster_loss_weight=1.0`、`sample_loss_weight=0.0` 开始
   - 如果查询有清晰的任务标签，添加 `sample_loss_weight=1.0`
   - 如果两者都使用，则平衡权重（例如，各 0.5）

2. **对比参数**：
   - 增加 `top_k` 和 `last_k`（到 5-7）以获得更稳健的学习
   - 降低 `temperature`（0.1-0.5）以获得更尖锐的分布
   - 增加 `H`（到 5-10）以获得更多负样本

3. **训练**：
   - 16GB GPU 使用 `batch_size=32`，8GB GPU 使用 `batch_size=16`
   - 对于更大的数据集，增加 `training_steps`（到 1000+）
   - 如果 GPU 内存有限，使用 `gradient_accumulation`

4. **聚类**：
   - 设置 `n_clusters` ≈ sqrt(num_training_queries) / 10
   - 根据数据多样性尝试 3-10 个聚类

5. **评估**：
   - 每 `eval_steps` 监控验证准确率
   - 如果验证损失停止改善，使用早停

## 实现细节

- **框架**：PyTorch + Hugging Face Transformers
- **主干**：mDeBERTa-v3-base（microsoft/mdeberta-v3-base）
- **优化器**：AdamW，带线性预热
- **损失**：多目标对比损失（样本-LLM + 聚类）
- **序列化**：PyTorch state_dict 保存为 `.pth` 文件

## 相关路由器

- **图路由器（Graph Router）**：也使用结构化表示，但使用 GNN
- **MLP 路由器**：更简单的神经网络方法，训练更快
- **因果 LM 路由器（Causal LM Router）**：使用微调的 LLM 而不是编码器
- **MF 路由器**：矩阵分解方法，更轻量

---

如有问题或疑问，请参考 LLMRouter 主文档或在 GitHub 上提交 issue。
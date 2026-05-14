# MLP 路由器

## 概述

**MLP 路由器**（Multi-Layer Perceptron Router，多层感知机路由器）是一种基于监督学习的路由方法，它使用神经网络分类器来预测给定查询的最适合的大语言模型（LLM），基于从训练数据中学习到的模式。

## 论文参考

该路由器实现了用于 LLM 路由的**多层感知机（MLP）**方法，参考自以下论文：

- **[FusionFactory: Fusing LLM Capabilities with Multi-LLM Log Data](https://arxiv.org/abs/2507.10540)**
  - Feng, T., Zhang, H., Lei, Z., et al. (2025). arXiv:2507.10540.
  - 提出了通过定制的 LLM 路由器进行查询级融合的方法，包括基于 MLP 的方法。

- **基础理论**: Rumelhart, D. E., Hinton, G. E., & Williams, R. J. (1986). "Learning representations by back-propagating errors." Nature.

MLP 路由器将 LLM 选择视为一个多类分类问题，目标是预测每个输入查询的最佳性能模型。

## 工作原理

### 架构

```
查询 → 嵌入 → MLP 分类器 → LLM 选择
            （隐藏层）
```

### 路由机制

1. **查询嵌入**：使用 Longformer 嵌入将每个输入查询转换为固定大小的向量表示
2. **特征学习**：MLP 在训练期间学习嵌入空间中的非线性模式
3. **分类**：训练后的网络预测哪个 LLM 最可能在查询上表现最佳
4. **选择**：路由器选择具有最高预测概率的 LLM

### 训练过程

1. **数据准备**：
   - 从不同 LLM 收集历史查询-响应对
   - 为每个查询生成嵌入
   - 根据性能指标将每个查询标记为表现最佳的 LLM

2. **模型训练**：
   - 将查询嵌入作为输入特征输入
   - 使用 LLM 名称作为目标标签
   - 使用反向传播和梯度下降训练 MLP 分类器

3. **优化**：
   - 模型学习将查询嵌入映射到最优 LLM 选择
   - 正则化防止对训练数据的过拟合

## 配置参数

### 训练超参数（配置文件中的 `hparam`）

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `hidden_layer_sizes` | list[int] | `[128, 64]` | 每个隐藏层中的神经元数量。较大的值增加模型容量但可能导致过拟合。例如：`[128, 64]` 创建一个具有 128 和 64 个神经元的 2 层网络。 |
| `activation` | str | `"relu"` | 隐藏层的激活函数。选项：`"identity"`、`"logistic"`、`"tanh"`、`"relu"`。大多数情况下推荐使用 ReLU。 |
| `solver` | str | `"adam"` | 优化算法。选项：`"lbfgs"`（适用于小数据集）、`"adam"`（适用于大数据集）、`"sgd"`（需要精细控制）。 |
| `alpha` | float | `0.0001` | L2 正则化参数。较高的值防止过拟合，但可能降低模型容量。范围：`0.0001` 到 `0.01`。 |
| `learning_rate` | str | `"adaptive"` | 学习率调度。选项：`"constant"`（恒定）、`"invscaling"`（逆缩放）、`"adaptive"`（根据训练进度自动调整）。 |
| `learning_rate_init` | float | `0.001` | 权重更新的初始学习率。典型范围：`0.0001` 到 `0.01`。 |
| `max_iter` | int | `500` | 最大训练迭代次数/轮数。如果模型未收敛，请增加此值。 |
| `random_state` | int | `42` | 用于可重复性的随机种子。设置为任何整数以在运行之间获得一致的结果。 |

### PyTorch 版本专用参数

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `lr` | float | `0.001` | 学习率，控制权重更新的步长 |
| `epochs` | int | `100` | 训练轮数（遍历整个数据集的次数） |
| `batch_size` | int | `32` | 每次训练批次中的样本数量 |

### 数据路径

| 参数 | 描述 |
|-----------|-------------|
| `query_data_train` | 训练查询，JSONL 格式 |
| `routing_data_train` | 历史路由性能数据（查询-LLM 对及性能分数） |
| `query_embedding_data` | 预计算的查询嵌入（PyTorch 张量文件） |
| `llm_data` | LLM 候选者信息（模型、API 名称、元数据） |

### 模型路径

| 参数 | 用途 | 使用场景 |
|-----------|---------|-------|
| `ini_model_path` | 用于初始化的预训练模型 | 可选：留空以从头开始训练 |
| `save_model_path` | 保存训练后的模型的位置 | 训练：训练完成后模型保存在此处 |
| `load_model_path` | 加载用于推理的模型 | 测试：训练好的 `.pkl` 文件路径 |

### 推理/测试参数

在推理期间，路由器使用：
- **加载的模型**：来自 `load_model_path` 的预训练 MLP 分类器
- **API 配置**：来自 `llm_data` 的端点和模型映射
- **任务格式化**：可选的 `task_name` 参数以格式化特定基准测试的查询

推理期间不调整超参数——所有决策都由训练好的模型做出。

## CLI 使用方法

MLP 路由器可以通过 `llmrouter` 命令行界面使用：

### 训练

```bash
# 训练 MLP 路由器
llmrouter train --router mlprouter --config configs/model_config_train/mlprouter.yaml

# 使用 GPU 加速训练
llmrouter train --router mlprouter --config configs/model_config_train/mlprouter.yaml --device cuda

# 使用静默模式训练（较少的详细输出）
llmrouter train --router mlprouter --config configs/model_config_train/mlprouter.yaml --quiet
```

### 推理

```bash
# 路由单个查询
llmrouter infer --router mlprouter --config configs/model_config_test/mlprouter.yaml \
    --query "什么是机器学习？"

# 从文件路由查询
llmrouter infer --router mlprouter --config configs/model_config_test/mlprouter.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
llmrouter infer --router mlprouter --config configs/model_config_test/mlprouter.yaml \
    --query "解释神经网络" --route-only
```

### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router mlprouter --config configs/model_config_test/mlprouter.yaml

# 使用自定义端口启动
llmrouter chat --router mlprouter --config configs/model_config_test/mlprouter.yaml --port 8080

# 创建公共可共享链接
llmrouter chat --router mlprouter --config configs/model_config_test/mlprouter.yaml --share
```

---

## 使用示例

### 训练 MLP 路由器

```python
from llmrouter.models import MLPRouter, MLPTrainer

# 使用训练配置初始化路由器
router = MLPRouter(yaml_path="configs/model_config_train/mlprouter.yaml")

# 创建训练器
trainer = MLPTrainer(router=router, device="cpu")

# 训练模型
trainer.train()
# 模型将保存到 save_model_path 指定的路径
```

**命令行训练：**
```bash
python tests/train_test/test_mlprouter.py --yaml_path configs/model_config_train/mlprouter.yaml
```

### 推理：路由单个查询

```python
from llmrouter.models import MLPRouter

# 使用测试配置初始化路由器（加载训练好的模型）
router = MLPRouter(yaml_path="configs/model_config_test/mlprouter.yaml")

# 路由单个查询
query = {"query": "法国的首都是什么？"}
result = router.route_single(query)

print(f"选择的模型: {result['model_name']}")
```

### 推理：批量路由与 API 执行

```python
from llmrouter.models import MLPRouter

# 初始化路由器
router = MLPRouter(yaml_path="configs/model_config_test/mlprouter.yaml")

# 准备查询批次
queries = [
    {"query": "解释量子计算", "ground_truth": "..."},
    {"query": "编写一个对列表进行排序的 Python 函数", "ground_truth": "..."}
]

# 路由并执行查询（包括 API 调用和性能评估）
results = router.route_batch(batch=queries, task_name="general")

for result in results:
    print(f"查询: {result['query']}")
    print(f"路由到: {result['model_name']}")
    print(f"响应: {result['response']}")
    print(f"性能: {result.get('task_performance', 'N/A')}")
    print("-" * 80)
```

### 使用特定任务（例如：MMLU、GSM8K）

```python
# 为特定基准测试任务路由查询
queries = [
    {
        "query": "问题文本在这里",
        "choices": ["A", "B", "C", "D"],
        "ground_truth": "A"
    }
]

# 任务名称触发自动提示格式化
results = router.route_batch(batch=queries, task_name="mmlu")
```

### 命令行测试

```bash
python tests/inference_test/test_mlprouter.py --yaml_path configs/model_config_test/mlprouter.yaml
```

## YAML 配置示例

**训练配置**（`configs/model_config_train/mlprouter.yaml`）：

```yaml
# mlprouter 训练配置参数（PyTorch 版本）：

data_path:
  query_data_train: 'data/example_data/query_data/default_query_train.jsonl'
  query_data_test: 'data/example_data/query_data/default_query_test.jsonl'
  query_embedding_data: 'data/example_data/routing_data/query_embeddings_longformer.pt'
  routing_data_train: 'data/example_data/routing_data/default_routing_train_data.jsonl'
  routing_data_test: 'data/example_data/routing_data/default_routing_test_data.jsonl'
  llm_data: 'data/example_data/llm_candidates/default_llm.json'
  llm_embedding_data: 'data/example_data/llm_candidates/default_llm_embeddings.json'

model_path:
  ini_model_path: ''  # 留空以从头开始训练
  save_model_path: 'saved_models/mlprouter/mlprouter.pkl'

metric:
  weights:
    performance: 1    # 任务性能的权重
    cost: 0           # 成本（token）的权重
    llm_judge: 0      # LLM-as-judge 分数的权重

hparam:
  # 网络架构
  hidden_layer_sizes: [128, 64]   # 每个隐藏层中的神经元数量
  activation: "relu"              # 隐藏层的激活函数（'relu', 'tanh', 'logistic', 'identity'）

  # 训练参数（PyTorch）
  lr: 0.001                       # 学习率
  epochs: 100                     # 训练轮数
  batch_size: 32                  # 训练批次大小
  alpha: 0.0001                   # L2 正则化（权重衰减）
```

**测试配置**（`configs/model_config_test/mlprouter.yaml`）：

```yaml
# mlprouter 测试配置参数：

data_path:
  query_data_test: 'data/example_data/query_data/default_query_test.jsonl'
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

model_path:
  load_model_path: 'saved_models/mlprouter/mlprouter.pkl'

metric:
  weights:
    performance: 1
    cost: 0
    llm_judge: 0

# 注意：推理不需要 hparam，但可以包含作为参考
```

## 优势

- ✅ **快速推理**：训练完成后，路由速度极快（单次前向传播）
- ✅ **可扩展**：高效处理大量 LLM 候选者
- ✅ **灵活**：超参数可以针对不同的数据集大小进行调整
- ✅ **可解释**：可以分析哪些特征（嵌入维度）影响路由决策

## 限制

- ❌ **需要训练数据**：需要历史性能数据进行监督学习
- ❌ **特征依赖**：性能很大程度上取决于查询嵌入的质量
- ❌ **泛化能力**：对于与训练数据非常不同的查询，泛化能力可能较差
- ❌ **二元决策**：只选择一个 LLM（没有集成或回退机制）

## 何时使用 MLP 路由器

**适用场景：**
- 您有足够的历史查询-响应数据和性能标签
- 查询分布相对稳定且可预测
- 需要快速、低延迟的路由决策
- 想要一个简单、可解释的 LLM 路由基线

**考虑替代方案的情况：**
- 可用的训练数据有限 → 使用 KNN 路由器或启发式方法
- 查询高度多样化或超出分布 → 使用基于 LLM 的路由器
- 需要多模型集成 → 使用混合方法
- 需要动态自适应 → 使用在线学习方法

## 最佳性能建议

1. **数据质量**：确保训练数据覆盖多样化的查询类型并具有准确的性能标签
2. **超参数调优**：
   - 从默认值开始
   - 如果欠拟合，增加 `hidden_layer_sizes`
   - 如果过拟合，增加 `alpha`
   - 对于小数据集（<1000 个样本），使用 `solver="lbfgs"`
3. **嵌入质量**：使用适合领域的嵌入（Longformer 用于长文本）
4. **定期重新训练**：定期使用新数据重新训练以适应变化的查询分布
5. **验证**：始终在保留的测试集上进行验证以检查泛化能力

## 实现细节

- **框架**：PyTorch（支持 CUDA 加速）
- **嵌入模型**：Longformer（用于查询向量化）
- **输入维度**：由嵌入大小决定（通常为 768 或 1024）
- **输出**：分类预测（LLM 名称作为字符串）
- **序列化**：模型保存为 `.pkl` 文件

## 相关路由器

- **KNN 路由器**：基于实例学习的替代方案（无需训练）
- **SVM 路由器**：另一种使用核技巧的监督学习方法
- **LLM 路由器**：使用语言模型进行路由决策
- **Graph 路由器**：利用图神经网络进行结构化路由

---

如有问题或建议，请参阅 LLMRouter 主文档或在 GitHub 上提出 issue。
# SVM 路由器

## 概述

**SVM 路由器**（Support Vector Machine Router，支持向量机路由器）是一种基于监督学习的路由方法，使用基于核的分类技术为每个查询选择最优的 LLM。它利用 SVM 的强大能力在高维嵌入空间中寻找决策边界。

## 论文参考

此路由器实现了用于 LLM 路由的 **支持向量机（SVM）** 分类，如以下文献所述：

- **[FusionFactory: Fusing LLM Capabilities with Multi-LLM Log Data](https://arxiv.org/abs/2507.10540)**
  - Feng, T., Zhang, H., Lei, Z., et al. (2025). arXiv:2507.10540.
  - 提出了通过定制的 LLM 路由器（包括基于 SVM 的方法）进行查询级融合。

- **原始 SVM 论文**：
  - Cortes, C., & Vapnik, V. (1995). "Support-vector networks." Machine Learning.

- **应用**：SVM 对高维数据和非线性可分类别特别有效，使其非常适合基于查询嵌入的路由。

## 工作原理

### 架构

```
Query → Embedding → SVM Classifier → LLM Selection
                    (Kernel Mapping)
```

### 路由机制

1. **查询嵌入**：使用 Longformer 嵌入将输入查询转换为固定大小的向量表示
2. **核变换**：使用核函数（如 RBF）将嵌入映射到更高维的特征空间
3. **决策边界**：使用训练好的 SVM 根据超平面分离分类哪个 LLM 是最优的
4. **选择**：返回具有最高决策函数分数的 LLM

### 训练过程

1. **数据准备**：
   - 从不同 LLM 收集历史查询-响应对
   - 为每个查询生成嵌入
   - 用表现最好的 LLM 标记每个查询

2. **核选择**：
   - 选择合适的核函数（RBF、多项式、线性或 sigmoid）
   - RBF 核是默认选择，在大多数情况下效果良好

3. **模型训练**：
   - 找到最大化类别之间边界的最优超平面
   - 使用支持向量（关键训练样本）定义决策边界
   - 正则化参数 C 控制边界宽度和分类错误之间的权衡

4. **优化**：
   - SVM 优化是凸的，保证全局最优
   - 核技巧允许高效学习复杂的非线性边界

## SVM 的主要优势

- **核技巧**：可以通过映射到高维来处理非线性可分数据
- **边界最大化**：找到具有良好泛化能力的鲁棒决策边界
- **内存高效**：仅存储支持向量（训练数据的子集）
- **高维有效**：即使特征数量超过样本数量也能良好工作

## 配置参数

### 训练超参数（配置中的 `hparam`）

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `kernel` | str | `"rbf"` | 核函数类型。选项：`"linear"`（线性决策边界）、`"poly"`（多项式）、`"rbf"`（径向基函数，推荐）、`"sigmoid"`。RBF 对非线性问题最通用。 |
| `C` | float | `1.0` | 正则化参数。控制平滑决策边界和正确分类训练点之间的权衡。较低的 C → 较宽的边界，更多正则化。较高的 C → 较窄的边界，对错误分类的容忍度较低。范围：`0.01` 到 `100`。 |
| `gamma` | str/float | `"scale"` | RBF/poly/sigmoid 的核系数。定义单个训练样本的影响半径。选项：`"scale"`（默认：1/(n_features * X.var())）、`"auto"`（1/n_features）或浮点值。较高的 gamma → 更紧密的决策边界（过拟合风险）。 |
| `probability` | bool | `true` | 启用概率估计。如果为 true，可以使用 `predict_proba()` 获取置信度分数。训练稍慢但提供不确定性估计。 |
| `random_state` | int | - | 用于可重复性的随机种子（可选）。 |

### 数据路径

| 参数 | 描述 |
|-----------|-------------|
| `query_data_train` | JSONL 格式的训练查询 |
| `routing_data_train` | 历史路由性能数据（查询-LLM 对及其性能分数） |
| `query_embedding_data` | 预计算的查询嵌入（PyTorch 张量文件） |
| `llm_data` | LLM 候选信息（模型、API 名称、元数据） |

### 模型路径

| 参数 | 用途 | 使用方式 |
|-----------|---------|-------|
| `ini_model_path` | 用于初始化的预训练模型 | 可选：留空以从头开始训练 |
| `save_model_path` | 保存训练模型的路径 | 训练：模型在训练完成后保存到这里 |
| `load_model_path` | 用于推理的加载模型 | 测试：已训练的 `.pkl` 文件路径 |

### 推理/测试参数

在推理过程中，路由器：
- 从 `load_model_path` 加载预训练的 SVM 模型
- 使用与训练相同的核和参数
- 应用决策函数来预测最优的 LLM
- 推理期间不调整超参数

## CLI 使用

SVM 路由器可以通过 `llmrouter` 命令行界面使用：

### 训练

```bash
# 训练 SVM 路由器
llmrouter train --router svmrouter --config configs/model_config_train/svmrouter.yaml

# 使用安静模式训练
llmrouter train --router svmrouter --config configs/model_config_train/svmrouter.yaml --quiet
```

### 推理

```bash
# 路由单个查询
llmrouter infer --router svmrouter --config configs/model_config_test/svmrouter.yaml \
    --query "Explain the theory of relativity"

# 从文件路由查询
llmrouter infer --router svmrouter --config configs/model_config_test/svmrouter.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
llmrouter infer --router svmrouter --config configs/model_config_test/svmrouter.yaml \
    --query "What is machine learning?" --route-only
```

### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router svmrouter --config configs/model_config_test/svmrouter.yaml

# 使用自定义端口启动
llmrouter chat --router svmrouter --config configs/model_config_test/svmrouter.yaml --port 8080

# 创建可公开分享的链接
llmrouter chat --router svmrouter --config configs/model_config_test/svmrouter.yaml --share
```

---

## 使用示例

### 训练 SVM 路由器

```python
from llmrouter.models import SVMRouter, SVMRouterTrainer

# 使用训练配置初始化路由器
router = SVMRouter(yaml_path="configs/model_config_train/svmrouter.yaml")

# 创建训练器
trainer = SVMRouterTrainer(router=router, device="cpu")

# 训练模型
trainer.train()
# 模型将保存到 save_model_path 指定的路径
```

**命令行训练：**
```bash
python tests/train_test/test_svmrouter.py --yaml_path configs/model_config_train/svmrouter.yaml
```

### 推理：路由单个查询

```python
from llmrouter.models import SVMRouter

# 使用测试配置初始化路由器（加载已训练的模型）
router = SVMRouter(yaml_path="configs/model_config_test/svmrouter.yaml")

# 路由单个查询
query = {"query": "Explain the theory of relativity"}
result = router.route_single(query)

print(f"Selected Model: {result['model_name']}")
```

### 推理：带 API 执行的批量路由

```python
from llmrouter.models import SVMRouter

# 初始化路由器
router = SVMRouter(yaml_path="configs/model_config_test/svmrouter.yaml")

# 准备批量查询
queries = [
    {"query": "What is machine learning?", "ground_truth": "..."},
    {"query": "Write a sorting algorithm in Python", "ground_truth": "..."}
]

# 路由并执行查询（包括 API 调用和性能评估）
results = router.route_batch(batch=queries, task_name="general")

for result in results:
    print(f"Query: {result['query']}")
    print(f"Routed to: {result['model_name']}")
    print(f"Response: {result['response']}")
    print(f"Performance: {result.get('task_performance', 'N/A')}")
    print("-" * 80)
```

### 用于特定任务

```python
# 为基准测试任务路由查询（例如 MMLU）
queries = [
    {
        "query": "Which of the following is a prime number?",
        "choices": ["A. 4", "B. 6", "C. 7", "D. 8"],
        "ground_truth": "C"
    }
]

# 任务名称触发自动提示格式化
results = router.route_batch(batch=queries, task_name="mmlu")
```

## YAML 配置示例

**训练配置**（`configs/model_config_train/svmrouter.yaml`）：

```yaml
data_path:
  query_data_train: 'data/example_data/query_data/default_query_train.jsonl'
  routing_data_train: 'data/example_data/routing_data/default_routing_train_data.jsonl'
  query_embedding_data: 'data/example_data/routing_data/query_embeddings_longformer.pt'
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

model_path:
  ini_model_path: ''  # 留空以从头开始训练
  save_model_path: 'saved_models/svmrouter/svmrouter.pkl'

hparam:
  kernel: "rbf"          # 径向基函数核
  C: 1.0                 # 正则化强度
  gamma: "scale"         # 自动 gamma 计算
  probability: true      # 启用概率估计

metric:
  weights:
    performance: 1    # 任务性能权重
    cost: 0           # 成本权重（tokens）
    llm_judge: 0      # LLM 作为裁判的分数权重
```

**测试配置**（`configs/model_config_test/svmrouter.yaml`）：

```yaml
data_path:
  query_data_test: 'data/example_data/query_data/default_query_test.jsonl'
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

model_path:
  load_model_path: 'saved_models/svmrouter/svmrouter.pkl'

# 注意：hparam 部分可以包含在内以供参考，但在推理期间不使用
```

## 核选择指南

### 线性核（`kernel="linear"`）
- **适用场景**：类别线性可分、高维数据
- **优势**：训练快速、可解释、无需调整 gamma
- **劣势**：无法处理非线性模式

### RBF 核（`kernel="rbf"`）- **推荐**
- **适用场景**：数据分布未知、通用路由
- **优势**：处理非线性模式、最通用
- **劣势**：需要调整 gamma 参数

### 多项式核（`kernel="poly"`）
- **适用场景**：数据具有多项式关系
- **优势**：可以建模复杂的交互
- **劣势**：需要调整更多参数（degree、gamma、coef0）

### Sigmoid 核（`kernel="sigmoid"`）
- **适用场景**：需要类似神经网络的决策边界
- **优势**：类似于神经网络激活
- **劣势**：可能收敛不佳，使用较少

## 超参数调整技巧

### C 参数（正则化）
```
低 C (0.01-0.1)：   宽边界，更多泛化，容忍错误
中等 C (1.0)：      平衡（默认）
高 C (10-100)：     窄边界，紧密拟合训练数据
```

### Gamma 参数（RBF 核）
```
低 gamma (0.001)：   平滑决策边界，影响范围远
中等 gamma：        平衡（使用 "scale" 或 "auto"）
高 gamma (1-10)：   复杂边界，局部影响（过拟合风险）
```

### 推荐调整策略
1. 从默认值开始：`kernel="rbf"`、`C=1.0`、`gamma="scale"`
2. 如果欠拟合：增加 C，增加 gamma
3. 如果过拟合：减少 C，减少 gamma，或使用线性核
4. 使用交叉验证找到最优值

## 优势

- ✅ **坚实的理论基础**：具有可证明泛化边界的边界最大化
- ✅ **核灵活性**：可以建模复杂的非线性决策边界
- ✅ **内存高效**：仅存储支持向量（通常是数据的小子集）
- ✅ **对异常值鲁棒**：正则化防止对噪声过拟合
- ✅ **高维有效**：当特征数 >> 样本数时效果良好
- ✅ **概率估计**：可以为路由决策提供置信度分数

## 局限性

- ❌ **大型数据集上慢**：训练时间扩展性差（O(n²) 到 O(n³)）
- ❌ **核选择**：性能在很大程度上取决于选择正确的核和参数
- ❌ **专注于二元**：最初设计用于二元分类（扩展到多类）
- ❌ **无增量学习**：必须使用新数据从头重新训练
- ❌ **需要训练数据**：需要标记的历史性能数据
- ❌ **黑盒核**：非线性核可能难以解释

## 何时使用 SVM 路由器

**良好的使用场景：**
- 中等规模数据集（数百到数万个样本）
- 简单模型无法捕获的非线性路由模式
- 需要关于泛化的理论保证
- 希望获得路由置信度的概率估计
- 具有平衡的类别分布（每个 LLM 的样本数量相似）

**考虑替代方案的情况：**
- 非常大的数据集（>100k 样本）→ 使用 MLP 路由器或集成方法
- 需要实时训练更新 → 使用在线学习方法
- 高度不平衡的数据 → 使用加权 SVM 或其他技术
- 简单的线性模式 → 使用逻辑回归或线性 SVM
- 训练数据有限 → 使用 KNN 路由器或启发式方法

## 与 MLP 路由器的比较

| 方面 | SVM 路由器 | MLP 路由器 |
|--------|------------|------------|
| 训练速度 | 大型数据集上较慢 | 使用小批量训练更快 |
| 推理速度 | 快 | 快 |
| 非线性建模 | 核技巧 | 多个隐藏层 |
| 内存使用 | 仅支持向量 | 存储所有权重 |
| 超参数调整 | 核 + C + gamma | 层 + 激活 + 学习率 |
| 理论保证 | 强（边界理论） | 较弱 |
| 可扩展性 | 差（O(n²-n³)） | 较好（O(n)） |

## 实现细节

- **框架**：scikit-learn 的 `SVC`（支持向量分类）
- **嵌入模型**：Longformer（用于查询向量化）
- **输入维度**：由嵌入大小决定（通常为 768 或 1024）
- **输出**：分类预测（LLM 名称作为字符串）
- **序列化**：使用 pickle 将模型保存为 `.pkl` 文件
- **多类策略**：一对一或一对多（scikit-learn 中自动）

## 最佳性能技巧

1. **数据预处理**：
   - 确保嵌入已归一化（SVM 对特征尺度敏感）
   - 删除重复或非常相似的查询
   - 如果可能，平衡类别分布

2. **超参数选择**：
   - 从 RBF 核和默认 C=1.0、gamma="scale" 开始
   - 使用网格搜索或随机搜索进行调整
   - 在保留的测试集上验证

3. **核选择**：
   - 首先尝试线性核（快速、可解释）
   - 如果线性核效果不佳，使用 RBF
   - 考虑在特定领域使用多项式核

4. **性能优化**：
   - 对于大型数据集，使用 `kernel="linear"` 或采样子集
   - 仅在需要时启用 probability=true（增加开销）
   - 对于非常大的数据集，考虑近似方法

5. **定期重新训练**：
   - 定期使用新数据重新训练
   - 监控验证集上的性能
   - 如果 LLM 能力发生变化，更新嵌入

## 相关路由器

- **MLP 路由器**：基于神经网络的替代方案，更适合非常大的数据集
- **KNN 路由器**：基于实例，无需训练，适合小数据集
- **线性路由器**：使用逻辑回归的简化版本
- **集成路由器**：将 SVM 与其他路由方法结合

---

如有问题或建议，请参考主要 LLMRouter 文档或在 GitHub 上提交 issue。
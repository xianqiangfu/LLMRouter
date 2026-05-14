# KNN 路由器

## 概述

**KNN 路由器**（K-近邻路由器）是一种基于实例的路由方法，通过查询与历史查询的相似度来选择最优 LLM。它无需显式训练阶段，简单易懂且可解释性强，非常适合标注数据有限的场景。

## 论文参考

该路由器实现了用于 LLM 路由的 **K-近邻（KNN）算法**，相关论文如下：

- **[FusionFactory: Fusing LLM Capabilities with Multi-LLM Log Data](https://arxiv.org/abs/2507.10540)**
  - Feng, T., Zhang, H., Lei, Z., et al. (2025). arXiv:2507.10540.
  - 提出通过定制化的 LLM 路由器（包括基于 KNN 的方法）进行查询级融合。

- **原始 KNN 概念**：
  - Cover, T., & Hart, P. (1967). "Nearest neighbor pattern classification." IEEE Transactions on Information Theory.

- **路由应用**：KNN 是一种惰性学习算法，通过查找 K 个最相似的历史查询并根据其表现投票选择最佳 LLM 来做出路由决策。

## 工作原理

### 架构

```
查询 → 嵌入 → 查找 K 近邻 → 多数投票 → LLM 选择
              (距离计算)
```

### 路由机制

1. **查询嵌入**：使用 Longformer 嵌入将输入查询转换为固定大小的向量
2. **距离计算**：计算查询嵌入与所有训练查询嵌入之间的距离
3. **近邻选择**：基于距离度量（欧氏距离、余弦距离等）选择 K 个最接近的历史查询
4. **投票**：K 个近邻为其表现最佳的 LLM 投票（均匀投票或距离加权投票）
5. **选择**：返回得票最多的 LLM

### 关键特性

- **惰性学习**：无训练阶段 — 算法仅存储所有训练样本
- **基于实例**：决策基于局部相似性，而非全局模式
- **非参数化**：不对数据分布做假设
- **可解释性**：可以检查哪些相似查询影响了每个路由决策

### "训练"过程

KNN 没有传统意义上的训练。"训练"步骤仅：
1. 存储来自历史数据的查询嵌入
2. 存储相应的表现最佳的 LLM 标签
3. 构建高效搜索索引（Ball Tree、KD Tree 或暴力搜索）

推理时，直接使用存储的样本进行路由决策。

## 配置参数

### 超参数（配置中的 `hparam`）

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `n_neighbors` | int | `5` | **最重要参数**：考虑的近邻数量（K）。小 K（1-3）→ 对噪声敏感。大 K（10-20）→ 边界平滑但可能错过局部模式。典型范围：3-10。 |
| `weights` | str | `"uniform"` | 投票权重函数。`"uniform"`：所有近邻投票权重相同。`"distance"`：更近的近邻影响更大（权重 = 1/距离）。当近邻样本更可靠时使用 `"distance"`。 |
| `algorithm` | str | `"auto"` | 计算近邻的算法。`"auto"`：自动选择最佳方法。`"ball_tree"`：高维高效。`"kd_tree"`：低维高效。`"brute"`：暴力搜索（慢但始终可用）。 |
| `leaf_size` | int | `30` | Ball Tree 或 KD Tree 的叶子大小。影响树构建的速度和内存。较大值 → 构建更快但查询更慢。典型范围：20-50。 |
| `p` | int | `2` | Minkowski 度量的幂参数。`p=1`：曼哈顿距离（L1）。`p=2`：欧氏距离（L2，推荐）。更高的 p → 关注最大差异。 |
| `metric` | str | `"minkowski"` | 距离度量。选项：`"minkowski"`（通用，与 p 参数配合使用）、`"euclidean"`、`"manhattan"`、`"cosine"`（适合文本嵌入）、`"chebyshev"`。对于文本，考虑 `"cosine"`。 |
| `n_jobs` | int | `-1` | 并行作业数。`-1`：使用所有 CPU 核心。`1`：单线程。更高的值显著加快查询速度。 |

### 数据路径

| 参数 | 描述 |
|-----------|-------------|
| `query_data_train` | JSONL 格式的历史训练查询数据 |
| `routing_data_train` | 历史路由性能数据（查询-LLM 对及其评分） |
| `query_embedding_data` | 预计算的查询嵌入（PyTorch 张量文件） |
| `llm_data` | LLM 候选信息（模型、API 名称、元数据） |

### 模型路径

| 参数 | 用途 | 使用方式 |
|-----------|---------|-------|
| `ini_model_path` | 用于初始化的预训练模型 | 可选：留空则从零构建 |
| `save_model_path` | KNN 模型保存位置 | 训练时：模型（嵌入+标签）保存在此 |
| `load_model_path` | 推理时加载的模型 | 测试时：保存的 `.pkl` 文件路径 |

### 推理/测试参数

推理期间：
- KNN 模型加载存储的嵌入和标签
- 使用与"训练"相同的距离度量和 K 值
- 对每个新查询执行近邻搜索
- 无需重新训练 — 可即时添加新样本

## 命令行使用

KNN 路由器可通过 `llmrouter` 命令行界面使用：

### 训练

```bash
# "训练" KNN 路由器（构建搜索索引）
llmrouter train --router knnrouter --config configs/model_config_train/knnrouter.yaml

# 使用安静模式训练
llmrouter train --router knnrouter --config configs/model_config_train/knnrouter.yaml --quiet
```

### 推理

```bash
# 路由单个查询
llmrouter infer --router knnrouter --config configs/model_config_test/knnrouter.yaml \
    --query "AI 的伦理影响是什么？"

# 从文件路由查询
llmrouter infer --router knnrouter --config configs/model_config_test/knnrouter.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
llmrouter infer --router knnrouter --config configs/model_config_test/knnrouter.yaml \
    --query "解释神经网络" --route-only
```

### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router knnrouter --config configs/model_config_test/knnrouter.yaml

# 使用自定义端口启动
llmrouter chat --router knnrouter --config configs/model_config_test/knnrouter.yaml --port 8080

# 创建公开共享链接
llmrouter chat --router knnrouter --config configs/model_config_test/knnrouter.yaml --share
```

---

## 使用示例

### "训练" KNN 路由器

```python
from llmrouter.models import KNNRouter, KNNRouterTrainer

# 使用训练配置初始化路由器
router = KNNRouter(yaml_path="configs/model_config_train/knnrouter.yaml")

# 创建训练器（实际上只是存储数据）
trainer = KNNRouterTrainer(router=router, device="cpu")

# "训练"模型（构建搜索索引）
trainer.train()
# 模型将保存到 save_model_path 指定的路径
```

**命令行训练：**
```bash
python tests/train_test/test_knnrouter.py --yaml_path configs/model_config_train/knnrouter.yaml
```

### 推理：路由单个查询

```python
from llmrouter.models import KNNRouter

# 使用测试配置初始化路由器（加载存储的样本）
router = KNNRouter(yaml_path="configs/model_config_test/knnrouter.yaml")

# 路由单个查询
query = {"query": "AI 的伦理影响是什么？"}
result = router.route_single(query)

print(f"选定的模型: {result['model_name']}")
```

### 推理：批量路由与 API 执行

```python
from llmrouter.models import KNNRouter

# 初始化路由器
router = KNNRouter(yaml_path="configs/model_config_test/knnrouter.yaml")

# 准备批量查询
queries = [
    {"query": "解释神经网络", "ground_truth": "..."},
    {"query": "调试这段 Python 代码: ...", "ground_truth": "..."}
]

# 路由并执行查询
results = router.route_batch(batch=queries, task_name="general")

for result in results:
    print(f"查询: {result['query']}")
    print(f"路由到: {result['model_name']}")
    print(f"响应: {result['response']}")
    print(f"性能: {result.get('task_performance', 'N/A')}")
    print("-" * 80)
```

### 用于特定任务

```python
# 为基准测试任务路由查询
queries = [
    {
        "query": "原子序数为 6 的元素是什么？",
        "choices": ["A. 氮", "B. 碳", "C. 氧", "D. 氢"],
        "ground_truth": "B"
    }
]

results = router.route_batch(batch=queries, task_name="mmlu")
```

## YAML 配置示例

**训练配置** (`configs/model_config_train/knnrouter.yaml`):

```yaml
data_path:
  query_data_train: 'data/example_data/query_data/default_query_train.jsonl'
  routing_data_train: 'data/example_data/routing_data/default_routing_train_data.jsonl'
  query_embedding_data: 'data/example_data/routing_data/query_embeddings_longformer.pt'
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

model_path:
  ini_model_path: ''  # 留空以从零构建
  save_model_path: 'saved_models/knnrouter/knnrouter.pkl'

hparam:
  n_neighbors: 5        # K 值 - 考虑的近邻数量
  weights: "uniform"    # 投票权重: "uniform" 或 "distance"
  algorithm: "auto"     # 近邻搜索算法
  leaf_size: 30         # 树算法参数
  p: 2                  # 距离度量幂（2 = 欧氏距离）
  metric: "minkowski"   # 距离度量
  n_jobs: -1            # 使用所有 CPU 核心

metric:
  weights:
    performance: 1
    cost: 0
    llm_judge: 0
```

**测试配置** (`configs/model_config_test/knnrouter.yaml`):

```yaml
data_path:
  query_data_test: 'data/example_data/query_data/default_query_test.jsonl'
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

model_path:
  load_model_path: 'saved_models/knnrouter/knnrouter.pkl'

# 与训练相同的超参数
hparam:
  n_neighbors: 5
  weights: "uniform"
  algorithm: "auto"
  metric: "minkowski"
  p: 2
```

## 选择 K (n_neighbors)

K 值对性能有重要影响：

### 小 K (1-3)
- **优点**：捕获局部模式，查询快速
- **缺点**：对噪声和异常值敏感
- **适用场景**：数据干净，需要细粒度区分

### 中等 K (4-10) - **推荐**
- **优点**：在噪声鲁棒性和敏感性之间平衡
- **缺点**：可能模糊决策边界
- **适用场景**：通用路由，典型使用场景

### 大 K (10-30)
- **优点**：对噪声鲁棒，决策边界平滑
- **缺点**：可能错过局部模式，查询较慢
- **适用场景**：噪声数据，需要稳定的预测

### 经验法则
- 从 K = sqrt(N) 开始，其中 N 是训练样本数
- 使用奇数 K 避免平局（例如 3、5、7）
- 使用交叉验证找到最优 K

## 距离度量选择

### 欧氏距离 (`metric="minkowski", p=2`)
- **默认选择**，适用于通用嵌入
- 测量嵌入空间中的直线距离
- 对特征缩放敏感

### 曼哈顿距离 (`metric="minkowski", p=1`)
- 绝对差异之和
- 比欧氏距离对异常值更鲁棒
- 适用于稀疏数据

### 余弦距离 (`metric="cosine"`)
- **推荐用于文本嵌入**
- 测量向量之间的角度，忽略幅度
- 当查询长度变化显著时表现良好

### 其他度量
- `"chebyshev"`：各维度上的最大差异
- `"hamming"`：用于二进制特征
- 自定义度量：可以定义自己的距离函数

## 超参数调优技巧

### 调优 n_neighbors (K)
```python
# 尝试多个 K 值并使用交叉验证
for k in [3, 5, 7, 10, 15]:
    # 使用此 K 评估路由准确率
    # 选择验证性能最佳的 K
```

### 调优 weights
- 当所有近邻同样可信时使用 `"uniform"`
- 当更近的样本应该更重要时使用 `"distance"`
- `"distance"` 通常在 KNN 路由中效果更好

### 调优 algorithm
- `"auto"` 通常就可以了
- 对于大数据集（>10k 样本），尝试 `"ball_tree"`
- 对于低维嵌入（<20 维），尝试 `"kd_tree"`

### 调优 metric
- 对于文本嵌入：首先尝试 `"cosine"`
- 对于归一化嵌入：`"euclidean"` 效果很好
- 在保留集上进行实验和验证

## 优点

- ✅ **无需训练**：仅存储样本，无需优化
- ✅ **增量学习**：可即时添加新样本而无需重新训练
- ✅ **可解释**：可以检查哪些历史查询影响了每个决策
- ✅ **非参数化**：不对数据分布做假设
- ✅ **简单**：易于理解和实现
- ✅ **小数据有效**：即使只有少量训练样本也能工作良好
- ✅ **适应局部模式**：对数据中的局部结构敏感

## 局限性

- ❌ **内存密集**：在内存中存储所有训练样本
- ❌ **推理较慢**：必须计算到所有样本的距离（每个查询 O(N)）
- ❌ **维度诅咒**：在极高维度下性能下降
- ❌ **对无关特征敏感**：所有嵌入维度同等重要
- ❌ **无特征学习**：无法学习哪些特征重要
- ❌ **依赖良好嵌入**：性能严重依赖嵌入质量

## 何时使用 KNN 路由器

**适合的场景：**
- 小到中等数据集（数十到数万个样本）
- 需要快速原型设计而无需训练
- 需要可解释的路由决策
- 数据分布频繁变化（易于更新）
- 需要增量添加新样本
- 用于训练的计算资源有限

**考虑替代方案时：**
- 极大数据集（>10万样本）→ 使用 MLP 或 SVM 路由器
- 具有多个无关特征的高维嵌入→ 先使用降维
- 需要大规模快速推理→ 使用训练模型（MLP/SVM）
- 想要学习复杂模式→ 使用基于神经网络的路由器
- 类别不平衡→ 使用加权 KNN 或其他方法

## 与其他路由器的比较

| 方面 | KNN 路由器 | MLP 路由器 | SVM 路由器 |
|--------|------------|------------|------------|
| 训练时间 | 无（即时） | 分钟到小时 | 分钟 |
| 推理速度 | 慢（O(N)） | 快（O(1)） | 快（O(#支持向量)） |
| 内存使用 | 高（所有数据） | 低（仅权重） | 中（支持向量） |
| 可解释性 | 高 | 低 | 中 |
| 处理非线性 | 是（局部） | 是（层） | 是（核） |
| 增量学习 | 容易 | 困难 | 困难 |
| 小数据性能 | 优秀 | 差 | 良好 |

## 实现细节

- **框架**：scikit-learn 的 `KNeighborsClassifier`
- **嵌入模型**：Longformer（用于查询向量化）
- **输入维度**：由嵌入大小决定（通常为 768 或 1024）
- **输出**：分类预测（LLM 名称作为字符串）
- **序列化**：模型保存为 `.pkl` 文件使用 pickle
- **搜索优化**：使用 Ball Tree 或 KD Tree 进行高效近邻搜索

## 最佳性能技巧

1. **嵌入质量**：
   - 使用领域特定的嵌入（长文本使用 Longformer）
   - KNN 前考虑归一化嵌入
   - 尝试不同的嵌入模型

2. **超参数选择**：
   - 从 K=5、weights="distance"、metric="cosine" 开始
   - 使用交叉验证找到最优 K
   - 为您的数据尝试不同的距离度量

3. **数据预处理**：
   - 删除重复查询
   - 过滤噪声或标记错误的样本
   - 尽可能平衡类别分布

4. **扩展**：
   - 对于大数据集，使用 `algorithm="ball_tree"`
   - 设置 `n_jobs=-1` 使用所有 CPU 核心
   - 如果数据集非常大，考虑采样

5. **增量更新**：
   - 易于添加新样本：只需追加到训练数据并重新保存
   - 无需昂贵的重新训练
   - 非常适合持续学习场景

## 高级用法

### 距离加权投票

```yaml
hparam:
  n_neighbors: 5
  weights: "distance"  # 更近的近邻影响更大
  metric: "cosine"     # 适合文本嵌入
```

### 自定义距离度量

对于专门的路由需求，可以定义自定义距离函数并通过扩展 scikit-learn 接口与 KNN 路由器一起使用。

### 处理不平衡类别

如果某些 LLM 在训练数据中出现得更频繁：
- 使用 `weights="distance"` 给予更近的样本更多影响
- 考虑分层采样以平衡类别
- 使用类别加权投票（需要自定义实现）

## 相关路由器

- **KNN 多轮路由器**：扩展 KNN 用于多轮对话
- **MLP 路由器**：具有更快推理的参数化替代方案
- **SVM 路由器**：具有更好可扩展性的基于核的替代方案
- **混合路由器**：将 KNN 与其他路由方法结合

---

如有问题或建议，请参考 LLMRouter 主文档或在 GitHub 上提交 issue。
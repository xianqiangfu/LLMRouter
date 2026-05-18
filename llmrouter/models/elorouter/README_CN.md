# ELO 路由器

## 概述

**ELO 路由器**是一种基于评分的路由方法，使用最初为国际象棋设计的 Elo 评分系统对 LLM 进行排名。它将历史性能数据转换为成对比较，并计算全局排名。所有查询都被路由到单个评分最高的 LLM。

## 论文参考

该路由器的灵感来自 **Elo 评分系统**和 **RouteLLM**：

- **[RouteLLM: Learning to Route LLMs with Preference Data](https://arxiv.org/abs/2406.18665)**
  - Ong, I., et al. (2024). arXiv:2406.18665. 发表于 ICLR 2025。
  - 使用加权 Elo 计算实现 `sw_ranking` 路由器。

- **原始 Elo 系统**：
  - Elo, A. E. (1978). "The Rating of Chessplayers, Past and Present." Arco Publishing.

- **在 LLM 中的应用**：
  - Zheng, L., et al. (2023). "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." NeurIPS.
  - Bradley-Terry 模型：Bradley, R. A., & Terry, M. E. (1952). "Rank Analysis of Incomplete Block Designs." Biometrika.

## 工作原理

### 架构

```
历史数据 → 成对战 → Elo 计算 → 单个最佳模型选择
            (胜者/败者)    (逻辑回归最大似然估计)
```

### 路由机制

1. **训练阶段**：
   - 对于训练数据中的每个查询，确定表现最佳的 LLM
   - 创建成对"对决"：胜者（最佳 LLM）与每个败者（其他 LLM）
   - 使用逻辑回归通过最大似然估计估计 Elo 分数
   - 将 Elo 分数保存到磁盘

2. **推理阶段**：
   - 加载预先计算的 Elo 分数
   - **始终选择具有最高 Elo 评分的 LLM**
   - 将所有查询路由到这个单一模型（与查询无关的路由）

### 关键特征

- **全局排名**：为每个 LLM 计算单一的全局评分
- **与查询无关**：与 KNN/MLP/SVM 不同，在推理过程中忽略查询内容
- **成对比较**：基于相对性能，而非绝对分数
- **统计基础**：基于 Bradley-Terry 模型和最大似然估计

### Elo 计算公式

对于每个成对战（模型 A 对模型 B）：

```
P(A 获胜) = 1 / (1 + 10^((Rating_B - Rating_A) / 400))
```

训练器使用逻辑回归来找到使观察到的对战结果似然度最大的 Elo 评分。

## 训练过程

### 1. 构建对战数据

对于每个查询：
- 确定表现最佳的模型（胜者）
- 创建对战：胜者对所有其他模型（败者）
- 生成对称对战（A 对 B 和 B 对 A）以实现平衡训练

示例：
```
查询："解释重力"
性能：GPT-4 (0.95), Claude (0.85), Llama (0.70)

创建的对战：
  GPT-4 对 Claude → GPT-4 获胜
  GPT-4 对 Llama  → GPT-4 获胜
  Claude 对 GPT-4 → Claude 失败
  Llama 对 GPT-4  → Llama 失败
```

### 2. 估计 Elo 分数

使用逻辑回归最大似然估计找到最能解释对战结果的 Elo 评分：
- 将所有模型初始化为 1000 评分
- 拟合逻辑回归以预测对战胜者
- 将系数转换为 Elo 分数（按 400 缩放）

### 3. 保存排名

将 Elo 分数保存为字典：`{"GPT-4": 1250, "Claude": 1180, "Llama": 950}`

## 配置参数

### 训练参数

无需调优超参数！给定训练数据，Elo 计算是确定性的。

**固定常量**（在训练器代码中）：
- `SCALE`: 400.0 - 标准 Elo 缩放因子
- `BASE`: 10.0 - Elo 概率基数
- `INIT_RATING`: 1000.0 - 所有模型的初始评分

### 数据路径

| 参数 | 描述 |
|-----------|-------------|
| `query_data_train` | JSONL 格式的训练查询 |
| `routing_data_train` | 历史路由性能数据（查询-LLM 对及其性能分数） |
| `llm_data` | LLM 候选信息（模型、API 名称、元数据） |

### 模型路径

| 参数 | 用途 | 使用方式 |
|-----------|---------|-------|
| `save_model_path` | 保存计算出的 Elo 分数的位置 | 训练：保存 `{model_name: elo_score}` 字典 |
| `load_model_path` | 要加载以进行推理的 Elo 分数 | 测试：保存的 `.pkl` 文件的路径 |

### 推理参数

在推理过程中：
- 从 `load_model_path` 加载 Elo 分数
- 选择评分最高的模型
- 将**所有查询**路由到这个单一模型
- 没有特定于查询的路由决策

## CLI 使用

ELO 路由器可以通过 `llmrouter` 命令行界面使用：

### 训练

```bash
# 计算 Elo 排名
llmrouter train --router elorouter --config configs/model_config_train/elorouter.yaml

# 使用静默模式训练
llmrouter train --router elorouter --config configs/model_config_train/elorouter.yaml --quiet
```

### 推理

```bash
# 路由单个查询（始终选择评分最高的模型）
llmrouter infer --router elorouter --config configs/model_config_test/elorouter.yaml \
    --query "生命的意义是什么？"

# 从文件路由查询
llmrouter infer --router elorouter --config configs/model_config_test/elorouter.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
llmrouter infer --router elorouter --config configs/model_config_test/elorouter.yaml \
    --query "解释量子力学" --route-only
```

### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router elorouter --config configs/model_config_test/elorouter.yaml

# 使用自定义端口启动
llmrouter chat --router elorouter --config configs/model_config_test/elorouter.yaml --port 8080

# 创建可公开分享的链接
llmrouter chat --router elorouter --config configs/model_config_test/elorouter.yaml --share
```

---

## 使用示例

### 训练 ELO 路由器

```python
from llmrouter.models import EloRouter, EloRouterTrainer

# 使用训练配置初始化路由器
router = EloRouter(yaml_path="configs/model_config_train/elorouter.yaml")

# 创建训练器
trainer = EloRouterTrainer(router=router, device="cpu")

# 计算 Elo 分数
trainer.train()
# Elo 分数将保存到 save_model_path 指定的路径

# 查看计算出的排名
print("Elo 排名:")
for model, score in sorted(router.elo_scores.items(), key=lambda x: -x[1]):
    print(f"  {model}: {score:.2f}")
```

**命令行训练：**
```bash
python tests/train_test/test_elorouter.py --yaml_path configs/model_config_train/elorouter.yaml
```

### 推理：路由查询

```python
from llmrouter.models import EloRouter

# 使用测试配置初始化路由器（加载 Elo 分数）
router = EloRouter(yaml_path="configs/model_config_test/elorouter.yaml")

# 路由单个查询
query = {"query": "生命的意义是什么？"}
result = router.route_single(query)

print(f"选择的模型: {result['model_name']}")
# 注意：这将始终是同一个模型（Elo 评分最高）
```

### 带有 API 执行的批量路由

```python
from llmrouter.models import EloRouter

# 初始化路由器
router = EloRouter(yaml_path="configs/model_config_test/elorouter.yaml")

# 准备批量查询
queries = [
    {"query": "解释量子力学", "ground_truth": "..."},
    {"query": "写一首关于 AI 的诗", "ground_truth": "..."},
    {"query": "解方程 x^2 + 5x + 6 = 0", "ground_truth": "..."}
]

# 路由并执行（所有查询都路由到同一个最佳模型）
results = router.route_batch(batch=queries, task_name="general")

# 所有查询都路由到同一个模型
unique_models = set(r['model_name'] for r in results)
print(f"使用的不同模型数量: {len(unique_models)}")  # 始终为 1
```

## YAML 配置示例

**训练配置** (`configs/model_config_train/elorouter.yaml`)：

```yaml
data_path:
  query_data_train: 'data/example_data/query_data/default_query_train.jsonl'
  routing_data_train: 'data/example_data/routing_data/default_routing_train_data.jsonl'
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

model_path:
  ini_model_path: ''
  save_model_path: 'saved_models/elorouter/elorouter.pkl'

metric:
  weights:
    performance: 1    # 确定胜者的主要标准
    cost: 0
    llm_judge: 0
```

**测试配置** (`configs/model_config_test/elorouter.yaml`)：

```yaml
data_path:
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

model_path:
  load_model_path: 'saved_models/elorouter/elorouter.pkl'
```

## 优势

- ✅ **简单且可解释**：单一全局排名，易于理解
- ✅ **统计基础扎实**：基于 Bradley-Terry 模型和最大似然估计
- ✅ **无超参数**：无需调优，完全确定性
- ✅ **处理不平衡比较**：Elo 自然处理每个模型的不同对战次数
- ✅ **经过实战检验**：在国际象棋、体育和现在的 LLM 排行榜中使用的成熟系统
- ✅ **快速推理**：只需字典查找（O(1)）

## 限制

- ❌ **与查询无关**：忽略查询内容，始终路由到同一个模型
- ❌ **无专业化**：无法利用特定查询类型的模型优势
- ❌ **单一模型**：无法分配负载或使用集成
- ❌ **假设传递性**：假设如果 A > B 且 B > C，则 A > C（对于 LLM 可能不成立）
- ❌ **静态排名**：必须重新训练以更新 Elo 分数
- ❌ **无成本-性能权衡**：无论成本如何，始终选择评分最高的模型
- ❌ **数据需求大**：需要足够的成对比较才能获得准确的排名

## 何时使用 ELO 路由器

**适用场景：**
- 想要一个始终使用"最佳"模型的简单基线
- 需要 LLM 能力的全局排名
- 拥有大量具有一致评估指标的训练数据
- 不需要特定于查询的路由（所有查询都相似）
- 想要可解释、可解释的路由（只需显示 Elo 排名）

**不推荐使用：**
- 查询类型多样（编码、数学、创意写作等）
- 需要优化成本（Elo 始终选择评分最高的，通常是最昂贵的模型）
- 想要利用专业化的模型优势
- 需要在多个模型之间分配负载
- 训练数据有限

## 理解 Elo 分数

### 解释

```
Elo 分数    含义
---------    -------
1400+        主导模型，赢得大多数对战
1200-1400    强大模型，有竞争力
1000-1200    平均模型，表现混合
800-1000     弱模型，输掉大多数对战
<800         非常弱的模型，很少获胜
```

### Elo 差异和获胜概率

```
Elo 差异     预期胜率
--------     -----------------
0            50%
100          64%
200          76%
400          91%
```

如果模型 A 的 Elo 为 1200，模型 B 的 Elo 为 1000（差值 = 200），模型 A 预期会在约 76% 的对战中获胜。

## 与其他路由器的比较

| 方面 | ELO 路由器 | KNN 路由器 | MLP/SVM 路由器 |
|--------|------------|------------|----------------|
| 查询特定 | ❌ 否 | ✅ 是 | ✅ 是 |
| 训练速度 | 快 | 无 | 中等 |
| 推理速度 | 瞬时 | 中等 | 快 |
| 可解释性 | 高（排名） | 高（邻居） | 低 |
| 模型多样性 | 单个模型 | 多个模型 | 多个模型 |
| 超参数 | 无 | 少 | 多 |
| 数据效率 | 中等 | 高 | 中等 |

## 实现细节

- **框架**：使用 scikit-learn 的 LogisticRegression 的自定义实现
- **对战生成**：对称对战（A 对 B 和 B 对 A）以实现平衡训练
- **MLE 求解器**：用于逻辑回归的 LBFGS 优化器
- **输出**：将模型名称映射到 Elo 分数的字典
- **序列化**：使用 pickle 保存为 `.pkl` 文件

## 最佳性能技巧

1. **训练数据质量**：
   - 确保性能指标可靠且一致
   - 包含多样化的查询以避免偏差
   - 需要足够的查询（建议 50+）以获得稳定的排名

2. **性能指标选择**：
   - 使用 `metric.weights.performance = 1` 进行基于准确性的排名
   - 如需要可以包含成本（但会破坏纯排名的目的）
   - 确保指标在不同查询类型之间具有可比性

3. **模型池**：
   - 最适合 3-10 个模型
   - 模型太少 → 路由价值有限
   - 模型太多 → 每对的对战数据稀疏

4. **重新训练策略**：
   - 随着新数据的到来定期重新训练
   - 监控模型能力是否随时间变化
   - 向池中添加新模型时更新

5. **用作基线**：
   - ELO 路由器是用于比较的出色基线
   - 将查询特定路由器与 ELO 进行比较，以衡量个性化的价值

## 与 Chatbot Arena 的关系

该路由器直接受到 **Chatbot Arena** (LMSYS) 的启发：
- Chatbot Arena 使用 Elo 评分根据人类偏好对 LLM 进行排名
- 用户对成对比较进行投票 → 计算 Elo 分数
- 创建公共 LLM 排行榜

**主要区别**：
- Chatbot Arena：人类偏好对战
- ELO 路由器：自动化性能指标对战

## 高级用法

### 自定义 Elo 参数

虽然默认参数效果很好，但可以在 `trainer.py` 中修改 Elo 常量：

```python
# 更大的 SCALE → 更大的评分差异
elo_scores = compute_elo_mle(battles_df, SCALE=500.0, BASE=10.0, INIT_RATING=1500.0)
```

### 考虑成本

可以修改对战生成以考虑成本调整后的性能：

```python
# 在自定义训练器中
df["adjusted_performance"] = df["performance"] / (df["cost"] ** 0.5)
# 然后使用 adjusted_performance 来确定胜者
```

### 多指标 Elo

为不同指标（准确性、速度、成本效率）计算单独的 Elo 排名，并将它们结合起来。

## 相关路由器

- **最大 LLM 路由器**：始终选择最大的模型（更简单的启发式）
- **最小 LLM 路由器**：始终选择最小的模型（专注于成本）
- **混合 LLM 路由器**：多种路由策略的加权组合
- **矩阵分解路由器**：学习查询-模型亲和度（查询特定的替代方案）

---

如有问题或建议，请参考 LLMRouter 主文档或在 GitHub 上提交 issue。
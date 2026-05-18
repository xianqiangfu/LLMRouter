# Automix 路由器

## 概述

**Automix 路由器**是一种经济高效的路由方法，它使用自验证来决定何时将查询从小型、廉价的语言模型升级到更强大（但也更昂贵）的大型模型。它采用自一致性验证来评估小模型的置信度，然后决定是否需要进行升级。

## 论文参考

本路由器实现了以下论文中的 **Automix** 框架：

- **[AutoMix: Automatically Mixing Language Models](https://arxiv.org/abs/2310.12963)**
  - Aggarwal, P., Madaan, A., et al. (2023). arXiv:2310.12963. 发表于 NeurIPS 2024。
  - 提出了自验证和基于 POMDP 的路由方法，用于实现经济高效的 LLM 选择。

Automix 方法基于一个观察：许多查询可以由小型模型有效处理，昂贵的大型模型应仅在必要时使用。

## 工作原理

### 架构

```
Query → 小型模型 → 自验证 → 决策 → [保留或升级到大型模型]
                      (置信度分数)    (POMDP/阈值/自一致性)
```

### 路由机制

1. **初始响应**：查询首先发送到小型、经济高效的 LLM
2. **自验证**：小模型生成多个验证样本以评估其自身答案的置信度
3. **置信度评分**：根据验证样本的一致性计算验证分数
4. **路由决策**：基于验证分数，路由器决定：
   - **高置信度** → 使用小模型的答案（经济高效）
   - **低置信度** → 升级到大型模型（质量优先）
5. **最终响应**：返回小模型的答案或大型模型的答案

### 路由方法

Automix 支持三种路由策略：

#### 1. 阈值方法
- **决策规则**：如果 `p_ver_slm < threshold`，则路由到大型模型
- **特点**：简单、确定性
- **适用场景**：具有明确置信度边界的情况

#### 2. POMDP（部分可观察马尔可夫决策过程）
- **决策规则**：使用动态规划优化期望奖励
- **特点**：在成本约束下理论最优
- **适用场景**：需要在质量和成本之间平衡并获得形式化保证的情况

#### 3. 自一致性
- **决策规则**：基于多个样本之间的答案熵进行路由
- **特点**：衡量响应的多样性
- **适用场景**：检测模型不确定性的情况

### 自验证过程

验证过程如下：

1. 使用小模型生成答案：`answer_small`
2. 让小模型验证自己的答案（N 次采样）
3. 解析验证响应（例如，"True" 或 "False"）
4. 计算验证分数：`p_ver = 正确验证的比例`
5. 使用 `p_ver` 作为路由决策的置信度信号

## 配置参数

### 训练超参数（配置中的 `hparam`）

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `routing_method` | str | `"POMDP"` | 路由策略。选项：`"Threshold"`、`"POMDP"`、`"SelfConsistency"`。推荐使用 POMDP 以获得最佳成本-性能权衡。 |
| `num_bins` | int | `8` | 用于离散化验证分数的箱数（POMDP 使用）。值越高精度越高，但优化速度越慢。 |
| `small_model_cost` | float | `1` | 调用小模型的相对成本。用于成本效益分析。 |
| `large_model_cost` | float | `50` | 调用大型模型的相对成本。通常是小模型成本的 10-100 倍。 |
| `verifier_cost` | float | `1` | 运行验证的成本（通常与小模型成本类似）。 |
| `verbose` | bool | `true` | 是否在训练/推理期间打印详细输出。 |
| `cost_constraint` | tuple/null | `null` | 可选的 (min_cost, max_cost) 元组，用于约束路由决策。 |
| `max_workers` | int | `1` | API 调用的并行工作线程数。增加此值可加快处理速度（推荐 5-10）。 |
| `device` | str | `"cpu"` | 计算设备：`"cpu"` 或 `"cuda"`。 |

### 数据路径

| 参数 | 描述 |
|-----------|-------------|
| `routing_data_train` | 包含查询-LLM 性能对的训练数据（JSONL 格式） |
| `routing_data_test` | 用于评估的测试数据 |
| `llm_data` | 包含模型大小信息的 LLM 候选信息（JSON） |

**注意**：Automix 会根据 `llm_data` 中的 `size` 字段自动检测最小和最大的模型。

### 模型路径

| 参数 | 用途 | 使用场景 |
|-----------|---------|-------|
| `save_model_path` | 保存训练的路由策略的位置 | 训练：保存学习到的 POMDP 策略或阈值 |
| `load_model_path` | 加载用于推理的模型 | 测试：加载训练好的路由策略 |

### 推理参数

推理期间：
- 首先为每个查询调用小模型
- 执行自验证以获得置信度分数
- 应用学习到的路由策略决定是否升级
- 如需要则调用大型模型
- 不调整超参数

## CLI 使用

Automix 路由器可以通过 `llmrouter` 命令行界面使用：

### 训练

```bash
# 训练 Automix 路由器（学习最优路由策略）
llmrouter train --router automix --config configs/model_config_train/automix.yaml

# 以静默模式训练
llmrouter train --router automix --config configs/model_config_train/automix.yaml --quiet
```

### 推理

```bash
# 路由单个查询（使用自验证 + POMDP 策略）
llmrouter infer --router automix --config configs/model_config_test/automix.yaml \
    --query "Solve x^2 + 5x + 6 = 0"

# 路由文件中的查询
llmrouter infer --router automix --config configs/model_config_test/automix.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
llmrouter infer --router automix --config configs/model_config_test/automix.yaml \
    --query "Explain quantum entanglement" --route-only
```

### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router automix --config configs/model_config_test/automix.yaml

# 使用自定义端口启动
llmrouter chat --router automix --config configs/model_config_test/automix.yaml --port 8080

# 创建公共可分享链接
llmrouter chat --router automix --config configs/model_config_test/automix.yaml --share
```

---

## 使用示例

### 训练 Automix 路由器

```python
from llmrouter.models import AutomixRouter, AutomixTrainer

# 使用训练配置初始化路由器
router = AutomixRouter(yaml_path="configs/model_config_train/automix.yaml")

# 创建训练器
trainer = AutomixTrainer(router=router, device="cpu")

# 训练路由策略（学习最优阈值或 POMDP 策略）
trainer.train()
# 策略将保存到 save_model_path 指定的路径
```

**命令行训练：**
```bash
python tests/train_test/test_automix.py --yaml_path configs/model_config_train/automix.yaml
```

### 推理：路由单个查询

```python
from llmrouter.models import AutomixRouter

# 使用测试配置初始化路由器（加载训练好的策略）
router = AutomixRouter(yaml_path="configs/model_config_test/automix.yaml")

# 路由单个查询
query = {"query": "What is the capital of France?"}
result = router.route_single(query)

print(f"使用的模型: {result['model_name']}")
print(f"响应: {result['response']}")
print(f"验证分数: {result['verification_score']}")
print(f"路由到大型模型: {result['route_to_llm']}")
```

### 推理：带 API 执行的批量路由

```python
from llmrouter.models import AutomixRouter

# 初始化路由器
router = AutomixRouter(yaml_path="configs/model_config_test/automix.yaml")

# 准备批量查询
queries = [
    {"query": "Solve x^2 + 5x + 6 = 0", "ground_truth": "x = -2 or x = -3"},
    {"query": "Explain quantum entanglement", "ground_truth": "..."},
    {"query": "Write a Python function to reverse a string", "ground_truth": "..."}
]

# 路由并执行查询
results = router.route_batch(batch=queries, task_name="general")

for result in results:
    print(f"查询: {result['query']}")
    print(f"使用的模型: {result['model_name']}")
    print(f"响应: {result['response']}")
    print(f"验证分数: {result['verification_score']}")
    print(f"已升级: {result['route_to_llm']}")
    print(f"性能: {result.get('task_performance', 'N/A')}")
    print("-" * 80)
```

## YAML 配置示例

**训练配置** (`configs/model_config_train/automix.yaml`)：

```yaml
data_path:
  routing_data_train: 'data/example_data/routing_data/default_routing_train_data.jsonl'
  routing_data_test: 'data/example_data/routing_data/default_routing_test_data.jsonl'
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

model_path:
  save_model_path: 'saved_models/automix/automix_model.pkl'

hparam:
  routing_method: "POMDP"      # 推荐用于最佳性能
  num_bins: 8                  # 离散化粒度
  small_model_cost: 1          # 小模型的成本
  large_model_cost: 50         # 大型模型的成本（贵 50 倍）
  verifier_cost: 1             # 验证的成本
  verbose: true
  max_workers: 5               # 并行 API 调用以加快速度

metric:
  weights:
    performance: 1
    cost: 0
    llm_judge: 0
```

**测试配置** (`configs/model_config_test/automix.yaml`)：

```yaml
data_path:
  query_data_test: 'data/example_data/query_data/default_query_test.jsonl'
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

model_path:
  load_model_path: 'saved_models/automix/automix_model.pkl'

hparam:
  routing_method: "POMDP"
  num_bins: 8
  small_model_cost: 1
  large_model_cost: 50
  verifier_cost: 1
  max_workers: 5
```

## 优势

- ✅ **经济高效**：尽可能使用小型模型，最大限度地减少昂贵的大型模型 API 调用
- ✅ **质量感知**：通过将不确定的查询升级到大型模型来保持高质量
- ✅ **自验证**：使用模型自身的置信度，无需外部分类器
- ✅ **理论基础**：POMDP 方法在成本约束下提供最优路由
- ✅ **自动模型选择**：从配置中自动检测小模型和大模型
- ✅ **灵活的方法**：三种路由策略适用于不同场景

## 限制

- ❌ **双模型约束**：仅在两个模型之间路由（最小和最大）
- ❌ **验证开销**：自验证需要额外的 API 调用（2+ 个样本）
- ❌ **二元决策**：要么使用小模型，要么使用大型模型，没有中间选项
- ❌ **假设自我意识**：依赖于模型准确评估自身的置信度
- ❌ **冷启动**：需要包含两个模型性能指标的训练数据
- ❌ **API 依赖**：需要通过 API 访问小模型和大型模型

## 何时使用 Automix 路由器

**适用场景：**
- 成本敏感的应用程序，LLM API 成本是关注重点
- 难度混合的工作负载（有些查询简单，有些困难）
- 您可以通过 API 访问小模型和大型模型
- 需要在质量和成本之间动态平衡
- 希望采用原则性的模型选择方法

**考虑其他方案的情况：**
- 需要在 3+ 个模型之间路由 → 使用 MLP/SVM/KNN 路由器
- 所有查询难度相似 → 使用单个模型
- 无法承担验证开销 → 使用 ELO 路由器或静态选择
- 无法访问小模型 → 使用最大 LLM 路由器
- 需要最大质量而不考虑成本 → 使用最大 LLM 路由器

## 性能优化建议

1. **模型选择**：
   - 选择具有明显能力差距的小模型和大模型（例如，3B vs 70B）
   - 确保小模型的成本比大型模型低 10-100 倍
   - 验证模型可以通过相同的 API 访问

2. **路由方法选择**：
   - **POMDP**：最适合最优的成本-性能平衡
   - **阈值**：最适合简单、可解释的路由
   - **自一致性**：当验证不可靠时最佳

3. **超参数调优**：
   - 调整 `small_model_cost` 和 `large_model_cost` 以反映实际的 API 成本
   - 增加 `num_bins`（到 16-32）以获得更精确的 POMDP 优化
   - 如果验证使用不同的设置，请调优 `verifier_cost`

4. **数据准备**：
   - 确保训练数据具有多样化的查询难度
   - 包含真实答案以进行准确的性能评估
   - 如果使用多种路由方法，预计算查询嵌入

5. **优化**：
   - 增加 `max_workers`（5-10）以加快并行 API 调用
   - 使用 `cost_constraint` 来强制执行预算限制
   - 监控路由百分比（目标为 20-40% 的升级以获得良好平衡）

## 实现细节

- **框架**：基于 Automix 论文的自定义实现
- **路由方法**：阈值、POMDP（动态规划）、自一致性
- **验证**：自一致性采样（默认 n=2）
- **模型检测**：基于 `llm_data` 中的 `size` 字段自动检测
- **序列化**：使用 pickle 将模型保存为 `.pkl` 文件

## 相关路由器

- **混合 LLM 路由器**：类似的成本-质量权衡，但使用学习到的 MLP 预测器
- **最小 LLM 路由器**：始终使用最小模型（最大化成本节省）
- **最大 LLM 路由器**：始终使用最大模型（最大化质量）
- **MLP/SVM/KNN 路由器**：在多个模型之间路由（不仅仅是 2 个）

---

如有问题或建议，请参考 LLMRouter 主文档或在 GitHub 上提交 issue。
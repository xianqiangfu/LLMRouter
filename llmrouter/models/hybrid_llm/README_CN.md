# Hybrid LLM 路由器

## 概述

**Hybrid LLM 路由器**通过学习预测小模型（便宜）何时能够提供足够质量，智能地在小模型和大模型（昂贵）之间进行平衡。它使用 MLP 回归估计质量差距，并基于成本-质量权衡做出路由决策。

## 论文参考

基于 **Hybrid LLM** 方法：

- **[Hybrid LLM: Cost-Efficient and Quality-Aware Query Routing](https://arxiv.org/abs/2404.14618)**
  - Ding, Y., et al. (2024). arXiv:2404.14618.
  - 提出基于 MLP 的质量差距预测，实现成本感知的路由。

- **核心思想**：当质量差距较小时路由到小模型，否则路由到大模型。

## 工作原理

### 架构

```
查询 → Longformer 嵌入 → MLP 回归器 → 质量差距分数 → 路由决策
                                                        ↓
                                        (与阈值比较)
                                                        ↓
                                    小模型（分数 ≥ 阈值）
                                    大模型（分数 < 阈值）
```

### 路由模式

路由器支持三种决策策略：

#### 1. 确定性模式
- 标签：如果 `q(Small) ≥ q(Large)`，则 `y = 1`，否则 `y = 0`
- 决策：如果 `score ≥ 0.5`，则路由到小模型

#### 2. 概率模式
- 标签：`y = sigmoid((q(Small) - q(Large)) / tau)`
- 基于质量差距的软标签
- 比硬二值分类更细致

#### 3. 变换模式
- 找到最大化标签分离的最优阈值 `t*`
- 标签：如果 `q(Small) ≥ q(Large) - t*`，则 `y = 1`
- 自动平衡类别

## 配置参数

### 路由器配置

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `router_mode` | str | `"deterministic"` | 模式：`"deterministic"`、`"probabilistic"` 或 `"transformed"` |
| `router_tau` | float | `0.1` | 概率模式的温度参数 |
| `router_threshold` | float | `0.5` | 决策阈值 |

### MLP 超参数 (`hparam`)

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `hidden_layer_sizes` | list[int] | `[128, 64]` | MLP 架构 |
| `activation` | str | `"relu"` | 激活函数 |
| `solver` | str | `"adam"` | 优化器 |
| `max_iter` | int | `300` | 训练迭代次数 |

## CLI 使用方法

Hybrid LLM 路由器可以通过 `llmrouter` 命令行界面使用：

### 训练

```bash
# 训练 Hybrid LLM 路由器
llmrouter train --router hybrid_llm --config configs/model_config_train/hybrid_llm.yaml

# 使用安静模式训练
llmrouter train --router hybrid_llm --config configs/model_config_train/hybrid_llm.yaml --quiet
```

### 推理

```bash
# 路由单个查询
llmrouter infer --router hybrid_llm --config configs/model_config_test/hybrid_llm.yaml \
    --query "What is photosynthesis?"

# 从文件路由查询
llmrouter infer --router hybrid_llm --config configs/model_config_test/hybrid_llm.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
llmrouter infer --router hybrid_llm --config configs/model_config_test/hybrid_llm.yaml \
    --query "Explain neural networks" --route-only
```

### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router hybrid_llm --config configs/model_config_test/hybrid_llm.yaml

# 使用自定义端口启动
llmrouter chat --router hybrid_llm --config configs/model_config_test/hybrid_llm.yaml --port 8080

# 创建可公开分享的链接
llmrouter chat --router hybrid_llm --config configs/model_config_test/hybrid_llm.yaml --share
```

---

## 使用示例

### 训练

```python
from llmrouter.models import HybridLLMRouter, HybridLLMTrainer

router = HybridLLMRouter(yaml_path="configs/model_config_train/hybrid_llm.yaml")
trainer = HybridLLMTrainer(router=router)
trainer.train()
```

### 推理

```python
from llmrouter.models import HybridLLMRouter

router = HybridLLMRouter(yaml_path="configs/model_config_test/hybrid_llm.yaml")
result = router.route_single({"query": "What is photosynthesis?"})

print(f"Routed to: {result['model_name']}")
print(f"Router Score: {result['router_score']}")  # 预测的质量差距
```

## YAML 配置示例

```yaml
router_mode: "probabilistic"
router_tau: 0.1
router_threshold: 0.5

hparam:
  hidden_layer_sizes: [128, 64]
  activation: relu
  solver: adam
  max_iter: 300

model_path:
  save_model_path: "saved_models/hybrid_llm/hybrid_trained.pkl"
```

## 优势

- ✅ **成本-质量平衡**：优化成本与性能之间的权衡
- ✅ **学习型策略**：适应数据模式
- ✅ **多种模式**：针对不同用例提供三种策略
- ✅ **双模型专注**：比多模型路由更简单

## 局限性

- ❌ **仅支持两个模型**：仅在两个模型（小模型和大模型）之间路由
- ❌ **需要两者数据**：需要包含两个模型性能的历史数据
- ❌ **模型选择**：自动选择最小和最大的模型（无法手动控制）
- ❌ **需要训练**：监督学习方法

## 适用场景

**适合：**
- 有明确的小-大模型对（例如 3B vs 70B）
- 希望优化成本-质量权衡
- 有包含两个模型性能的训练数据
- 二元路由决策可接受

**替代方案：**
- 3+ 个模型 → MLP/SVM/KNN 路由器
- 无训练数据 → Automix 路由器（自验证）
- 始终使用小模型 → 最小 LLM 路由器
- 始终使用大模型 → 最大 LLM 路由器

## 相关路由器

- **Automix 路由器**：类似的成本-质量目标，但使用自验证
- **最小/最大 LLM 路由器**：极端版本（始终使用一个模型）
- **MLP 路由器**：通用多类分类器

---

如有疑问或问题，请参考 LLMRouter 主文档或在 GitHub 上提出 issue。

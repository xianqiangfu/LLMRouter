# 最小 LLM 路由器

## 概述

**最小 LLM 路由器**是一个简单的启发式路由器，总是根据模型大小选择最小的可用 LLM。它优先考虑成本效率而非性能，非常适合对成本敏感的应用程序。

## 论文参考

此路由器是以下论文中描述的基线方法：

- **[GraphRouter: A Graph-based Router for LLM Selections](https://arxiv.org/abs/2410.03834)**
  - (2024). arXiv:2410.03834.
  - 使用最小/最大 LLM 作为路由方法的基线比较。

## 工作原理

### 路由逻辑

1. 从 `llm_data` 加载所有 LLM
2. 筛选大小以 'B' 结尾的模型（数十亿参数）
3. 解析大小（例如，"7B" → 7.0, "70B" → 70.0）
4. 选择最小的模型
5. 将所有查询路由到这一个模型

### 无需训练

这是一个零样本启发式方法——无需训练。

## 配置

只需要包含模型大小的 `llm_data`：

```json
{
  "Qwen2.5-3B": {"size": "3B", "model": "qwen/qwen2.5-3b-instruct"},
  "Qwen2.5-7B": {"size": "7B", "model": "qwen/qwen2.5-7b-instruct"},
  "Llama-70B": {"size": "70B", "model": "meta/llama-3.1-70b-instruct"}
}
```

路由器将选择 "Qwen2.5-3B"（最小）。

## CLI 使用

最小 LLM 路由器可以通过 `llmrouter` 命令行界面使用：

### 推理

> **注意**：此路由器不需要训练——它是一个零样本启发式方法。

```bash
# 路由单个查询（总是选择最小模型）
llmrouter infer --router smallest_llm --config configs/model_config_test/smallest_llm.yaml \
    --query "What is machine learning?"

# 从文件路由查询
llmrouter infer --router smallest_llm --config configs/model_config_test/smallest_llm.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
llmrouter infer --router smallest_llm --config configs/model_config_test/smallest_llm.yaml \
    --query "Explain neural networks" --route-only
```

### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router smallest_llm --config configs/model_config_test/smallest_llm.yaml

# 使用自定义端口启动
llmrouter chat --router smallest_llm --config configs/model_config_test/smallest_llm.yaml --port 8080

# 创建公共可共享链接
llmrouter chat --router smallest_llm --config configs/model_config_test/smallest_llm.yaml --share
```

---

## 使用

```python
from llmrouter.models import SmallestLLM

router = SmallestLLM(yaml_path="configs/model_config_test/smallest_llm.yaml")

# 所有查询都路由到最小模型
queries = [
    {"query": "简单问题"},
    {"query": "需要推理的复杂问题"}
]

results = router.route_batch(queries)
# 两者都使用同一个最小模型
```

## 优势

- ✅ **最大成本节约**：总是使用最便宜的模型
- ✅ **简单**：无需训练，无需超参数
- ✅ **快速**：即时路由决策
- ✅ **可预测**：确定性行为

## 限制

- ❌ **忽略查询难度**：平等对待所有查询
- ❌ **可能牺牲质量**：小模型可能表现不佳
- ❌ **无法适应**：无法通过数据改进
- ❌ **单一模型**：无负载均衡

## 何时使用

**适用于：**
- 极端成本限制
- 查询大多简单
- 用于比较的基线
- 使用廉价模型进行开发/测试

**替代方案：**
- 需要质量 → 最大 LLM 路由器
- 平衡成本和质量 → 混合 LLM 路由器
- 查询特定 → KNN/MLP/SVM 路由器

## 相关路由器

- **最大 LLM 路由器**：相反策略（最大质量）
- **混合 LLM 路由器**：平衡小模型和大模型
- **ELO 路由器**：数据驱动的单模型选择

---

如有疑问或问题，请参考 LLMRouter 主文档或在 GitHub 上提出 issue。
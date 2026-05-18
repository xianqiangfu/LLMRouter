# 最大 LLM 路由器

## 概述

**最大 LLM 路由器**是一个简单的启发式路由器，始终基于模型大小选择可用的最大 LLM。它将最大质量置于成本之上，非常适合质量关键型应用。

## 论文参考

此路由器是以下论文中描述的基线方法：

- **[GraphRouter: A Graph-based Router for LLM Selections](https://arxiv.org/abs/2410.03834)**
  - (2024). arXiv:2410.03834.
  - 使用最小/最大 LLM 作为路由方法的基线对比。

## 工作原理

### 路由逻辑

1. 从 `llm_data` 加载所有 LLM
2. 过滤以 'B' 结尾的模型尺寸（数十亿参数）
3. 解析尺寸（例如："7B" → 7.0, "70B" → 70.0）
4. 选择具有最大尺寸的模型
5. 将所有查询路由到这单一模型

### 无需训练

这是一个零样本启发式方法 - 无需训练。

## 配置

只需要 `llm_data` 包含模型尺寸：

```json
{
  "Qwen2.5-3B": {"size": "3B", "model": "qwen/qwen2.5-3b-instruct"},
  "Qwen2.5-7B": {"size": "7B", "model": "qwen/qwen2.5-7b-instruct"},
  "Llama-70B": {"size": "70B", "model": "meta/llama-3.1-70b-instruct"}
}
```

路由器将选择 "Llama-70B"（最大）。

## CLI 使用

最大 LLM 路由器可以通过 `llmrouter` 命令行界面使用：

### 推理

> **注意**：此路由器不需要训练 - 它是零样本启发式方法。

```bash
# 路由单个查询（始终选择最大模型）
llmrouter infer --router largest_llm --config configs/model_config_test/largest_llm.yaml \
    --query "什么是机器学习？"

# 路由文件中的查询
llmrouter infer --router largest_llm --config configs/model_config_test/largest_llm.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
llmrouter infer --router largest_llm --config configs/model_config_test/largest_llm.yaml \
    --query "解释神经网络" --route-only
```

### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router largest_llm --config configs/model_config_test/largest_llm.yaml

# 使用自定义端口启动
llmrouter chat --router largest_llm --config configs/model_config_test/largest_llm.yaml --port 8080

# 创建公共可分享链接
llmrouter chat --router largest_llm --config configs/model_config_test/largest_llm.yaml --share
```

---

## 使用方法

```python
from llmrouter.models import LargestLLM

router = LargestLLM(yaml_path="configs/model_config_test/largest_llm.yaml")

# 所有查询都路由到最大模型
queries = [
    {"query": "简单问题"},
    {"query": "需要推理的复杂问题"}
]

results = router.route_batch(queries)
# 两者都使用相同的最大模型
```

## 优势

- ✅ **最大质量**：始终使用最强大的模型
- ✅ **简单**：无需训练，无需超参数
- ✅ **快速**：即时路由决策
- ✅ **可靠**：所有任务的最佳模型

## 限制

- ❌ **最大成本**：始终使用最昂贵的模型
- ❌ **浪费**：对简单查询来说是大材小用
- ❌ **无适应性**：无法通过数据改进
- ❌ **单一模型**：无负载均衡

## 使用场景

**适用于：**
- 质量至关重要，成本次要
- 所有查询都是复杂/具有挑战性的
- 最大性能的基线
- 失败代价高昂的生产环境

**替代方案：**
- 需要节省成本 → 最小 LLM 路由器
- 平衡成本质量 → 混合 LLM 路由器
- 查询特定 → KNN/MLP/SVM 路由器

## 相关路由器

- **最小 LLM 路由器**：相反策略（最大成本节省）
- **混合 LLM 路由器**：平衡小型和大型模型
- **ELO 路由器**：数据驱动的单一模型选择

---

如有问题或建议，请参考主 LLMRouter 文档或在 GitHub 上提出 issue。
# KNN 多轮路由器

## 概述

**KNN 多轮路由器**在标准 KNN 路由器基础上扩展了多轮流水线：它将复杂查询分解为子查询，使用 KNN 对每个子查询进行路由，通过路由的模型执行它们，并将响应聚合为最终答案。

## 论文参考

此路由器实现了如论文中描述的多轮路由：

- **[Router-R1: Teaching LLMs Multi-Round Routing and Aggregation via Reinforcement Learning](https://arxiv.org/abs/2506.09033)**
  - Zhang, H., Feng, T., & You, J. (2025). arXiv:2506.09033.
  - 提出了带有分解和聚合的多轮路由。

将 **K 近邻（K-Nearest Neighbors）** 与 **查询分解** 相结合：
- **KNN**：基于实例的学习，无需训练
- **查询分解**：将复杂查询分解为更简单的子任务
- **多智能体**：将子查询委托给专门化的模型

## 工作原理

### 架构

```
查询 → 分解 → [子查询 1, 子查询 2, ...]
           ↓               ↓ (KNN 路由)      ↓ (KNN 路由)
      基础 LLM          模型 A 执行    模型 B 执行
           ↓                     ↓                 ↓
       聚合 ← [响应 1, 响应 2, ...]
           ↓
    最终答案
```

### 流水线

1. **分解**：本地 LLM 将查询分解为 1-4 个子查询
2. **路由**：每个子查询通过 KNN 路由到最佳匹配模型
3. **执行**：子查询通过 API 在路由模型上执行
4. **聚合**：基础 LLM 将子响应合并为最终答案

## 配置参数

### KNN 超参数（`hparam`）

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `n_neighbors` | int | `5` | 最近邻数量 |
| `weights` | str | `"distance"` | 权重函数：`"uniform"` 或 `"distance"` |
| `metric` | str | `"cosine"` | KNN 的距离度量 |

### 多轮配置

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `base_model` | str | `"Qwen/Qwen2.5-3B-Instruct"` | 用于分解/聚合的基础模型 |
| `use_local_llm` | bool | `false` | 使用本地 vLLM（true）或 API（false） |
| `api_endpoint` | str | - | 用于子查询执行的 API 端点 |

## CLI 使用

KNN 多轮路由器可以通过 `llmrouter` 命令行界面使用：

### 训练

```bash
# 训练 KNN 多轮路由器（构建 KNN 索引）
llmrouter train --router knnmultiroundrouter --config configs/model_config_train/knnmultiroundrouter.yaml

# 使用安静模式训练
llmrouter train --router knnmultiroundrouter --config configs/model_config_train/knnmultiroundrouter.yaml --quiet
```

### 推理

```bash
# 使用分解路由单个查询
llmrouter infer --router knnmultiroundrouter --config configs/model_config_test/knnmultiroundrouter.yaml \
    --query "解释气候变化及其成因"

# 从文件路由查询
llmrouter infer --router knnmultiroundrouter --config configs/model_config_test/knnmultiroundrouter.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
llmrouter infer --router knnmultiroundrouter --config configs/model_config_test/knnmultiroundrouter.yaml \
    --query "地震是什么原因造成的？" --route-only
```

### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router knnmultiroundrouter --config configs/model_config_test/knnmultiroundrouter.yaml

# 使用自定义端口启动
llmrouter chat --router knnmultiroundrouter --config configs/model_config_test/knnmultiroundrouter.yaml --port 8080

# 创建可公开分享的链接
llmrouter chat --router knnmultiroundrouter --config configs/model_config_test/knnmultiroundrouter.yaml --share
```

---

## 使用示例

### 推理（聊天模式）

```python
from llmrouter.models import KNNMultiRoundRouter

router = KNNMultiRoundRouter(yaml_path="configs/model_config_test/knnmultiroundrouter.yaml")

# 简单字符串查询仅返回响应
response = router.route_single("解释气候变化及其成因")
print(response)
```

### 推理（评估模式）

```python
# 字典查询返回完整指标
query = {
    "query": "地震是什么原因造成的，如何测量？",
    "ground_truth": "...",
    "task_name": "general"
}
result = router.route_single(query)

print(f"响应: {result['response']}")
print(f"Token 数: {result['prompt_tokens'] + result['completion_tokens']}")
print(f"性能: {result.get('task_performance', 'N/A')}")
```

## 优势

- ✅ **无需训练**：KNN 无需训练，只需加载数据
- ✅ **分解能力**：处理复杂的多方面查询
- ✅ **专门化路由**：每个子查询获得最佳模型
- ✅ **灵活性**：支持本地和基于 API 的执行

## 局限性

- ❌ **高延迟**：多次 API 调用增加响应时间
- ❌ **高成本**：分解 + 路由 + 聚合的 token 消耗
- ❌ **复杂性**：比简单路由有更多移动部件
- ❌ **本地 LLM 选项**：如果 use_local_llm=true，需要 vLLM 和 GPU

## 适用场景

**适用于：**
- 需要多步推理的复杂查询
- 受益于专门化模型的不同子任务
- 拥有 KNN 路由的训练数据

**替代方案：**
- 简单查询 → 标准 KNN 路由器
- 不需要分解 → 单轮路由器
- 需要 LLM 基础的分解 → LLM 多轮路由器

## 相关路由器

- **LLM 多轮路由器**：使用 LLM 进行路由而非 KNN
- **KNN 路由器**：不带分解的单轮 KNN
- **Router-R1**：采用不同方法的智能体多轮路由

---

如有问题或建议，请参考 LLMRouter 主文档或在 GitHub 上提交 issue。
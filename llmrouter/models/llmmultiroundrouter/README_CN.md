# LLM 多轮路由器

## 概述

**LLM 多轮路由器**使用基于 LLM 的推理进行查询分解和路由决策。与 KNN 多轮路由器不同，它不需要训练数据——它使用 LLM 提示智能地分解查询并为每个子查询选择最佳模型。

## 论文参考

此路由器实现的多轮路由描述于：

- **[Router-R1: Teaching LLMs Multi-Round Routing and Aggregation via Reinforcement Learning](https://arxiv.org/abs/2506.09033)**
  - Zhang, H., Feng, T., & You, J. (2025). arXiv:2506.09033.
  - 提出了具有分解和聚合的多轮路由。

具有分解功能的零样本基于 LLM 的路由：
- **LLM 推理**：使用语言模型做出路由决策
- **零样本**：无需训练，仅使用提示词即可工作
- **多智能体**：分解查询并委托给专业模型

## 工作原理

### 架构

```
查询 → LLM 分解+路由 → [(子查询 1, 模型 A), (子查询 2, 模型 B), ...]
                           ↓                          ↓
                      通过 API 执行               通过 API 执行
                           ↓                          ↓
                  LLM 聚合 ← [响应 1, 响应 2, ...]
                           ↓
                        最终答案
```

### 流程

1. **分解 + 路由（单次 LLM 调用）**：
   - LLM 将查询分解为子查询
   - 同时为每个子查询选择最佳模型
   - 基于提示词中提供的模型描述

2. **执行**：通过 API 使用路由模型执行子查询

3. **聚合**：基础 LLM 将响应组合为最终答案

## 与 KNN 多轮的关键区别

- **KNN**：使用 K 近邻（需要训练数据）
- **LLM**：使用 LLM 推理（零样本，无需训练）

## 配置参数

### 超参数 (`hparam`)

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `base_model` | str | `"Qwen/Qwen2.5-3B-Instruct"` | 用于分解/聚合/路由的基础模型 |
| `use_local_llm` | bool | `false` | 使用本地 vLLM（true）还是 API（false） |
| `api_endpoint` | str | - | 执行的 API 端点 |

### LLM 数据

需要具有模型描述的 `llm_data` 用于路由提示词。

## CLI 使用

LLM 多轮路由器可以通过 `llmrouter` 命令行界面使用：

### 推理

> **注意**：此路由器不需要训练——它使用零样本 LLM 提示词。

```bash
# 使用分解路由单个查询
llmrouter infer --router llmmultiroundrouter --config configs/model_config_test/llmmultiroundrouter.yaml \
    --query "比较神经网络和决策树"

# 从文件路由查询
llmrouter infer --router llmmultiroundrouter --config configs/model_config_test/llmmultiroundrouter.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
llmrouter infer --router llmmultiroundrouter --config configs/model_config_test/llmmultiroundrouter.yaml \
    --query "解释机器学习概念" --route-only
```

### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router llmmultiroundrouter --config configs/model_config_test/llmmultiroundrouter.yaml

# 使用自定义端口启动
llmrouter chat --router llmmultiroundrouter --config configs/model_config_test/llmmultiroundrouter.yaml --port 8080

# 创建可公开分享的链接
llmrouter chat --router llmmultiroundrouter --config configs/model_config_test/llmmultiroundrouter.yaml --share
```

---

## 使用示例

### 推理

```python
from llmrouter.models import LLMMultiRoundRouter

router = LLMMultiRoundRouter(yaml_path="configs/model_config_test/llmmultiroundrouter.yaml")

# 聊天模式
response = router.route_single("比较神经网络和决策树")
print(response)

# 评估模式
query = {"query": "...", "ground_truth": "...", "task_name": "general"}
result = router.route_single(query)
print(f"响应: {result['response']}")
print(f"性能: {result.get('task_performance', 'N/A')}")
```

## 优势

- ✅ **无需训练**：使用 LLM 提示词的零样本方式
- ✅ **智能路由**：LLM 理解模型能力
- ✅ **分解功能**：处理复杂的多方面查询
- ✅ **灵活性**：适用于 llm_data 中的任何模型

## 限制

- ❌ **高成本**：多次 LLM 调用（分解 + 聚合）
- ❌ **高延迟**：顺序 LLM 生成
- ❌ **提示词敏感性**：路由质量取决于提示词工程
- ❌ **无学习能力**：无法从历史数据中改进

## 适用场景

**适用于：**
- 没有可用的训练数据
- 需要零样本路由解决方案
- 需要分解的复杂查询
- 模型能力在元数据中有详细描述

**替代方案：**
- 有训练数据 → KNN 多轮路由器
- 简单查询 → 单轮路由器
- 成本敏感 → 避免多轮方法

## 相关路由器

- **KNN 多轮路由器**：基于训练的替代方案
- **Router-R1**：具有外部路由池的代理推理
- **因果 LM 路由器**：用于路由的微调 LLM（单轮）

---

如有问题或建议，请参考 LLMRouter 主文档或在 GitHub 上提交 issue。
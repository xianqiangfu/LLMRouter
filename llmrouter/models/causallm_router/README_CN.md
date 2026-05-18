# Causal LM Router（因果语言模型路由器）

## 概述

**Causal LM Router**（因果语言模型路由器）使用微调的因果语言模型来预测每个查询的最佳 LLM。与传统分类器不同，它将路由构建为文本生成任务，其中模型根据查询内容生成最优的 LLM 名称。

## 论文参考

该路由器受到 **RouteLLM** 和基于 LLM 的分类启发：

- **[RouteLLM: Learning to Route LLMs with Preference Data](https://arxiv.org/abs/2406.18665)**
  - Ong, I., 等 (2024). arXiv:2406.18665. 发表于 ICLR 2025。
  - 实现了 `causal_llm` 路由器，使用在偏好数据上调优的基于 LLM 的分类器。

- **LoRA**: Hu, E. J., 等 (2021). "LoRA: Low-Rank Adaptation of Large Language Models." ICLR.
- **核心思想**: 将路由视为条件文本生成。

## 工作原理

### 架构

```
Query → Prompt 模板 → 微调的 LLM (vLLM) → 生成的 LLM 名称 → 解析
```

### 路由机制

1. **训练阶段**：
   - 构建提示："Query: {query}\n\nBest LLM: {best_llm_name}"
   - 使用 LoRA 微调基础模型（如 Llama-2-7B）
   - 模型学习从查询预测最优 LLM 名称

2. **推理阶段**：
   - 将查询格式化为路由提示
   - 使用微调后的模型和 vLLM 生成 LLM 名称
   - 解析生成的文本以提取 LLM 名称
   - 将查询路由到预测的 LLM

## 配置参数

### 训练超参数 (`hparam`)

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `base_model` | str | `"meta-llama/Llama-2-7b-hf"` | 用于微调的基础 LLM |
| `use_lora` | bool | `true` | 是否使用 LoRA 进行高效微调 |
| `lora_r` | int | `16` | LoRA 秩（越低参数越少） |
| `lora_alpha` | int | `32` | LoRA 缩放因子 |
| `lora_dropout` | float | `0.1` | LoRA 层的 Dropout |
| `num_epochs` | int | `3` | 训练轮数 |
| `batch_size` | int | `4` | 每设备批次大小 |
| `learning_rate` | float | `0.00002` | 学习率 |
| `max_length` | int | `512` | 最大序列长度 |
| `merge_lora` | bool | `true` | 训练后合并 LoRA 权重 |

### 推理参数

| 参数 | 默认值 | 描述 |
|-----------|---------|-------------|
| `tensor_parallel_size` | `1` | 张量并行的 GPU 数量 |
| `max_new_tokens` | `32` | 最大生成 token 数 |
| `temperature` | `0.1` | 采样温度（低值使输出更确定性） |

## CLI 使用

Causal LM Router 可以通过 `llmrouter` 命令行界面使用：

### 训练

```bash
# 训练 Causal LM 路由器（需要 GPU）
llmrouter train --router causallmrouter --config configs/model_config_train/causallm_router.yaml --device cuda

# 使用静默模式训练
llmrouter train --router causallmrouter --config configs/model_config_train/causallm_router.yaml --device cuda --quiet
```

### 推理

```bash
# 路由单个查询
llmrouter infer --router causallmrouter --config configs/model_config_test/causallm_router.yaml \
    --query "解释光合作用"

# 路由文件中的查询
llmrouter infer --router causallmrouter --config configs/model_config_test/causallm_router.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
llmrouter infer --router causallmrouter --config configs/model_config_test/causallm_router.yaml \
    --query "什么是机器学习？" --route-only
```

### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router causallmrouter --config configs/model_config_test/causallm_router.yaml

# 使用自定义端口启动
llmrouter chat --router causallmrouter --config configs/model_config_test/causallm_router.yaml --port 8080

# 创建公共可分享链接
llmrouter chat --router causallmrouter --config configs/model_config_test/causallm_router.yaml --share
```

---

## 使用示例

### 训练

```python
from llmrouter.models import CausalLMRouter, CausalLMRouterTrainer

router = CausalLMRouter(yaml_path="configs/model_config_train/causallm_router.yaml")
trainer = CausalLMRouterTrainer(router=router)
trainer.train()
```

### 推理

```python
from llmrouter.models import CausalLMRouter

router = CausalLMRouter(yaml_path="configs/model_config_test/causallm_router.yaml")
result = router.route_single({"query": "解释光合作用"})
print(f"路由到: {result['model_name']}")
```

## 优势

- ✅ **LLM 推理能力**: 利用语言理解进行路由
- ✅ **无需特征工程**: 直接处理原始查询文本
- ✅ **迁移学习**: 从预训练知识中受益
- ✅ **LoRA 高效训练**: 仅训练小型适配器层

## 限制

- ❌ **需要 GPU**: vLLM 需要 CUDA
- ❌ **训练缓慢**: 微调 LLM 耗时较长
- ❌ **模型较大**: 基础模型数 GB
- ❌ **解析错误**: 生成的文本可能无法完全匹配 LLM 名称

## 使用场景

**适用于：**
- 大型数据集，值得进行 LLM 微调
- 复杂路由模式，受益于语言理解
- 有可用 GPU 资源

**替代方案：**
- 小数据集 → KNN/SVM 路由器
- 无 GPU → MLP 路由器
- 需要快速训练 → 更简单的分类器

## 相关路由器

- **Router-R1**: 也使用 LLM，但具有智能体推理
- **MLP/SVM 路由器**: 更简单的有监督替代方案
- **LLM 多轮路由器**: 使用 LLM 进行分解和路由

---

如有疑问或问题，请参考 LLMRouter 主文档或在 GitHub 上提 issue。
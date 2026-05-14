# Router-R1 (多轮路由器)

## 概述

**Router-R1** 是一个先进的多轮路由系统，结合了迭代推理与动态路由。与传统路由器只进行一次路由决策不同，Router-R1 使用推理循环，模型生成搜索查询，从专门的路由池获取信息，并通过多个推理步骤迭代优化答案。

## 论文参考

该路由器实现了 **Router-R1** 方法：

- **[Router-R1: Teaching LLMs Multi-Round Routing and Aggregation via Reinforcement Learning](https://arxiv.org/abs/2506.09033)**
  - Zhang, H., Feng, T., & You, J. (2025). arXiv:2506.09033.
  - 提出了基于强化学习的多轮路由与聚合方法。

- **核心思想**：通过强化学习结合推理步骤和外部知识源路由。

不是在开始时选择单个模型，而是将路由视为迭代搜索过程，模型可以在推理过程中多次查询路由池。

## 工作原理

### 架构

```
查询 -> vLLM 生成 -> <search>查询, LLM 候选</search> -> 路由池 -> <information>结果</information>
         |                                                                        |
    推理循环 <--------------------------------------------------------------+
         |
    <answer>最终答案</answer>
```

### 路由机制

1. **初始提示**：使用推理指令格式化用户查询
2. **迭代推理循环**（最多 5 次迭代）：
   - **生成**：模型生成推理文本和可选的 `<search>查询</search>`
   - **路由**：如果找到搜索标签，查询路由池 API 获取信息
   - **增强**：将检索到的信息作为 `<information>结果</information>` 追加
   - **继续**：将增强后的文本反馈给模型进行下一次迭代
3. **终止**：当模型输出 `<answer>最终答案</answer>` 时循环结束
4. **输出**：返回包含最终答案的完整推理轨迹

### 路由池

路由池是一个外部 API，提供：
- 基于查询内容的模型推荐
- 相关信息检索
- 领域特定知识

模型在训练过程中学会何时以及通过路由池搜索什么内容。

### Token 跟踪

Router-R1 跟踪三种类型的 token：
- **prompt_tokens**：所有迭代的 vLLM 输入 token
- **completion_tokens**：所有迭代的 vLLM 输出 token
- **route_tokens**：外部路由池 API token

总成本 = prompt_tokens + completion_tokens + route_tokens

## 配置参数

### 超参数（配置文件中的 `hparam`）

| 参数 | 类型 | 必填 | 说明 |
|-----------|------|----------|-------------|
| `model_id` | str | 是 | vLLM 使用的 HuggingFace 模型 ID（如 `"Qwen/Qwen2.5-7B-Instruct"`） |
| `api_base` | str | 是* | 路由池 API 的基础 URL |
| `api_key` | str | 是* | 访问路由池的 API 密钥 |

*可以在 YAML 配置之外通过环境变量设置。

### 环境变量

除了在 YAML 配置中设置 `api_base` 和 `api_key`，还可以使用与其他路由器相同的环境变量：

| 配置键 | 环境变量 |
|------------|---------------------|
| `api_key` | `API_KEYS` |
| `api_base` | `API_BASE` |

**`API_KEYS` 格式**（与其他路由器相同）：
```bash
# JSON 数组格式（推荐用于多个密钥）
export API_KEYS='["your-key-1", "your-key-2", "your-key-3"]'

# 逗号分隔格式
export API_KEYS='key1,key2,key3'

# 单个密钥
export API_KEYS='your-api-key'
```

**示例：**
```bash
export API_KEYS='your-api-key'
export API_BASE='https://api.openai.com/v1'

# 现在可以在不在 YAML 中设置 api_key/api_base 的情况下运行
llmrouter infer --router router_r1 --config configs/model_config_test/router_r1.yaml \
    --query "解释 transformers"
```

### 依赖项

Router-R1 需要：
- **vLLM==0.6.3**：用于 GPU 上的高效本地 LLM 推理（需要 torch==2.4.0）
- **CUDA**：需要 GPU（不支持 CPU）
- **openai>=1.0**：用于路由池 API 调用（在 `route_service.py` 中）

安装方式：
```bash
pip install vllm==0.6.3 torch==2.4.0 openai
```

### 模型支持

支持任何 vLLM 兼容的聊天模型：
- **Qwen**：`Qwen/Qwen2.5-7B-Instruct`、`Qwen/Qwen2.5-14B-Instruct`
- **Llama**：`meta-llama/Llama-3.1-8B-Instruct` 等

路由器会自动检测模型系列并应用相应的提示词模板。

## CLI 使用

Router-R1 可以通过 `llmrouter` 命令行界面使用：

### 推理

> **注意**：该路由器不需要训练——它是一个零样本智能系统。

```bash
# 使用智能推理路由单个查询
CUDA_VISIBLE_DEVICES=1 llmrouter infer --router router_r1 --config configs/model_config_test/router_r1.yaml \
    --query "解释机器学习中的 transformers 如何工作"

# 从文件路由查询
CUDA_VISIBLE_DEVICES=1 llmrouter infer --router router_r1 --config configs/model_config_test/router_r1.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
CUDA_VISIBLE_DEVICES=1 llmrouter infer --router router_r1 --config configs/model_config_test/router_r1.yaml \
    --query "什么是量子计算？" --route-only
```

### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router router_r1 --config configs/model_config_test/router_r1.yaml

# 使用自定义端口启动
llmrouter chat --router router_r1 --config configs/model_config_test/router_r1.yaml --port 8080

# 创建公开可分享的链接
llmrouter chat --router router_r1 --config configs/model_config_test/router_r1.yaml --share
```

---

## 使用示例

### 推理：路由单个查询

```python
from llmrouter.models import RouterR1

# 使用配置初始化路由器
router = RouterR1(yaml_path="configs/model_config_test/router_r1.yaml")

# 路由单个查询
query = {"query": "解释机器学习中的 transformers 如何工作"}
result = router.route_single(query, return_details=True)

print(f"使用的模型: {result['model_name']}")
print(f"响应（含推理轨迹）:\n{result['response']}")
print(f"总 Token 数: {result['total_tokens']}")
print(f"  - 提示 Token: {result['prompt_tokens']}")
print(f"  - 补全 Token: {result['completion_tokens']}")
print(f"  - 路由 Token: {result['route_tokens']}")
```

### 推理：批量路由

```python
from llmrouter.models import RouterR1

# 初始化路由器
router = RouterR1(yaml_path="configs/model_config_test/router_r1.yaml")

# 准备批量查询
queries = [
    {"query": "什么是量子计算？", "ground_truth": "..."},
    {"query": "解方程 x^2 - 4 = 0", "ground_truth": "x = 2 或 x = -2"}
]

# 路由并执行查询
results = router.route_batch(batch=queries, task_name="general")

for result in results:
    print(f"查询: {result['query']}")
    print(f"模型: {result['model_name']}")
    print(f"响应:\n{result['response']}")
    print(f"总 Token 数: {result['input_token'] + result['output_token']}")
    print(f"性能: {result.get('task_performance', 'N/A')}")
    print("-" * 80)
```

## YAML 配置示例

**测试配置**（`configs/model_config_test/router_r1.yaml`）：

```yaml
data_path:
  query_data_test: 'data/example_data/query_data/default_query_test.jsonl'

hparam:
  model_id: "Qwen/Qwen2.5-7B-Instruct"
  api_base: "https://api.example.com/v1"  # 你的路由池 API
  api_key: "${ROUTING_API_KEY}"            # 使用环境变量
```

**注意**：Router-R1 不需要训练——它是一个零样本智能系统。

## 优势

- ✅ **智能推理**：通过推理循环迭代优化答案
- ✅ **动态路由**：每个查询可以多次查询路由池
- ✅ **可解释性**：完整的推理轨迹显示决策过程
- ✅ **灵活性**：适用于任何 vLLM 兼容的聊天模型
- ✅ **Token 跟踪**：全面跟踪所有 token 成本
- ✅ **无需训练**：零样本系统，无需训练数据

## 局限性

- ❌ **需要 GPU**：vLLM 需要 CUDA，不支持 CPU
- ❌ **高延迟**：多次生成迭代增加响应时间
- ❌ **高成本**：多次 API 调用（vLLM + 路由池）费用较高
- ❌ **复杂性**：比简单路由器更难调试和控制
- ❌ **路由池依赖**：需要外部路由池 API
- ❌ **行为可变性**：非确定性推理可能在运行间有所变化
- ❌ **资源密集**：需要大量 GPU 显存（8GB+ VRAM）

## 何时使用 Router-R1

**适用场景：**
- 需要多步推理的复杂查询
- 需要完整推理轨迹的可解释路由决策
- 可以访问高质量的路由池 API
- 有可用的 GPU 资源（8GB+ VRAM）
- 质量比延迟/成本更重要
- 研究或高级应用

**考虑其他方案的情况：**
- 简单路由任务 → 使用 KNN/SVM/MLP 路由器
- 无可用 GPU → 使用基于 API 的路由器
- 对成本/延迟敏感 → 使用更简单的路由器
- 无路由池 API → 使用其他路由方法
- 需要确定性行为 → 使用训练好的分类器

## 性能建议

1. **模型选择**：
   - 使用 7B 模型以平衡质量和速度
   - 仅在需要最高质量时使用 14B+ 模型
   - Qwen 模型在推理任务中通常表现良好

2. **API 配置**：
   - 确保路由池 API 具有低延迟（<500ms）
   - 使用环境变量存储 API 密钥（安全性）
   - 单独监控路由池成本

3. **提示词工程**：
   - 在 `prompt_pool.py` 中为你的领域自定义提示词
   - 如有需要，调整停止序列
   - 尝试调整温度（默认：1.0）

4. **资源管理**：
   - RouterR1 根据可见 GPU 和注意力头可除性自动选择 `tensor_parallel_size`
   - 使用 `LLMROUTER_TENSOR_PARALLEL_SIZE=<int>` 覆盖以强制固定值
   - 监控 VRAM 使用情况并相应调整模型大小
   - 考虑批量查询以提高 GPU 利用率

5. **Token 优化**：
   - 限制最大迭代次数（当前上限为 5）
   - 使用较短的 max_tokens 以更快生成
   - 监控 token 成本（提示 + 补全 + 路由）

## 实现细节

- **框架**：vLLM 用于本地推理，OpenAI SDK 用于路由池
- **模型类型**：支持 Qwen、Llama 和其他指令调优模型
- **提示词模板**：基于模型系列自动检测
- **Token 计数**：分别跟踪 vLLM token 和外部 API token
- **最大迭代次数**：5 次迭代（代码中可配置）
- **停止序列**：`["</search>", "</answer>"]`

## 推理轨迹示例

```
[Generation 0] Output:
要回答这个问题，我需要了解什么是 transformers。
<search>机器学习中的 transformers 是什么？</search>

<information>
Transformers 是使用自注意力机制的神经网络架构...
</information>

[Generation 1] Output:
根据信息，transformers 通过以下方式工作：
1. 使用自注意力处理序列
2. 计算所有 token 之间的注意力分数
3. 使用多头注意力进行不同表示
<answer>
Transformers 是使用自注意力机制处理序列数据的神经网络架构。它们同时计算序列中所有位置之间的关系，使其高度可并行化...
</answer>
```

## 相关路由器

- **LLM 多轮路由器**：类似的多轮方法，但带有分解
- **因果 LM 路由器**：使用微调 LLM 但单次路由
- **Automix 路由器**：基于自验证的多步路由
- **KNN/SVM/MLP 路由器**：单次监督路由

---

如有问题或建议，请参考 LLMRouter 主文档或在 GitHub 上提交 Issue。
# LLMRouter 数据生成流水线

本目录包含用于生成 LLMRouter 训练和评估数据的脚本。该流水线由三个主要步骤组成，将原始基准测试数据转换为带有嵌入向量的格式化路由数据。

**快速开始**: 从 [`sample_config.yaml`](sample_config.yaml) 开始 - 这是一个即用型的配置文件，引用了示例数据目录。详细信息请参阅[步骤1：配置设置](#步骤1配置设置)。

## 目录

- [流水线概述](#流水线概述)
- [分步流水线](#分步流水线)
- [输入文件格式](#输入文件格式)
- [输出文件格式](#输出文件格式)
- [嵌入映射系统](#嵌入映射系统)
- [使用示例](#使用示例)
- [配置](#配置)

---

## 流水线概述

数据生成流水线遵循以下流程：

```
步骤1：配置（YAML）
    ↓
步骤2a：生成查询数据 → query_data_train.jsonl + query_data_test.jsonl
    ↓
步骤2b：生成LLM嵌入 → default_llm_embeddings.json
    ↓
步骤3：API调用与评估 →
    - query_embeddings_longformer.pt（统一嵌入）
    - default_routing_train_data.jsonl
    - default_routing_test_data.jsonl
```

### 核心特性

- **统一嵌入**：一个 `.pt` 文件包含所有查询（训练+测试）的嵌入向量
- **嵌入ID映射**：顺序ID（0, 1, 2, ...）直接映射到 `.pt` 文件中的行号
- **配置驱动**：所有路径和参数通过YAML配置控制
- **格式一致性**：输出格式与示例文件完全匹配

---

## 分步流水线

### 步骤1：配置设置

**从示例配置文件开始**：`llmrouter/data/sample_config.yaml`

此文件包含所有必要的路径和参数。你可以直接使用，也可以复制并修改以适应你自己的设置。

```bash
# 将示例配置复制到你的工作目录
cp llmrouter/data/sample_config.yaml my_config.yaml

# 根据需要编辑路径
# 然后使用任何流水线脚本运行
```

**示例配置结构**：

```yaml
data_path:
  query_data_train: 'data/example_data/query_data/default_query_train.jsonl'
  query_data_test: 'data/example_data/query_data/default_query_test.jsonl'
  query_embedding_data: 'data/example_data/routing_data/query_embeddings_longformer.pt'
  routing_data_train: 'data/example_data/routing_data/default_routing_train_data.jsonl'
  routing_data_test: 'data/example_data/routing_data/default_routing_test_data.jsonl'
  llm_data: 'data/example_data/llm_candidates/default_llm.json'
  llm_embedding_data: 'data/example_data/llm_candidates/default_llm_embeddings.json'

data_generation:
  sample_size: 500  # 每个任务的样本数
  train_ratio: 0.8  # 训练/测试分割比例
  random_seed: 42
```

**快速开始**：直接使用示例配置：
```bash
python llmrouter/data/data_generation.py --config llmrouter/data/sample_config.yaml
python llmrouter/data/generate_llm_embeddings.py --config llmrouter/data/sample_config.yaml
python llmrouter/data/api_calling_evaluation.py --config llmrouter/data/sample_config.yaml
```

### 步骤2a：生成查询数据 (`data_generation.py`)

**用途**：从基准测试数据集提取查询并创建训练/测试分割的JSONL文件。

**输入**：无（直接从HuggingFace/本地路径加载数据集）

**输出**：
- `query_data_train.jsonl` - 训练查询数据
- `query_data_test.jsonl` - 测试查询数据

**使用方法**：
```bash
# 使用配置文件（推荐）
python llmrouter/data/data_generation.py --config llmrouter/data/sample_config.yaml

# 或使用命令行参数
python llmrouter/data/data_generation.py --sample 100 \
    --output_train data/query_train.jsonl \
    --output_test data/query_test.jsonl
```

**功能说明**：
1. 从11个基准测试数据集加载样本（Natural QA、Trivia QA、MMLU、GPQA、MBPP、HumanEval、GSM8K、CommonsenseQA、MATH、OpenbookQA、ARC-Challenge）
2. 跨不同数据集结构标准化数据格式
3. 将数据分割为训练/测试集（默认80/20）
4. 保存为符合 `StandardQueryData` 格式的JSONL文件

**支持的数据集**：

| 类别 | 数据集 |
|------|--------|
| 文本 | Natural QA、Trivia QA、MMLU、GPQA、CommonsenseQA、OpenbookQA、ARC-Challenge |
| 数学 | GSM8K、MATH |
| 代码 | MBPP、HumanEval |
| 多模态 | Geometry3K、MathVista、Charades-Ego (Activity/Object/Verb) |

### 步骤2b：生成LLM嵌入 (`generate_llm_embeddings.py`)

**用途**：从LLM候选模型的元数据生成嵌入向量。

**输入**：`default_llm.json` - LLM元数据文件

**输出**：`default_llm_embeddings.json` - 带嵌入的LLM元数据

**使用方法**：
```bash
# 使用配置文件（推荐）
python llmrouter/data/generate_llm_embeddings.py --config llmrouter/data/sample_config.yaml

# 或使用命令行参数
python llmrouter/data/generate_llm_embeddings.py \
    --input data/example_data/llm_candidates/default_llm.json \
    --output data/example_data/llm_candidates/default_llm_embeddings.json
```

**功能说明**：
1. 从JSON文件读取LLM元数据
2. 使用 `feature` 字段描述为每个LLM生成嵌入
3. 向每个LLM条目添加 `embedding` 字段
4. 保存带有嵌入的更新JSON

### 步骤3：API调用与评估 (`api_calling_evaluation.py`)

**用途**：调用LLM API、评估响应，并生成统一嵌入和路由数据。

**输入**：
- `query_data_train.jsonl` 和 `query_data_test.jsonl`（来自步骤2a）
- `default_llm.json`（用于模型配置）

**输出**：
- `query_embeddings_longformer.pt` - 所有查询的统一嵌入
- `default_routing_train_data.jsonl` - 带模型响应的训练路由数据
- `default_routing_test_data.jsonl` - 带模型响应的测试路由数据

**使用方法**：
```bash
# 设置API密钥为环境变量
# 服务特定的字典格式（推荐用于多个提供商）：
export API_KEYS='{"NVIDIA": "key1,key2", "OpenAI": ["key3", "key4"]}'
# 或传统格式：
export API_KEYS='["key1", "key2", ...]'  # JSON数组格式
export API_KEYS='key1,key2,...'  # 逗号分隔

# 使用示例配置运行
python llmrouter/data/api_calling_evaluation.py --config llmrouter/data/sample_config.yaml --workers 100
```

**功能说明**：
1. 从训练和测试JSONL文件加载查询数据
2. 对每个查询，通过LiteLLM Router调用所有LLM候选模型（负载均衡）
3. 使用任务特定指标评估响应
4. 为所有唯一查询生成嵌入（训练和测试一起）
5. 创建带有顺序嵌入ID的统一 `.pt` 文件
6. 将 `embedding_id` 映射到路由数据记录
7. 保存带有所有字段的路由数据JSONL文件

**API调用机制**：

- **负载均衡**：使用多个API密钥分发请求
- **并行处理**：使用ThreadPoolExecutor并行化API调用
- **错误处理**：失败的API调用会在响应字段中记录错误消息
- **速率限制**：根据服务提供商自动处理速率限制

**评估机制**：

流水线支持多种基于任务类型的评估指标：

| 指标 | 描述 | 任务类型 |
|------|------|----------|
| `GSM8K` | 数学应用题评估 | `gsm8k` |
| `MATH` | 高级数学问题评估 | `math` |
| `em_mc` | 多选题精确匹配 | `mmlu`、`gpqa`、`commonsense_qa` 等 |
| `f1_score` | 文本匹配F1分数 | `natural_qa`、`trivia_qa` |
| `code_eval` | 代码执行评估 | `mbpp`、`human_eval` |
| `cem` | 近似精确匹配 | `natural_qa`、`trivia_qa`（自动转换） |

性能分数范围为 `0.0`（错误）到 `1.0`（正确）。

---

## 输入文件格式

### 查询数据JSONL (`query_data_train.jsonl` / `query_data_test.jsonl`)

**格式**：JSON Lines（每行一个JSON对象）

**必需字段**：

| 字段 | 类型 | 描述 | 示例 |
|------|------|------|------|
| `task_name` | string | 任务/数据集标识符 | `"gsm8k"`、`"mmlu"`、`"mbpp"` |
| `query` | string | 查询/问题文本 | `"2+2等于多少？"` |
| `ground_truth` | string | 正确答案/预期输出 | `"4"` 或 `"A"` |
| `metric` | string | 使用的评估指标 | `"GSM8K"`、`"em_mc"`、`"code_eval"` |
| `choices` | string \| null | 选项的JSON字符串（多选题） | `'{"text": ["A", "B"], "labels": ["A", "B"]}'` 或 `null` |
| `task_id` | string \| null | 任务标识符（代码任务） | `"HumanEval/0"` 或 `null` |

**示例**：
```json
{
  "task_name": "gsm8k",
  "query": "Janet有4个苹果。她给了Bob2个。她还剩下多少？",
  "ground_truth": "2",
  "metric": "GSM8K",
  "choices": null,
  "task_id": null
}
```

**多选题示例**：
```json
{
  "task_name": "mmlu",
  "query": "法国的首都是哪里？",
  "ground_truth": "A",
  "metric": "em_mc",
  "choices": "{\"text\": [\"巴黎\", \"伦敦\", \"柏林\"], \"labels\": [\"A\", \"B\", \"C\"]}",
  "task_id": null
}
```

**注意**：`choices` 字段存储为JSON字符串（而非JSON对象）以匹配示例格式。

### LLM数据JSON (`default_llm.json`)

**格式**：以LLM名称为键的JSON对象

**必需字段**（每个LLM）：

| 字段 | 类型 | 描述 | 示例 |
|------|------|------|------|
| `size` | string | 模型大小 | `"7B"`、`"70B"` |
| `feature` | string | 可读描述 | `"Qwen2.5-7B-Instruct represents..."` |
| `input_price` | float | 每百万输入令牌的成本 | `0.20` |
| `output_price` | float | 每百万输出令牌的成本 | `0.20` |
| `model` | string | API模型标识符 | `"qwen/qwen2.5-7b-instruct"` |
| `service` | string | 服务提供商 | `"NVIDIA"` |
| `api_endpoint` | string | 此模型的API端点URL | `"https://integrate.api.nvidia.com/v1"` |

**关于 `api_endpoint` 的说明**：指定API调用的基础URL的必需字段。如果此处未指定，路由器将回退到其YAML配置中的 `api_endpoint`。如果两者都不存在，将引发错误。这允许不同模型使用不同的API提供商。详细信息请参阅[主README](../README.md#configuring-api-endpoints-)。

**示例**：
```json
{
  "qwen2.5-7b-instruct": {
    "size": "7B",
    "feature": "Qwen2.5-7B-Instruct represents an upgraded version...",
    "input_price": 0.20,
    "output_price": 0.20,
    "model": "qwen/qwen2.5-7b-instruct",
    "service": "NVIDIA",
    "api_endpoint": "https://integrate.api.nvidia.com/v1"
  }
}
```

**API端点解析**：逐模型 `api_endpoint`（此字段）→ 路由器YAML `api_endpoint` → 缺失时错误。这允许不同模型使用不同的提供商。详细信息请参阅[主README](../README.md#configuring-api-endpoints-)。

---

## 输出文件格式

### 路由数据JSONL (`default_routing_train_data.jsonl` / `default_routing_test_data.jsonl`)

**格式**：JSON Lines（每行一个JSON对象）

**字段**：查询数据的所有字段加上以下内容：

| 字段 | 类型 | 描述 | 示例 |
|------|------|------|------|
| `model_name` | string | 生成响应的LLM模型 | `"llama3-chatqa-1.5-8b"` |
| `response` | string | 模型的响应文本 | `"答案是4。"` |
| `token_num` | int | 使用的总令牌数（输入+输出） | `453` |
| `input_tokens` | int | 输入令牌数 | `449` |
| `output_tokens` | int | 输出令牌数 | `4` |
| `response_time` | float | API响应时间（秒） | `1.7864494324` |
| `api_key_used` | string | API密钥标识符（如可用） | `"rivTkKeBPm"` 或 `""` |
| `performance` | float | 评估分数（0.0到1.0） | `0.95` |
| `embedding_id` | int | 映射到嵌入 `.pt` 文件的ID | `61` |
| `user_id` | null | 保留供将来使用 | `null` |
| `fig_id` | null | 保留供将来使用 | `null` |

**示例**：
```json
{
  "task_name": "gsm8k",
  "query": "Janet有4个苹果。她给了Bob2个。她还剩下多少？",
  "ground_truth": "2",
  "metric": "GSM8K",
  "choices": null,
  "task_id": null,
  "model_name": "llama3-chatqa-1.5-8b",
  "response": "Janet有4个苹果，给了Bob2个，所以她有4 - 2 = 2个苹果。",
  "token_num": 453,
  "input_tokens": 449,
  "output_tokens": 4,
  "response_time": 1.7864494324,
  "api_key_used": "",
  "performance": 1.0,
  "embedding_id": 42,
  "user_id": null,
  "fig_id": null
}
```

**关键点**：
- 每个查询出现多次（每个LLM候选模型一次）
- 同一查询的所有模型响应具有一致的 `embedding_id`
- `performance` 使用任务特定的评估指标计算
- `choices` 保持为JSON字符串格式

### 查询嵌入PyTorch文件 (`query_embeddings_longformer.pt`)

**格式**：PyTorch字典（通过 `torch.save()` 保存）

**结构**：字典映射 `embedding_id`（整数）→ 嵌入张量（torch.Tensor）

**关键属性**：
- **顺序ID**：嵌入ID从0开始并按顺序递增（0, 1, 2, 3, ...）
- **行号映射**：`embedding_id` 对应于字典中的位置
- **统一存储**：包含所有唯一查询的嵌入（训练和测试）
- **张量格式**：每个嵌入是形状为 `[embedding_dim]` 的 `torch.FloatTensor`

**加载示例**：
```python
import torch

# 加载嵌入
embeddings = torch.load("query_embeddings_longformer.pt")

# 通过ID访问嵌入
embedding_id = 42
query_embedding = embeddings[embedding_id]  # 返回 torch.Tensor

# 获取嵌入维度
embedding_dim = embeddings[0].shape[0]  # 例如，768
```

**重要**：训练和测试数据中的相同查询将具有**相同**的 `embedding_id`，因为嵌入仅为唯一查询生成。

### LLM嵌入JSON (`default_llm_embeddings.json`)

**格式**：与 `default_llm.json` 相同的结构，添加了 `embedding` 字段

**附加字段**：

| 字段 | 类型 | 描述 | 示例 |
|------|------|------|------|
| `embedding` | array | 嵌入向量（浮点数列表） | `[0.042, 0.090, -0.018, ...]` |

**注意**：此文件包含 `default_llm.json` 的所有字段，包括 `api_endpoint`，加上 `embedding` 字段。`api_endpoint` 字段的工作方式与 `default_llm.json` 中相同 - 它指定每个模型的API端点URL，并遵循相同的解析优先级（逐模型端点 → 路由器配置端点 → 错误）。

**示例**：
```json
{
  "qwen2.5-7b-instruct": {
    "feature": "Qwen2.5-7B-Instruct represents...",
    "input_price": 0.2,
    "output_price": 0.2,
    "model": "qwen/qwen2.5-7b-instruct",
    "api_endpoint": "https://integrate.api.nvidia.com/v1",
    "embedding": [0.04236221686005592, 0.09024723619222641, ...]
  }
}
```

---

## 嵌入映射系统

### 嵌入ID如何工作

嵌入映射系统确保查询嵌入的高效存储和检索：

1. **唯一查询识别**：查询通过元组 `(task_name, query, ground_truth, metric)` 识别

2. **顺序ID分配**：
   - 收集所有唯一查询（来自训练和测试）
   - 为每个唯一查询生成嵌入
   - 分配从0开始的顺序ID：`0, 1, 2, 3, ...`

3. **统一存储**：
   - 一个 `.pt` 文件包含所有嵌入
   - `embedding_id` 直接映射到 `.pt` 文件中的字典键
   - 相同查询 = 相同 `embedding_id`（无论是在训练还是测试中）

4. **路由数据中的映射**：
   - 每个路由数据记录都有一个 `embedding_id` 字段
   - 此ID指向 `.pt` 文件中对应的嵌入
   - 多个路由记录（不同模型）如果针对同一查询，可以共享相同的 `embedding_id`

### 映射示例

```
查询："2+2等于多少？"（task_name="gsm8k"，ground_truth="4"，metric="GSM8K"）
  ↓
分配 embedding_id = 42
  ↓
存储在 query_embeddings_longformer.pt 中：embeddings[42] = tensor([...])
  ↓
此查询的所有路由记录都有 embedding_id = 42：
  - {query: "2+2等于多少？", model_name: "llama3-8b", embedding_id: 42, ...}
  - {query: "2+2等于多少？", model_name: "gpt-4", embedding_id: 42, ...}
  - {query: "2+2等于多少？", model_name: "qwen-7b", embedding_id: 42, ...}
```

### 检索嵌入

```python
import torch
import json

# 加载嵌入
embeddings = torch.load("query_embeddings_longformer.pt")

# 加载路由数据
with open("default_routing_train_data.jsonl", "r") as f:
    for line in f:
        record = json.loads(line)
        embedding_id = record["embedding_id"]
        query_embedding = embeddings[embedding_id]

        # 现在你有了此查询的嵌入
        print(f"查询: {record['query']}")
        print(f"嵌入形状: {query_embedding.shape}")
```

---

## 使用示例

### 完整流水线运行

```bash
# 步骤1：生成查询数据
python llmrouter/data/data_generation.py --config llmrouter/data/sample_config.yaml

# 步骤2：生成LLM嵌入
python llmrouter/data/generate_llm_embeddings.py --config llmrouter/data/sample_config.yaml

# 步骤3：API调用和评估（需要API_KEYS环境变量）
# 服务特定的字典格式（推荐用于多个提供商）：
export API_KEYS='{"NVIDIA": "nvidia-key-1,nvidia-key-2", "OpenAI": ["openai-key-1", "openai-key-2"]}'
# 或传统格式：
export API_KEYS='["your-key-1", "your-key-2"]'
python llmrouter/data/api_calling_evaluation.py --config llmrouter/data/sample_config.yaml --workers 100
```

### 快速测试运行

```bash
# 生成用于测试的小数据集
python llmrouter/data/data_generation.py --config config.yaml --test

# 生成LLM嵌入
python llmrouter/data/generate_llm_embeddings.py --config config.yaml

# 使用有限样本测试API调用
python llmrouter/data/api_calling_evaluation.py --config config.yaml --test --workers 10
```

### 自定义配置

```yaml
# config.yaml
data_path:
  query_data_train: 'my_data/train_queries.jsonl'
  query_data_test: 'my_data/test_queries.jsonl'
  query_embedding_data: 'my_data/embeddings.pt'
  routing_data_train: 'my_data/train_routing.jsonl'
  routing_data_test: 'my_data/test_routing.jsonl'
  llm_data: 'my_data/llms.json'
  llm_embedding_data: 'my_data/llm_embeddings.json'

data_generation:
  sample_size: 1000  # 每个任务更多样本
  train_ratio: 0.9   # 90%训练，10%测试
  random_seed: 123
```

---

## 配置

### 必需的环境变量

- `API_KEYS`：服务特定的字典、JSON数组或逗号分隔的API密钥列表，用于LiteLLM Router
  ```bash
  # 服务特定的字典格式（推荐用于多个提供商）：
  export API_KEYS='{"NVIDIA": "key1,key2", "OpenAI": ["key3", "key4"]}'
  # 或传统格式：
  export API_KEYS='["key1", "key2"]'  # JSON格式
  export API_KEYS='key1,key2'  # 逗号分隔
  ```
  **注意**：使用字典格式时，确保LLM候选JSON中的 `service` 字段与 `API_KEYS` 中的键匹配。

### 配置文件结构

```yaml
data_path:
  # 查询数据（步骤3的输入，步骤2a的输出）
  query_data_train: 'path/to/query_data_train.jsonl'
  query_data_test: 'path/to/query_data_test.jsonl'

  # 嵌入（步骤3的输出）
  query_embedding_data: 'path/to/query_embeddings_longformer.pt'

  # 路由数据（步骤3的输出）
  routing_data_train: 'path/to/default_routing_train_data.jsonl'
  routing_data_test: 'path/to/default_routing_test_data.jsonl'

  # LLM数据（步骤2b和步骤3的输入）
  llm_data: 'path/to/default_llm.json'
  llm_embedding_data: 'path/to/default_llm_embeddings.json'  # 步骤2b的输出

data_generation:
  sample_size: 500      # 每个任务的样本数（默认：500）
  train_ratio: 0.8      # 训练/测试分割（默认：0.8）
  random_seed: 42       # 可重现性的随机种子
```

### 路径解析

- **相对路径**：相对于项目根目录解析
- **绝对路径**：按原样使用
- **路径解析**：由 `DataLoader.to_abs()` 方法处理

---

## 故障排除

### 常见问题

1. **缺少API密钥**：确保在运行步骤3之前设置了 `API_KEYS` 环境变量
2. **文件未找到**：检查配置文件中的所有路径是否正确
3. **嵌入ID不匹配**：确保所有步骤使用相同的配置
4. **内存问题**：如果内存不足，请减少 `--workers` 数量

### 验证

要验证输出格式与示例匹配：

```python
import json
import torch

# 检查路由数据格式
with open("default_routing_train_data.jsonl", "r") as f:
    sample = json.loads(f.readline())
    print("必需字段:", set(sample.keys()))

# 检查嵌入格式
embeddings = torch.load("query_embeddings_longformer.pt")
print(f"嵌入数量: {len(embeddings)}")
print(f"嵌入维度: {embeddings[0].shape}")
print(f"ID范围: 0到{len(embeddings)-1}")
```

---

## 文件结构

```
llmrouter/data/
├── README.md                    # 本文件（中文版）
├── data.py                      # 数据格式定义和验证器
├── data_loader.py               # 数据加载工具
├── data_generation.py           # 步骤2a：生成查询数据
├── generate_llm_embeddings.py   # 步骤2b：生成LLM嵌入
├── api_calling_evaluation.py    # 步骤3：API调用和评估
├── sample_config.yaml           # 示例配置文件（从这里开始！）
├── __init__.py                  # 包初始化
└── multimodal_generation.py     # 多模态数据生成
```

---

## 数据处理流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                    数据生成流水线（三步骤流程）                    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      步骤 1: 配置设置                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  sample_config.yaml                                      │   │
│  │  ├── data_path:                                         │   │
│  │  │   ├── query_data_train: '...'                        │   │
│  │  │   ├── query_data_test: '...'                         │   │
│  │  │   ├── llm_data: '...'                                │   │
│  │  │   └── ...                                            │   │
│  │  └── data_generation:                                   │   │
│  │      ├── sample_size: 500                               │   │
│  │      ├── train_ratio: 0.8                               │   │
│  │      └── random_seed: 42                                │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌───────────────────────────┐     ┌───────────────────────────┐
│   步骤 2a: 生成查询数据    │     │  步骤 2b: 生成LLM嵌入      │
│  data_generation.py       │     │  generate_llm_embeddings  │
├───────────────────────────┤     ├───────────────────────────┤
│ 输入: 11个基准数据集       │     │ 输入: default_llm.json    │
│   - Natural QA            │     │ 输出: default_llm_        │
│   - Trivia QA             │     │        embeddings.json    │
│   - MMLU, GPQA            │     │                           │
│   - GSM8K, MATH           │     │ 功能:                     │
│   - MBPP, HumanEval       │     │ 1. 读取LLM元数据          │
│   - CommonsenseQA, etc.   │     │ 2. 使用feature字段生成嵌入 │
├───────────────────────────┤     │ 3. 添加embedding字段       │
│ 输出:                    │     │ 4. 保存更新后的JSON        │
│   - query_data_train.jsonl│     │                           │
│   - query_data_test.jsonl │     └───────────────────────────┘
│                           │                 │
│ 功能:                    │                 │
│ 1. 加载数据集样本         │                 │
│ 2. 标准化数据格式         │                 │
│ 3. 训练/测试分割(80/20)   │                 │
│ 4. 保存JSONL文件          │                 │
└───────────────────────────┘                 │
                │                             │
                └──────────────┬──────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              步骤 3: API调用与评估                                │
│               api_calling_evaluation.py                          │
├─────────────────────────────────────────────────────────────────┤
│ 输入:                                                           │
│   - query_data_train.jsonl                                      │
│   - query_data_test.jsonl                                       │
│   - default_llm.json                                            │
│   - API_KEYS环境变量                                             │
├─────────────────────────────────────────────────────────────────┤
│ API调用机制:                                                     │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  LiteLLM Router                                         │  │
│   │  ├── 负载均衡: 多个API密钥分发请求                       │  │
│   │  ├── 并行处理: ThreadPoolExecutor                      │  │
│   │  └── 错误处理: 记录失败请求                            │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                  │
│ 评估机制:                                                        │
│   ┌──────────────┬────────────────┬──────────────────────────┐ │
│   │ 指标          │ 描述            │ 任务类型                  │ │
│   ├──────────────┼────────────────┼──────────────────────────┤ │
│   │ GSM8K        │ 数学应用题      │ gsm8k                     │ │
│   │ MATH         │ 高级数学        │ math                      │ │
│   │ em_mc        │ 多选题精确匹配  │ mmlu, gpqa, ...          │ │
│   │ f1_score     │ 文本匹配F1      │ natural_qa, trivia_qa    │ │
│   │ code_eval    │ 代码执行        │ mbpp, human_eval         │ │
│   └──────────────┴────────────────┴──────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ 输出:                                                           │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  query_embeddings_longformer.pt                         │  │
│   │  ├── 统一嵌入: 所有查询(训练+测试)                      │  │
│   │  ├── 顺序ID: 0, 1, 2, 3, ...                           │  │
│   │  └── 嵌入映射: embedding_id → 向量                     │  │
│   └─────────────────────────────────────────────────────────┘  │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  default_routing_train_data.jsonl                       │  │
│   │  └── default_routing_test_data.jsonl                    │  │
│   │      ├── 查询字段 + 响应数据                             │  │
│   │      ├── model_name, response, token_num                │  │
│   │      ├── performance (0.0-1.0)                          │  │
│   │      └── embedding_id (映射到.pt文件)                   │  │
│   └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      输出数据可用于路由器训练                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 其他说明

- **嵌入模型**：目前使用基于Longformer的嵌入（通过 `get_longformer_embedding()`）
- **负载均衡**：LiteLLM Router在多个API密钥之间分发API调用
- **并行处理**：使用ThreadPoolExecutor并行化API调用
- **错误处理**：失败的API调用会在响应字段中记录错误消息
- **格式一致性**：所有输出设计为与示例文件完全匹配以确保兼容性

如有疑问或问题，请参阅LLMRouter主文档或提出issue。
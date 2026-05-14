# LLMRouter 工具函数模块说明

本模块包含 LLMRouter 项目的各类工具函数，提供数据加载、处理、评估、嵌入生成、API 调用等核心功能。

## 目录

- [模块概览](#模块概览)
- [数据加载与转换](#数据加载与转换)
- [API 调用](#api-调用)
- [嵌入生成](#嵌入生成)
- [评估指标](#评估指标)
- [提示词格式化](#提示词格式化)
- [数据处理](#数据处理)
- [对话处理](#对话处理)
- [进度跟踪](#进度跟踪)
- [模型加载](#模型加载)
- [张量与 DataFrame 工具](#张量与-dataframe-工具)
- [常量与配置](#常量与配置)
- [环境设置](#环境设置)

## 模块概览

### 文件列表

| 文件 | 说明 |
|------|------|
| `__init__.py` | 包初始化文件，导出所有公共接口 |
| `data_loader.py` | 数据加载工具（CSV、JSONL、PyTorch） |
| `data_convert.py` | 数据格式转换工具 |
| `data_processing.py` | 数据处理和嵌入生成 |
| `dataframe_utils.py` | DataFrame 清理和标准化 |
| `api_calling.py` | API 调用工具（支持负载均衡） |
| `embeddings.py` | 文本嵌入生成（Longformer） |
| `evaluation.py` | 评估指标（F1、EM、BERT Score 等） |
| `prompting.py` | 提示词格式化工具 |
| `conversation.py` | 对话处理工具 |
| `arena_conversation.py` | Arena 对话和偏好聚合 |
| `progress.py` | 进度跟踪工具 |
| `model_loader.py` | 模型加载和保存 |
| `tensor_utils.py` | 张量转换工具 |
| `router_helpers.py` | 路由器辅助工具 |
| `constants.py` | 常量和配置 |
| `setup.py` | 环境设置 |

---

## 数据加载与转换

### data_loader.py

提供多种文件格式的数据加载功能。

#### 函数列表

##### `load_csv(path: str) -> Optional[pd.DataFrame]`
加载 CSV 文件并返回 DataFrame。

**参数：**
- `path`: CSV 文件路径

**返回：**
- 成功时返回 `pd.DataFrame`，失败返回 `None`

**示例：**
```python
from llmrouter.utils import load_csv

df = load_csv("data.csv")
if df is not None:
    print(df.head())
```

##### `load_jsonl(path: str) -> Optional[List[Dict[str, Any]]]`
加载 JSONL（JSON Lines）文件并返回字典列表。

**参数：**
- `path`: JSONL 文件路径

**返回：**
- 成功时返回字典列表，失败返回 `None`

**示例：**
```python
from llmrouter.utils import load_jsonl

data = load_jsonl("data.jsonl")
if data:
    print(f"Loaded {len(data)} records")
```

##### `jsonl_to_csv(jsonl_path: str, csv_path: Optional[str] = None) -> Optional[pd.DataFrame]`
将 JSONL 文件转换为 CSV 格式。

**参数：**
- `jsonl_path`: 输入 JSONL 文件路径
- `csv_path`: 输出 CSV 文件路径（可选，默认同目录下同名 CSV）

**返回：**
- 成功时返回 `pd.DataFrame`，失败返回 `None`

**示例：**
```python
from llmrouter.utils import jsonl_to_csv

df = jsonl_to_csv("data.jsonl", "data.csv")
```

##### `load_pt(path: str) -> Optional[Any]`
加载 PyTorch .pt 文件（可以是 Tensor 或 Dict）。

**参数：**
- `path`: .pt 文件路径

**返回：**
- 成功时返回加载的数据，失败返回 `None`

**示例：**
```python
from llmrouter.utils import load_pt

embeddings = load_pt("query_embeddings.pt")
```

### data_convert.py

数据格式转换工具，支持将数据转换为路由器训练/测试所需格式。

**依赖：** `litellm`, `tqdm`, `pandas`, `numpy`

**主要功能：**
- 测试数据转换（`convert_data`）
- 训练数据转换（`convert_train_data`）
- 训练测试数据合并（`merge_train_test`）

**命令行使用示例：**
```bash
# 转换测试数据（不使用 LLM）
python -m llmrouter.utils.data_convert \
    --input default_routing_test_data.jsonl \
    --output router_test_data_nq.json \
    --mode test

# 转换测试数据（使用 LLM 生成能力字段）
python -m llmrouter.utils.data_convert \
    --input default_routing_test_data.jsonl \
    --output router_test_data_nq.json \
    --mode test --use-llm --workers 10

# 转换训练数据
python -m llmrouter.utils.data_convert \
    --input default_routing_train_data.jsonl \
    --output router_train_data_nq.json \
    --mode train

# 合并训练和测试数据
python -m llmrouter.utils.data_convert \
    --test-file router_test_data_nq.json \
    --train-file router_train_data_nq.json \
    --output train_test_nq.jsonl \
    --mode merge
```

---

## API 调用

### api_calling.py

使用 LiteLLM 进行 API 调用，支持手动负载均衡。

**依赖：** `litellm`, `transformers`（可选）

#### 函数列表

##### `call_api(request, api_keys_env=None, max_tokens=512, temperature=0.01, top_p=0.9, timeout=30, max_retries=3)`

使用 LiteLLM 完成接口进行 LLM API 调用，支持手动轮询负载均衡。

**参数：**
- `request`: 单个请求字典或请求列表，每个请求包含：
  - `api_endpoint` (str): API 端点 URL
  - `query` (str): 查询/提示文本
  - `model_name` (str): 模型标识名称
  - `api_name` (str): 实际 API 模型名称/路径
  - `service` (str, optional): 服务提供商名称（如 "NVIDIA", "OpenAI"）
  - `system_prompt` (str, optional): 系统提示词
- `api_keys_env`: API_KEYS 环境变量覆盖（可选，用于测试）
- `max_tokens`: 最大生成 token 数，默认 512
- `temperature`: 采样温度，默认 0.01
- `top_p`: Top-p 采样参数，默认 0.9
- `timeout`: 请求超时时间（秒），默认 30
- `max_retries`: 最大重试次数，默认 3

**返回：**
- 与输入格式匹配的单个字典或字典列表，包含：
  - `response` (str): API 响应文本
  - `token_num` (int): 总 token 数
  - `prompt_tokens` (int): 输入 token 数
  - `completion_tokens` (int): 输出 token 数
  - `response_time` (float): 响应时间（秒）
  - `error` (str, optional): 错误信息

**示例：**
```python
from llmrouter.utils import call_api

# 单个请求
request = {
    "api_endpoint": "https://integrate.api.nvidia.com/v1",
    "query": "What is 2+2?",
    "model_name": "qwen2.5-7b-instruct",
    "api_name": "qwen/qwen2.5-7b-instruct"
}
result = call_api(request)
print(result["response"])

# 批量请求（自动分发到多个 API 密钥）
requests = [request1, request2, request3]
results = call_api(requests)
```

**API Keys 配置：**

支持多种格式（通过环境变量 `API_KEYS`）：

1. 服务特定格式（字典）：
```python
API_KEYS = '{"NVIDIA": "key1,key2", "OpenAI": ["key3", "key4"]}'
```

2. 列表格式：
```python
API_KEYS = '["key1", "key2", "key3"]'
```

3. 单个密钥：
```python
API_KEYS = "your-api-key"
```

4. 逗号分隔：
```python
API_KEYS = "key1,key2,key3"
```

---

## 嵌入生成

### embeddings.py

使用 Longformer 模型生成文本嵌入。

**依赖：** `torch`, `transformers`

**环境变量：**
- `LLMROUTER_EMBEDDING_DEVICE`: 指定设备（如 "cpu"、"cuda"、"cuda:0"），默认自动选择

#### 函数列表

##### `get_longformer_embedding(texts)`

获取文本的 Longformer 嵌入。

**参数：**
- `texts`: 输入文本（字符串或字符串列表）

**返回：**
- 单个嵌入（`torch.Tensor`）如果输入单个文本
- 批量嵌入（`torch.Tensor`）如果输入多个文本

**示例：**
```python
from llmrouter.utils import get_longformer_embedding

# 单个文本
embedding = get_longformer_embedding("Hello, world!")
print(embedding.shape)  # torch.Size([768])

# 批量文本
embeddings = get_longformer_embedding(["Hello", "World"])
print(embeddings.shape)  # torch.Size([2, 768])
```

##### `parallel_embedding_task(data)`

并行生成嵌入的任务函数。

**参数：**
- `data`: 元组 `(id, query_text)`

**返回：**
- 元组 `(id, query_embedding, success_flag)`

**示例：**
```python
from llmrouter.utils import parallel_embedding_task
from multiprocessing.dummy import Pool as ThreadPool

tasks = [(0, "text1"), (1, "text2"), (2, "text3")]
with ThreadPool(10) as p:
    results = p.map(parallel_embedding_task, tasks)

for id, embedding, success in results:
    if success:
        print(f"ID {id}: {embedding.shape}")
```

---

## 评估指标

### evaluation.py

提供多种评估指标，用于评估模型预测与真实答案的匹配程度。

**依赖：**
- `numpy`（必需）
- `bert-score`（可选，用于 BERTScore）
- `openai`（可选，用于 `model_prompting`）

#### 函数列表

##### `normalize_answer(s: str, normal_method: str = "") -> str`

标准化文本用于评估。

**参数：**
- `s`: 要标准化的字符串
- `normal_method`: 标准化方法（"mc" 用于多选题，"" 用于标准处理）

**返回：**
- 标准化后的字符串

##### `f1_score(prediction: str, ground_truth: str) -> Tuple[float, float, float]`

计算预测与真实答案之间的 F1 分数。

**参数：**
- `prediction`: 预测文本
- `ground_truth`: 真实答案文本

**返回：**
- 元组 `(f1, precision, recall)`

**示例：**
```python
from llmrouter.utils import f1_score

f1, precision, recall = f1_score("the cat sat on the mat", "cat sat on mat")
print(f"F1: {f1:.3f}, Precision: {precision:.3f}, Recall: {recall:.3f}")
```

##### `exact_match_score(prediction: str, ground_truth: str, normal_method: str = "") -> bool`

检查预测是否与真实答案完全匹配（标准化后）。

**参数：**
- `prediction`: 预测文本
- `ground_truth`: 真实答案文本
- `normal_method`: 标准化方法

**返回：**
- 完全匹配返回 `True`，否则返回 `False`

**示例：**
```python
from llmrouter.utils import exact_match_score

match = exact_match_score("The answer is 42.", "42")
print(match)  # True
```

##### `cem_score(prediction: str, ground_truth: str) -> float`

计算 CEM（Contains Exact Match）分数，如果标准化后的预测包含真实答案则返回 1.0，否则返回 0.0。

**参数：**
- `prediction`: 预测文本
- `ground_truth`: 真实答案文本

**返回：**
- 分数 1.0 或 0.0

##### `get_bert_score(generate_response: List[str], ground_truth: List[str]) -> float`

计算生成响应与真实答案之间的 BERT 分数（F1）。

**参数：**
- `generate_response`: 生成响应列表
- `ground_truth`: 真实答案文本列表

**返回：**
- 平均 BERT 分数（F1）

**依赖：** 需要安装 `bert-score`

**示例：**
```python
from llmrouter.utils import get_bert_score

score = get_bert_score(
    ["The cat sat on the mat"],
    ["cat sat on mat"]
)
print(f"BERT Score: {score:.4f}")
```

##### `evaluate_code(generated_code: str, test_cases: list, timeout: int = 5) -> bool`

评估生成的代码是否通过测试用例。

**参数：**
- `generated_code`: 生成的代码字符串
- `test_cases`: 测试用例字符串列表（断言）
- `timeout`: 最大执行时间（秒），默认 5

**返回：**
- 所有测试通过返回 `True`，否则返回 `False`

**示例：**
```python
from llmrouter.utils import evaluate_code

code = "def add(a, b):\n    return a + b"
tests = ["assert add(1, 2) == 3", "assert add(-1, 1) == 0"]
passed = evaluate_code(code, tests)
print(f"Tests passed: {passed}")
```

##### `calculate_task_performance(prediction: str, ground_truth: Optional[str], task_name: Optional[str] = None, metric: Optional[str] = None) -> Optional[float]`

根据任务名称或指定的评估指标计算任务性能分数。

**参数：**
- `prediction`: 模型的响应/预测
- `ground_truth`: 真实答案（可选）
- `task_name`: 任务名称，用于推断评估指标（如果未提供 metric）
- `metric`: 使用的评估指标（可选，如果未提供则从 task_name 推断）

**支持的指标：**
- `em`: Exact Match（精确匹配）
- `em_mc`: Exact Match for Multiple Choice（多选题精确匹配）
- `cem`: Contains Exact Match（包含精确匹配）
- `gsm8k`: GSM8K 专用评估
- `math`: MATH 专用评估（`\boxed{}` 格式）
- `f1`: F1 分数

**返回：**
- 性能分数（0.0 到 1.0）或 None（如果 ground_truth 不可用）

**示例：**
```python
from llmrouter.utils import calculate_task_performance

# 使用任务名称自动推断指标
score = calculate_task_performance(
    prediction="42",
    ground_truth="42",
    task_name="gsm8k"
)

# 指定评估指标
score = calculate_task_performance(
    prediction="The cat sat on the mat",
    ground_truth="cat sat on mat",
    metric="cem"
)
```

##### `model_prompting(llm_model: str, prompt: str, max_token_num: Optional[int] = 512, temperature: Optional[float] = 0.2, top_p: Optional[float] = 0.7, stream: Optional[bool] = True) -> str`

使用 OpenAI 兼容的 API 获取 LLM 响应。

**参数：**
- `llm_model`: 使用的模型名称
- `prompt`: 输入提示文本
- `max_token_num`: 最大生成 token 数，默认 512
- `temperature`: 采样温度，默认 0.2
- `top_p`: Top-p 采样参数，默认 0.7
- `stream`: 是否流式输出，默认 True

**依赖：** 需要 `openai` 库

**环境变量：**
- `OPENAI_API_KEY` / `NVIDIA_API_KEY` / `NVAPI_KEY`: API 密钥
- `OPENAI_API_BASE` / `NVIDIA_API_BASE`: API 端点

**示例：**
```python
from llmrouter.utils import model_prompting

response = model_prompting(
    llm_model="nvdev/nvidia/llama-3.1-nemotron-70b-instruct",
    prompt="What is the capital of France?",
    max_token_num=100
)
print(response)
```

---

## 提示词格式化

### prompting.py

为不同任务生成格式化的提示词，支持自定义任务扩展。

**依赖：** `llmrouter.prompts`

#### 函数列表

##### `format_mc_prompt(question, choices)`

格式化多选题提示词。

**参数：**
- `question`: 问题文本
- `choices`: 选项列表

**返回：**
- 字典 `{"system": system_prompt, "user": user_query}`

**示例：**
```python
from llmrouter.utils import format_mc_prompt

prompt = format_mc_prompt(
    question="What is 2+2?",
    choices=["3", "4", "5", "6"]
)
print(prompt["system"])
print(prompt["user"])
```

##### `format_gsm8k_prompt(query)`

格式化 GSM8K 数学题提示词。

**参数：**
- `query`: 题目文本

**返回：**
- 字典 `{"system": system_prompt, "user": user_query}`

##### `format_math_prompt(query)`

格式化 MATH 竞赛数学题提示词。

**参数：**
- `query`: 题目文本

**返回：**
- 字典 `{"system": system_prompt, "user": user_query}`

##### `format_commonsense_qa_prompt(query, choices)`

格式化常识问答提示词。

**参数：**
- `query`: 问题文本
- `choices`: 字典 `{"label": [...], "text": [...]}`

**返回：**
- 字典 `{"system": system_prompt, "user": user_query}`

##### `format_mbpp_prompt(text, tests)`

格式化 MBPP 代码生成任务提示词。

**参数：**
- `text`: 任务描述
- `tests`: 测试用例列表

**返回：**
- 字典 `{"system": system_prompt, "user": user_query}`

##### `format_humaneval_prompt(prompt)`

格式化 HumanEval 代码生成任务提示词。

**参数：**
- `prompt`: 函数签名和文档字符串

**返回：**
- 字典 `{"system": system_prompt, "user": user_query}`

##### `generate_task_query(task_name, sample_data)`

根据任务名称和样本数据生成查询提示词。

**参数：**
- `task_name`: 任务名称
- `sample_data`: 包含 `query` 和 `choices`（可选）的字典

**返回：**
- 字典 `{"system": system_prompt, "user": user_query}`

**支持的任务：**
- `natural_qa`, `trivia_qa`: 直接查询
- `mmlu`, `gpqa`: 多选题
- `gsm8k`: 小学数学
- `math`: 竞赛数学
- `commonsense_qa`, `openbook_qa`, `arc_challenge`: 常识问答
- `mbpp`, `human_eval`: 代码生成
- `geometry3k`: 几何数学
- `mathvista`: 数学视觉问答
- `charades_ego_*`: 视频动作识别

**示例：**
```python
from llmrouter.utils import generate_task_query

# GSM8K 任务
prompt = generate_task_query(
    task_name="gsm8k",
    sample_data={"query": "John has 5 apples. He gives 2 to Mary. How many does he have left?"}
)

# MMLU 任务
prompt = generate_task_query(
    task_name="mmlu",
    sample_data={
        "query": "What is the capital of France?",
        "choices": ["London", "Paris", "Berlin", "Madrid"]
    }
)
```

##### `register_prompt(task_name: str, default_metric: Optional[str] = None)`

装饰器，用于注册自定义提示词格式化函数。

**参数：**
- `task_name`: 任务名称
- `default_metric`: 可选的默认评估指标名称

**示例：**
```python
from llmrouter.utils import register_prompt

@register_prompt('sentiment_analysis', default_metric='sentiment_accuracy')
def format_sentiment_analysis_prompt(sample_data):
    return {
        "system": "You are a sentiment classifier.",
        "user": f"Classify the sentiment: {sample_data['query']}"
    }

# 现在可以使用自定义任务
prompt = generate_task_query(
    task_name="sentiment_analysis",
    sample_data={"query": "I love this product!"}
)
```

##### `register_task_metric(task_name: str, metric_name: str)`

注册任务的默认评估指标。

**参数：**
- `task_name`: 任务名称
- `metric_name`: 评估指标名称

**示例：**
```python
from llmrouter.utils import register_task_metric

register_task_metric('custom_task', 'custom_f1_score')
```

---

## 数据处理

### data_processing.py

提供最终数据处理和嵌入生成的功能。

**依赖：** `pandas`, `numpy`, `torch`, `tqdm`

#### 函数列表

##### `process_final_data(df_all)`

处理最终数据以匹配路由器格式，包括生成嵌入 ID 并保存文件。

**参数：**
- `df_all`: 包含所有数据（包括 `query_embedding` 列）的 DataFrame

**返回：**
- 元组 `(df_train_indexed, df_test_indexed, embedding_dict)`

**输出文件：**
- `query_embeddings.pt`: 嵌入字典
- `default_routing_train_data.jsonl`: 训练数据
- `default_routing_test_data.jsonl`: 测试数据

##### `process_unified_embeddings_and_routing(df_train, df_test, query_data_train, query_data_test, embedding_output_path, routing_train_output_path, routing_test_output_path)`

处理统一的嵌入（训练+测试）并生成带 embedding_id 映射的路由数据。

**参数：**
- `df_train`: 训练路由数据 DataFrame
- `df_test`: 测试路由数据 DataFrame
- `query_data_train`: 原始训练查询数据
- `query_data_test`: 原始测试查询数据
- `embedding_output_path`: 嵌入 .pt 文件保存路径
- `routing_train_output_path`: 训练路由数据 JSONL 保存路径
- `routing_test_output_path`: 测试路由数据 JSONL 保存路径

**返回：**
- 元组 `(embedding_dict, df_train_final, df_test_final)`

##### `generate_embeddings_for_data(data, desc="Generating embeddings")`

为数据列表生成嵌入。

**参数：**
- `data`: 包含 `query` 字段的数据项列表
- `desc`: 进度条描述

**返回：**
- 元组列表 `[(id, embedding, success), ...]`

**示例：**
```python
from llmrouter.utils import generate_embeddings_for_data

data = [
    {"query": "What is AI?"},
    {"query": "Explain machine learning."}
]

results = generate_embeddings_for_data(data, desc="Processing queries")
for id, embedding, success in results:
    if success:
        print(f"ID {id}: {embedding.shape}")
```

---

## 对话处理

### conversation.py & arena_conversation.py

处理对话格式和偏好聚合的工具函数。

**依赖：** `json`

#### 函数列表

##### `extract_user_prompt(conversation, turn=1)`

从对话中提取用户提示。

**参数：**
- `conversation`: 对话（字符串或列表）
- `turn`: 轮次编号（从 1 开始）

**返回：**
- 用户提示文本

##### `extract_model_response(conversation, turn=1)`

从对话中提取模型响应。

**参数：**
- `conversation`: 对话（字符串或列表）
- `turn`: 轮次编号（从 1 开始）

**返回：**
- 模型响应文本

##### `aggregate_preferences_by_query(data, turn_filter=None)`

按查询聚合所有成对偏好并创建整体排名。

**参数：**
- `data`: 数据列表，每条数据包含 `conversation_a`、`conversation_b`、`model_a`、`model_b`、`winner` 等
- `turn_filter`: 可选的轮次过滤器

**返回：**
- 字典，键为查询文本，值为包含模型、偏好等信息的字典

##### `calculate_model_scores(query_groups)`

计算每个查询组中每个模型的评估分数。

**参数：**
- `query_groups`: 由 `aggregate_preferences_by_query` 返回的查询组字典

**返回：**
- 转换后的样本列表，每个样本包含模型、查询、偏好分数等信息

**示例：**
```python
from llmrouter.utils.conversation import (
    extract_user_prompt,
    extract_model_response,
    aggregate_preferences_by_query,
    calculate_model_scores
)

# 提取用户提示
user_prompt = extract_user_prompt(conversation, turn=1)

# 提取模型响应
model_response = extract_model_response(conversation, turn=1)

# 聚合偏好
query_groups = aggregate_preferences_by_query(arena_data)

# 计算分数
scores = calculate_model_scores(query_groups)
```

---

## 进度跟踪

### progress.py

提供并行处理的进度跟踪功能。

**依赖：** `tqdm`

#### 类列表

##### `ProgressTracker`

进度跟踪器类，用于并行处理的进度显示。

**初始化参数：**
- `total`: 总任务数
- `desc`: 描述文本，默认 "Processing"

**方法：**

###### `update(success: bool = True, model_name: str = None)`
更新进度。

**参数：**
- `success`: 是否成功，默认 True
- `model_name`: 模型名称（可选）

###### `close()`
关闭进度条并打印统计信息。

**示例：**
```python
from llmrouter.utils import ProgressTracker

tracker = ProgressTracker(total=100, desc="Processing")

for i in range(100):
    # 处理任务
    success = process_item(i)
    tracker.update(success=success)

tracker.close()
```

---

## 模型加载

### model_loader.py

提供模型保存和加载的工具函数。

**依赖：** `torch`, `pickle`

#### 函数列表

##### `save_model(model: Any, filepath: str) -> bool`

保存模型到文件（支持 .pt 或 .pkl 格式）。

**参数：**
- `model`: 要保存的模型对象
- `filepath`: 完整文件路径（包括扩展名）

**返回：**
- 成功返回 `True`，失败返回 `False`

**示例：**
```python
from llmrouter.utils import save_model
import torch

model = torch.nn.Linear(10, 5)
save_model(model, "models/my_model.pt")
```

##### `load_model(filepath: str) -> Any`

从文件加载模型（支持 .pt 或 .pkl 格式）。

**参数：**
- `filepath`: 完整文件路径（包括扩展名）

**返回：**
- 加载的模型对象

**示例：**
```python
from llmrouter.utils import load_model

model = load_model("models/my_model.pt")
```

---

## 张量与 DataFrame 工具

### tensor_utils.py

张量处理工具。

**依赖：** `torch`, `ast`, `re`

#### 函数列表

##### `to_tensor(s: str) -> torch.Tensor`

将字符串表示转换为张量。

**参数：**
- `s`: 张量的字符串表示

**返回：**
- `torch.Tensor`

**示例：**
```python
from llmrouter.utils import to_tensor

tensor_str = "tensor([1.0, 2.0, 3.0])"
tensor = to_tensor(tensor_str)
```

### dataframe_utils.py

DataFrame 处理工具。

**依赖：** `pandas`

#### 函数列表

##### `clean_df(df)`

清理和标准化 DataFrame 列。

**参数：**
- `df`: 输入 DataFrame

**返回：**
- 清理后的 DataFrame

**执行的操作：**
- 删除 `query_embedding` 和 `formatted_query` 列
- 设置 `user_id` 和 `fig_id` 为 `None`
- 重命名列：
  - `prompt_tokens` → `input_tokens`
  - `completion_tokens` → `output_tokens`
  - `gt` → `ground_truth`

**示例：**
```python
from llmrouter.utils import clean_df

df_clean = clean_df(df)
```

---

## 常量与配置

### constants.py

定义项目常量和配置。

#### 常量

##### `TASK_DESCRIPTIONS: Dict[str, str]`
任务描述字典。

```python
{
    "natural_qa": 'Natural Questions consists of real Google search queries paired with full Wikipedia articles.',
    "trivia_qa": 'TriviaQA features complex trivia-style questions with evidence from multiple web sources.',
    "gsm8k": 'GSM8K is a benchmark of grade school math word problems.',
    # ... 更多任务
}
```

##### `TASK_CATEGORIES: Dict[str, List[str]]`
任务类别分类字典。

```python
{
    'MATH_TASK': ['gsm8k', 'math'],
    'CODE_TASK': ["mbpp", "human_eval"],
    'COMMONSENSE_TASK': ['commonsense_qa', 'openbook_qa', 'arc_challenge'],
    'WORLD_KNOWLEDGE_TASK': ["natural_qa", "trivia_qa"],
    'POPULAR_TASK': ["mmlu", "gpqa"],
    'PREFERENCE_TASK': ["mt_bench", "chatbot_arena"]
}
```

##### `HF_TOKEN: str`
Hugging Face token。

##### `CASE_NUM: int`
每个任务的样本数，默认 500。

##### `API_KEYS: str`
API 密钥配置。

---

## 环境设置

### setup.py

环境设置工具。

#### 函数列表

##### `setup_environment()`

设置公共环境变量和路径。

**执行的操作：**
- 设置 `KMP_DUPLICATE_LIB_OK='True'`（避免某些库的冲突）

**示例：**
```python
from llmrouter.utils import setup_environment

setup_environment()
```

---

## 路由器辅助工具

### router_helpers.py

为路由器提供辅助功能。

#### 函数列表

##### `format_api_request_with_task(query_text, task_name, api_endpoint, model_name, api_model_name, choices=None)`

使用任务特定的系统/用户提示格式格式化 API 请求。

**参数：**
- `query_text`: 原始查询文本
- `task_name`: 用于格式化的任务名称（如 "mmlu", "gsm8k"）
- `api_endpoint`: API 端点 URL
- `model_name`: 模型标识名称
- `api_model_name`: 实际 API 模型名称
- `choices`: 多选题的可选选项

**返回：**
- 包含 `query`、`system_prompt`、`api_endpoint`、`model_name`、`api_name` 字段的请求字典

**示例：**
```python
from llmrouter.utils import format_api_request_with_task

request = format_api_request_with_task(
    query_text="What is 2+2?",
    task_name="mmlu",
    api_endpoint="https://api.example.com/v1",
    model_name="model-1",
    api_model_name="provider/model-1",
    choices=["3", "4", "5", "6"]
)
```

---

## 使用示例

### 完整流程示例

```python
import os
os.environ['API_KEYS'] = 'your-api-key'

from llmrouter.utils import (
    load_jsonl,
    generate_embeddings_for_data,
    process_final_data,
    calculate_task_performance,
    format_api_request_with_task,
    call_api
)

# 1. 加载数据
data = load_jsonl("data.jsonl")

# 2. 生成嵌入
embedding_results = generate_embeddings_for_data(data, desc="Generating embeddings")

# 3. 格式化 API 请求
request = format_api_request_with_task(
    query_text="What is the capital of France?",
    task_name="mmlu",
    api_endpoint="https://api.example.com/v1",
    model_name="model-1",
    api_model_name="provider/model-1"
)

# 4. 调用 API
result = call_api(request)
print(result["response"])

# 5. 评估
score = calculate_task_performance(
    prediction=result["response"],
    ground_truth="Paris",
    task_name="mmlu"
)
print(f"Score: {score}")
```

### 进度跟踪示例

```python
from llmrouter.utils import ProgressTracker

tracker = ProgressTracker(total=100, desc="Processing queries")

for i in range(100):
    # 处理任务
    success = process_query(queries[i])
    tracker.update(success=success, model_name="gpt-4")

tracker.close()
```

### 自定义任务提示词

```python
from llmrouter.utils import register_prompt, generate_task_query, register_task_metric

# 注册自定义任务
@register_prompt('translation', default_metric='translation_bleu')
def format_translation_prompt(sample_data):
    return {
        "system": "You are a professional translator.",
        "user": f"Translate to English: {sample_data['query']}"
    }

# 使用自定义任务
prompt = generate_task_query(
    task_name="translation",
    sample_data={"query": "你好，世界！"}
)

# 注册评估指标
register_task_metric('translation', 'bleu_score')
```

---

## 依赖说明

### 核心依赖（必需）
- `pandas`: 数据处理
- `numpy`: 数值计算
- `torch`: 深度学习框架
- `transformers`: 模型和分词器
- `tqdm`: 进度条

### 可选依赖
- `litellm`: API 调用（用于 `api_calling.py` 和 `model_prompting`）
- `bert-score`: BERT 评估指标（用于 `get_bert_score`）
- `openai`: OpenAI API 客户端（用于 `model_prompting`）

### 安装可选依赖
```bash
pip install litellm bert-score openai
```

---

## 注意事项

1. **API 密钥配置**: 使用 `call_api` 前，需要设置 `API_KEYS` 环境变量。
2. **嵌入设备选择**: 可以通过 `LLMROUTER_EMBEDDING_DEVICE` 环境变量指定嵌入生成的设备。
3. **评估指标扩展**: 可以通过 `register_task_metric` 注册自定义评估指标。
4. **提示词扩展**: 可以通过 `register_prompt` 装饰器为自定义任务注册提示词格式化函数。
5. **线程安全**: `ProgressTracker` 使用锁机制，确保在多线程环境下的线程安全。
6. **错误处理**: 所有函数都包含错误处理，失败时会返回 `None` 或抛出异常。

---

## 许可证

请参考项目根目录的 LICENSE 文件。
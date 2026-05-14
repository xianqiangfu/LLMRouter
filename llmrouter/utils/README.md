# llmrouter/utils 工具模块

本目录包含 LLMRouter 项目的核心工具模块，提供 API 调用、嵌入生成、数据处理、对话管理和评估等功能。

## 目录结构

```
llmrouter/utils/
├── __init__.py              # 模块初始化，导出公共接口
├── api_calling.py           # API 调用工具
├── embeddings.py            # 嵌入生成工具
├── data_processing.py       # 数据处理工具
├── data_loader.py           # 数据加载工具
├── data_convert.py          # 数据格式转换工具
├── conversation.py          # 对话管理工具
├── arena_conversation.py    # Arena 对话管理工具
├── evaluation.py            # 评估指标工具
├── prompting.py             # 提示词格式化工具
├── router_helpers.py        # 路由辅助工具
├── constants.py             # 常量配置
├── progress.py              # 进度跟踪工具
├── dataframe_utils.py       # DataFrame 工具
├── tensor_utils.py          # 张量工具
├── model_loader.py          # 模型加载工具
└── setup.py                 # 环境设置工具
```

## 功能说明

### 1. API 调用功能

`api_calling.py` 提供统一的 API 调用接口，支持多种 LLM 服务提供商。

**核心功能:**
- 手动轮询负载均衡：在多个 API 密钥之间自动分配请求
- 支持单次请求和批量请求
- 支持服务特定的 API 密钥配置
- 自动重试机制和错误处理
- Token 统计和响应时间跟踪

**关键函数:**

```python
call_api(request, max_tokens=512, temperature=0.01, ...)
```

- 支持单个请求或批量请求
- 自动使用轮询算法分配 API 密钥
- 返回包含响应、token 数量和执行时间的结果

**API 密钥配置:**

支持多种格式的 `API_KEYS` 环境变量：

```python
# 字典格式（服务特定）
API_KEYS = '{"NVIDIA": "key1,key2", "OpenAI": ["key3", "key4"]}'

# 列表格式
API_KEYS = '["key1", "key2", "key3"]'

# 单个密钥
API_KEYS = "your-api-key"

# 逗号分隔
API_KEYS = "key1,key2,key3"
```

**使用示例:**

```python
from llmrouter.utils import call_api

request = {
    "api_endpoint": "https://integrate.api.nvidia.com/v1",
    "query": "What is 2+2?",
    "model_name": "qwen2.5-7b-instruct",
    "api_name": "qwen/qwen2.5-7b-instruct",
    "service": "NVIDIA"
}

result = call_api(request)
print(result["response"])
```

### 2. 嵌入功能

`embeddings.py` 提供 Longformer 模型的文本嵌入生成功能。

**核心功能:**
- 使用 allenai/longformer-base-4096 模型
- 支持最长 4096 tokens 的文本
- 自动设备选择（CUDA/MPS/CPU）
- 均值池化获取句子级嵌入
- 支持并行嵌入生成

**关键函数:**

```python
get_longformer_embedding(texts)
```

- 支持单个文本或文本列表
- 自动返回正确的张量形状
- 嵌入结果移动到 CPU 确保兼容性

```python
parallel_embedding_task(data)
```

- 用于多进程并行嵌入生成
- 返回 (id, embedding, success_flag) 元组

**使用示例:**

```python
from llmrouter.utils import get_longformer_embedding

# 单个文本
embedding = get_longformer_embedding("Hello, world!")
print(embedding.shape)  # (768,)

# 批量文本
embeddings = get_longformer_embedding(["text1", "text2", "text3"])
print(embeddings.shape)  # (3, 768)
```

**设备配置:**

可通过环境变量设置设备：

```bash
export LLMROUTER_EMBEDDING_DEVICE="cuda:0"
```

### 3. 数据处理功能

`data_processing.py`、`data_loader.py` 和 `data_convert.py` 提供完整的数据处理流水线。

#### 数据加载 (`data_loader.py`)

```python
load_csv(path)          # 加载 CSV 文件
load_jsonl(path)        # 加载 JSONL 文件
jsonl_to_csv(jsonl_path)  # JSONL 转 CSV
load_pt(path)           # 加载 PyTorch .pt 文件
```

#### 数据处理 (`data_processing.py`)

```python
process_final_data(df_all)
```

- 处理最终数据以匹配路由格式
- 提取唯一查询嵌入
- 生成嵌入 ID 并保存为 .pt 文件
- 将数据分割为训练/测试集（80/20）
- 保存为 JSONL 格式

```python
process_unified_embeddings_and_routing(...)
```

- 处理训练和测试数据的统一嵌入
- 创建顺序嵌入 ID（0, 1, 2, ...）
- 映射嵌入 ID 到路由数据
- 保存统一嵌入文件和路由数据

```python
generate_embeddings_for_data(data, desc)
```

- 为数据列表生成嵌入
- 使用线程池并行处理
- 返回嵌入结果列表

#### 数据转换 (`data_convert.py`)

提供命令行工具用于数据格式转换：

```bash
# 转换测试数据
python data_convert.py --input default_routing_test_data.jsonl \
                       --output router_test_data_nq.json \
                       --mode test

# 使用 LLM 生成缺失字段
python data_convert.py --input default_routing_test_data.jsonl \
                       --output router_test_data_nq.json \
                       --mode test --use-llm --workers 10

# 转换训练数据
python data_convert.py --input default_routing_train_data.jsonl \
                       --output router_train_data_nq.json \
                       --mode train

# 合并训练和测试数据
python data_convert.py --test-file router_test_data_nq.json \
                       --train-file router_train_data_nq.json \
                       --output train_test_nq.jsonl \
                       --mode merge
```

**使用示例:**

```python
from llmrouter.utils import (
    load_csv, load_jsonl,
    process_final_data,
    generate_embeddings_for_data
)

# 加载数据
data = load_jsonl("data.jsonl")

# 生成嵌入
embeddings = generate_embeddings_for_data(data, "Generating embeddings")

# 处理数据
df_train, df_test, embedding_dict = process_final_data(df_all)
```

### 4. 对话管理功能

`conversation.py` 和 `arena_conversation.py` 提供对话数据处理和管理功能。

#### 标准对话管理 (`conversation.py`)

```python
extract_user_prompt(conversation, turn=1)
```

- 从对话中提取指定轮次的用户提示
- 支持字符串和列表格式
- 自动处理 JSON 解析

```python
extract_model_response(conversation, turn=1)
```

- 从对话中提取指定轮次的模型响应
- 支持多轮对话

```python
aggregate_preferences_by_query(data, turn_filter=None)
```

- 按查询聚合所有成对偏好
- 支持按轮次过滤
- 创建偏好矩阵和胜率统计

```python
calculate_model_scores(query_groups)
```

- 为每个模型计算评估分数
- 模型有胜出则得 1.0 分，否则 0.0 分

#### Arena 对话管理 (`arena_conversation.py`)

Arena 专用版本，处理 OpenAI 格式的对话数据：

```python
extract_arena_user_prompt(conversation_json)
extract_arena_model_response(conversation_json)
aggregate_arena_preferences_by_query(data)
calculate_arena_model_scores(query_groups)
```

**使用示例:**

```python
from llmrouter.utils import (
    extract_user_prompt,
    extract_model_response,
    aggregate_preferences_by_query,
    calculate_model_scores
)

# 提取对话内容
user_msg = extract_user_prompt(conversation, turn=1)
model_response = extract_model_response(conversation, turn=1)

# 聚合偏好并计算分数
query_groups = aggregate_preferences_by_query(data, turn_filter=1)
converted_data = calculate_model_scores(query_groups)
```

### 5. 评估功能

`evaluation.py` 提供多种评估指标。

**关键指标函数:**

```python
f1_score(prediction, ground_truth)
```

- 计算 F1 分数、精确率和召回率
- 处理特殊答案格式（yes/no/noanswer）

```python
exact_match_score(prediction, ground_truth, normal_method="")
```

- 计算精确匹配分数
- 支持多种标准化方法
- 特殊处理多选题（"mc" 模式）

```python
cem_score(prediction, ground_truth)
```

- 包含匹配分数
- 完全匹配或包含即得 1.0 分

```python
calculate_task_performance(prediction, ground_truth, task_name, metric)
```

- 统一的任务性能评估接口
- 自动根据任务名称选择评估指标
- 支持自定义评估指标

```python
evaluate_code(generated_code, test_cases, timeout=5)
```

- 评估生成的代码是否通过测试用例
- 支持超时设置
- 安全执行环境

```python
get_bert_score(generate_response, ground_truth)
```

- 计算 BERT 分数
- 需要额外依赖 `bert-score`

**使用示例:**

```python
from llmrouter.utils import (
    f1_score, exact_match_score, cem_score,
    calculate_task_performance, evaluate_code
)

# 计算 F1 分数
f1, precision, recall = f1_score(
    prediction="The capital of France is Paris.",
    ground_truth="Paris is the capital of France."
)

# 计算任务性能
score = calculate_task_performance(
    prediction="4",
    ground_truth="The answer is 4.",
    task_name="gsm8k",
    metric="gsm8k"
)

# 评估代码
passed = evaluate_code(
    generated_code="def add(a, b): return a + b",
    test_cases=["assert add(2, 3) == 5"]
)
```

### 6. 提示词格式化功能

`prompting.py` 提供各种任务的提示词格式化。

**内置任务格式化器:**

```python
format_mc_prompt(question, choices)
```

- 多选题格式化
- 自动生成 A/B/C/D 选项

```python
format_gsm8k_prompt(query)
format_math_prompt(query)
```

- 数学问题格式化

```python
format_commonsense_qa_prompt(query, choices)
```

- 常识推理题格式化

```python
format_mbpp_prompt(text, tests)
format_humaneval_prompt(prompt)
```

- 代码生成任务格式化

```python
generate_task_query(task_name, sample_data)
```

- 统一的任务查询生成接口
- 根据任务名称自动选择格式化器
- 返回包含 system 和 user 提示的字典

**使用示例:**

```python
from llmrouter.utils.prompting import (
    format_mc_prompt, format_gsm8k_prompt,
    generate_task_query
)

# 多选题格式化
formatted = format_mc_prompt(
    question="What is 2+2?",
    choices=["3", "4", "5", "6"]
)

# 统一任务查询生成
task_query = generate_task_query(
    task_name="mmlu",
    sample_data={
        "query": "Question text",
        "choices": ["A", "B", "C", "D"]
    }
)
```

### 7. 辅助工具

#### 进度跟踪 (`progress.py`)

```python
from llmrouter.utils import ProgressTracker

tracker = ProgressTracker(total=100)
tracker.update(50)
tracker.close()
```

#### 常量配置 (`constants.py`)

```python
from llmrouter.utils import TASK_DESCRIPTIONS, TASK_CATEGORIES, CASE_NUM

# 任务描述
desc = TASK_DESCRIPTIONS["gsm8k"]

# 任务类别
math_tasks = TASK_CATEGORIES['MATH_TASK']  # ['gsm8k', 'math']

# 默认配置
samples = CASE_NUM  # 500
```

#### 路由辅助 (`router_helpers.py`)

```python
from llmrouter.utils import format_api_request_with_task

request = format_api_request_with_task(
    query_text="What is 2+2?",
    task_name="gsm8k",
    api_endpoint="https://api.example.com/v1",
    model_name="gpt-4",
    api_model_name="openai/gpt-4"
)
```

## 插件系统工作原理

LLMRouter 的工具模块提供了灵活的插件系统，允许用户自定义提示词格式化器和评估指标。

### 提示词插件注册

使用装饰器注册自定义提示词格式化器：

```python
from llmrouter.utils.prompting import register_prompt

@register_prompt('sentiment_analysis', default_metric='sentiment_f1')
def format_sentiment_analysis_prompt(sample_data):
    """自定义情感分析提示词格式化器"""
    query = sample_data['query']
    system_prompt = "你是一个情感分析专家..."
    user_query = f"分析以下文本的情感：{query}"
    return {"system": system_prompt, "user": user_query}
```

**工作原理:**

1. `@register_prompt` 装饰器将函数注册到 `PROMPT_REGISTRY` 字典
2. 可选的 `default_metric` 参数将任务映射到评估指标
3. 当调用 `generate_task_query()` 时，系统首先检查 `PROMPT_REGISTRY`
4. 如果找到匹配的任务名称，使用自定义格式化器
5. 否则使用内置格式化器

### 评估指标注册

使用函数注册默认评估指标：

```python
from llmrouter.utils.prompting import register_task_metric

register_task_metric('sentiment_analysis', 'sentiment_f1')
```

**工作原理:**

1. 将任务名称映射到评估指标名称
2. 当调用 `calculate_task_performance()` 且未指定 metric 时
3. 系统首先检查 `TASK_METRIC_REGISTRY`
4. 如果找到映射，使用对应的评估指标
5. 否则使用默认的内置映射规则

### 自定义评估指标

在 `llmrouter/evaluation/batch_evaluator.py` 中注册自定义评估指标：

```python
from llmrouter.evaluation.batch_evaluator import EVALUATION_METRICS

def sentiment_f1(prediction, ground_truth):
    """自定义情感分析 F1 评估"""
    # 实现评估逻辑
    return score

# 注册到评估指标字典
EVALUATION_METRICS['sentiment_f1'] = sentiment_f1
```

**插件系统优势:**

1. **扩展性**: 无需修改核心代码即可添加新任务和指标
2. **灵活性**: 用户可以为特定任务定制提示词和评估方法
3. **一致性**: 统一的注册机制确保接口一致
4. **优先级**: 自定义插件优先于内置实现

## 关键工具函数列表

### API 调用
- `call_api()` - 统一 API 调用接口
- `_parse_api_keys()` - 解析 API 密钥配置
- `_get_api_key()` - 轮询选择 API 密钥

### 嵌入生成
- `get_longformer_embedding()` - 生成 Longformer 嵌入
- `parallel_embedding_task()` - 并行嵌入生成

### 数据加载
- `load_csv()` - 加载 CSV 文件
- `load_jsonl()` - 加载 JSONL 文件
- `load_pt()` - 加载 PyTorch 文件

### 数据处理
- `process_final_data()` - 处理最终路由数据
- `process_unified_embeddings_and_routing()` - 处理统一嵌入
- `generate_embeddings_for_data()` - 批量生成嵌入

### 对话管理
- `extract_user_prompt()` - 提取用户提示
- `extract_model_response()` - 提取模型响应
- `aggregate_preferences_by_query()` - 聚合偏好数据
- `calculate_model_scores()` - 计算模型分数

### 评估指标
- `f1_score()` - 计算 F1 分数
- `exact_match_score()` - 计算精确匹配
- `cem_score()` - 计算包含匹配分数
- `calculate_task_performance()` - 统一评估接口
- `evaluate_code()` - 评估代码生成

### 提示词格式化
- `format_mc_prompt()` - 多选题格式化
- `format_gsm8k_prompt()` - GSM8K 格式化
- `format_math_prompt()` - MATH 格式化
- `generate_task_query()` - 统一任务查询生成

## 关键工具类列表

- `ProgressTracker` - 进度跟踪类
- `PROMPT_REGISTRY` - 提示词插件注册表（字典）
- `TASK_METRIC_REGISTRY` - 任务指标映射表（字典）
- `EVALUATION_METRICS` - 评估指标注册表（字典）

## 配置常量

### 任务描述 (TASK_DESCRIPTIONS)
包含所有支持的任务描述信息：
- 自然问答：natural_qa, trivia_qa
- 数学推理：gsm8k, math
- 常识推理：commonsense_qa, openbook_qa, arc_challenge
- 代码生成：mbpp, human_eval
- 其他：mmlu, gpqa, mt_bench, chatbot_arena

### 任务类别 (TASK_CATEGORIES)
按能力分类的任务：
- MATH_TASK: 数学推理任务
- CODE_TASK: 代码生成任务
- COMMONSENSE_TASK: 常识推理任务
- WORLD_KNOWLEDGE_TASK: 世界知识任务
- PREFERENCE_TASK: 偏好评估任务

### 默认配置
- `CASE_NUM`: 每个任务的默认样本数（500）

## 依赖说明

### 核心依赖
- `torch` - PyTorch 深度学习框架
- `transformers` - Hugging Face 变换器库
- `pandas` - 数据处理
- `numpy` - 数值计算
- `tqdm` - 进度条

### 可选依赖
- `litellm` - API 调用（必需）
- `openai` - OpenAI API 客户端
- `bert-score` - BERT 评估指标
- `sentence-transformers` - 句子嵌入

## 安装

```bash
# 安装核心依赖
pip install torch transformers pandas numpy tqdm litellm

# 安装可选依赖
pip install openai bert-score sentence-transformers
```

## 使用示例

### 完整工作流示例

```python
from llmrouter.utils import (
    load_jsonl, generate_embeddings_for_data,
    process_final_data, call_api, calculate_task_performance
)

# 1. 加载数据
data = load_jsonl("data.jsonl")

# 2. 生成嵌入
embeddings = generate_embeddings_for_data(data)

# 3. 为数据添加嵌入列
for i, (_, embedding, success) in enumerate(embeddings):
    if success:
        data[i]['query_embedding'] = embedding

# 4. 调用 API 获取响应
for item in data:
    request = {
        "api_endpoint": "https://api.example.com/v1",
        "query": item['query'],
        "model_name": "gpt-4",
        "api_name": "openai/gpt-4"
    }
    result = call_api(request)
    item['response'] = result['response']
    item['token_num'] = result['token_num']

# 5. 评估响应
for item in data:
    item['performance'] = calculate_task_performance(
        prediction=item['response'],
        ground_truth=item['ground_truth'],
        task_name=item['task_name']
    )

# 6. 处理最终数据
df_train, df_test, embedding_dict = process_final_data(data)
```

## 贡献指南

如需添加新的工具函数或扩展现有功能：

1. 在相应的模块中添加函数
2. 在 `__init__.py` 中导出公共接口
3. 添加文档字符串和使用示例
4. 如适用，实现插件注册机制
5. 更新本文档

## 许可证

本项目遵循项目根目录的许可证。
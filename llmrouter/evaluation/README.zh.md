# Evaluation 包

`evaluation` 包提供了一个基于装饰器的高级接口，用于批量评估模型预测与真实答案的匹配度。它使用灵活的指标注册系统，让你可以轻松添加自定义评估指标。

## 概述

此包分离了关注点：
- **`llmrouter.utils.evaluation`**：底层工具函数（评分函数、文本标准化、嵌入向量等）
- **`llmrouter.evaluation`**：基于装饰器的高层批量评估接口

## 快速开始

```python
from llmrouter.evaluation import evaluate_batch

# 准备数据
data = [
    {'prediction': 'hello world', 'ground_truth': 'hello', 'metric': 'f1'},
    {'prediction': 'exact match', 'ground_truth': 'exact match', 'metric': 'em'}
]

# 评估
results = evaluate_batch(data)

# 结果包含原始数据加上 'score' 字段
for result in results:
    print(f"Score: {result['score']}")
```

## 评估指标和计算方法

### 内置指标

系统默认注册了以下评估指标：

| 指标 | 名称 | 适用场景 | 计算方法 |
|------|------|----------|----------|
| `em` | 完全匹配 | 答案需要完全相同的任务 | 预测和真实答案标准化后完全一致 |
| `em_mc` | 多选题完全匹配 | 多选题任务 | 从预测中提取选项标记，与真实答案比较 |
| `cem` | 包含匹配 | 答案可能包含在长文本中的任务 | 预测包含真实答案或完全匹配 |
| `cemf1` | 包含匹配+F1回退 | 通用问答任务 | 包含匹配失败时回退到 F1 分数 |
| `f1` | F1 分数 | 需要评估部分匹配的任务 | 精确率和召回率的调和平均数 |
| `bert_score` | BERT 语义相似度 | 需要语义相似度评估的任务 | 使用 BERT 模型计算语义相似度 |
| `gsm8k` | GSM8K 数学题评估 | 数学问题解决任务 | 提取并比较数字答案 |

### 评估指标详细计算方法

#### 1. 完全匹配 (EM)

**计算步骤**：
1. 对预测和真实答案进行标准化：
   - 转为小写
   - 移除冠词（a, an, the）
   - 移除标点符号
   - 统一空格
2. 比较标准化后的文本是否完全相同
3. 多选题模式（`em_mc`）会从预测中提取 `(A)`, `(B)` 等选项标记

**返回值**：`1.0`（匹配）或 `0.0`（不匹配）

#### 2. F1 分数

**计算步骤**：
1. 对预测和真实答案进行标准化（同上）
2. 将文本分词
3. 计算精确率（Precision）：
   ```
   Precision = 共同词数 / 预测词数
   ```
4. 计算召回率（Recall）：
   ```
   Recall = 共同词数 / 真实答案词数
   ```
5. 计算 F1 分数：
   ```
   F1 = 2 × (Precision × Recall) / (Precision + Recall)
   ```

**返回值**：`[0, 1]` 之间的浮点数

**特殊处理**：
- 如果标准化后答案为 `yes`、`no` 或 `noanswer` 且不匹配，直接返回 0
- 如果没有共同词，返回 0

#### 3. 包含匹配 (CEM)

**计算步骤**：
1. 对预测和真实答案进行标准化
2. 检查是否满足以下任一条件：
   - 标准化后的预测和真实答案完全相同
   - 标准化后的真实答案包含在预测中

**返回值**：`1.0`（匹配）或 `0.0`（不匹配）

#### 4. CEMF1（包含匹配 + F1 回退）

**计算步骤**：
1. 先尝试 CEM 评估
2. 如果 CEM 不匹配，则回退到 F1 分数
3. 返回最高分

**返回值**：`[0, 1]` 之间的浮点数

#### 5. BERT Score

**计算步骤**：
1. 使用预训练的 BERT 模型（如 `bert-base-uncased`）
2. 计算预测和真实答案之间的词嵌入
3. 计算精确率、召回率和 F1 分数（基于嵌入的余弦相似度）

**返回值**：平均 F1 分数（`[0, 1]` 之间的浮点数）

**依赖**：需要安装 `bert-score` 包：
```bash
pip install bert-score
```

#### 6. GSM8K 评估

**计算步骤**：
1. 从真实答案中提取数字（格式：`#### 123`）
2. 清理数字（移除逗号、美元符号、小数点）
3. 从预测中提取最后一个有效数字
4. 比较两个数字是否相同

**返回值**：`1.0`（匹配）或 `0.0`（不匹配）

#### 7. 文本标准化处理

所有指标（除 BERT Score 外）都使用以下标准化流程：

```python
def normalize_answer(s):
    # 1. 移除冠词 (a, an, the)
    s = remove_articles(s)

    # 2. 转为小写
    s = lower(s)

    # 3. 移除标点符号
    s = remove_punc(s)

    # 4. 统一空格
    s = white_space_fix(s)

    return s
```

## 批量评估器功能

### 架构

评估系统使用**装饰器模式**配合**注册表**：

```
┌─────────────────┐
│  Metric Registry │
│ EVALUATION_METRICS│
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  @evaluation_metric     │
│  装饰器注册指标函数      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  evaluate_batch()       │
│  批量评估处理            │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Metric Function        │
│  执行具体评估逻辑        │
└─────────────────────────┘
```

### 工作流程

```
输入数据 → 指标查找 → 指标函数 → 评分 → 输出数据
   ↓          ↓          ↓        ↓        ↓
[dict]    EVALUATION_   eval_func  float   [dict+score]
          METRICS
```

1. 输入列表中的每个项目指定一个 `metric` 名称
2. `evaluate_batch()` 从 `EVALUATION_METRICS` 注册表中查找指标函数
3. 指标函数使用 `prediction`、`ground_truth` 和任何额外的 kwargs 被调用
4. 分数被添加到结果字典中

### 主要功能

#### 1. 批量评估

```python
from llmrouter.evaluation import evaluate_batch

data = [
    {'prediction': 'hello', 'ground_truth': 'hello', 'metric': 'em'},
    {'prediction': 'world', 'ground_truth': 'word', 'metric': 'f1'},
    {'prediction': 'long answer', 'ground_truth': 'answer', 'metric': 'cem'}
]

results = evaluate_batch(data)
```

#### 2. 默认指标

```python
# 为所有没有指定 'metric' 的项目使用默认指标
results = evaluate_batch(data, default_metric='em')
```

#### 3. 自定义参数传递

```python
data = [
    {
        'prediction': 'hello world',
        'ground_truth': 'world',
        'metric': 'custom_metric',
        'threshold': 0.8,  # 自定义参数
        'min_length': 5    # 自定义参数
    }
]

results = evaluate_batch(data)
```

#### 4. 错误处理

如果评估失败：
- 分数设置为 `0.0`
- 添加 `evaluation_error` 字段包含错误信息
- 保留原始数据
- 打印警告信息

### 可用功能

| 函数 | 描述 |
|------|------|
| `evaluate_batch(data, default_metric)` | 批量评估预测数据 |
| `evaluation_metric(name)` | 注册指标的装饰器 |
| `register_custom_metric(name, func)` | 以编程方式注册指标 |
| `get_available_metrics()` | 列出所有已注册的指标 |
| `EVALUATION_METRICS` | 指标注册表字典 |

## 注册自定义指标

### 方法 1：使用装饰器（推荐）

创建一个包含自定义指标的 Python 文件：

```python
# custom_metrics/my_metrics.py
from llmrouter.evaluation import evaluation_metric

@evaluation_metric('my_custom_metric')
def my_eval_function(prediction: str, ground_truth: str, threshold: float = 0.5, **kwargs) -> float:
    """
    你的自定义评估逻辑。

    Args:
        prediction: 预测的文本
        ground_truth: 真实答案文本
        threshold: 自定义参数（通过数据字典传递）
        **kwargs: 数据字典中的其他参数

    Returns:
        评估分数（浮点数）
    """
    # 你的评估逻辑
    return 1.0 if len(prediction) > threshold else 0.0
```

然后导入模块以注册它：

```python
# main.py
from llmrouter.evaluation import evaluate_batch
import custom_metrics.my_metrics  # 导入触发装饰器注册

data = [
    {'prediction': 'hello', 'ground_truth': 'world', 'metric': 'my_custom_metric', 'threshold': 3}
]
results = evaluate_batch(data)
```

**重要**：必须导入模块才能执行装饰器并注册指标。

### 方法 2：编程方式注册

```python
from llmrouter.evaluation import register_custom_metric, evaluate_batch

def my_metric(prediction: str, ground_truth: str, **kwargs) -> float:
    return 1.0 if prediction == ground_truth else 0.0

register_custom_metric('my_metric', my_metric)

# 现在使用它
results = evaluate_batch([
    {'prediction': 'hi', 'ground_truth': 'hello', 'metric': 'my_metric'}
])
```

## 指标函数签名

所有指标函数必须遵循此签名：

```python
def metric_function(
    prediction: str,      # 必需：预测文本
    ground_truth: str,     # 必需：真实答案文本
    **kwargs               # 可选：数据字典中的额外参数
) -> float:               # 必需：返回浮点数分数
    ...
```

数据字典中的额外参数（除了 `prediction`、`ground_truth` 和 `metric`）作为 `**kwargs` 传递。

## 评估流程说明

### 完整评估流程

```
1. 准备数据阶段
   ↓
   ┌─────────────────────────────────┐
   │ data = [                        │
   │   {'prediction': '...',         │
   │    'ground_truth': '...',       │
   │    'metric': 'em'},             │
   │   ...                           │
   │ ]                               │
   └─────────────────────────────────┘
           ↓
2. 调用批量评估
   ↓
   ┌─────────────────────────────────┐
   │ results = evaluate_batch(data)  │
   └─────────────────────────────────┘
           ↓
3. 遍历每个数据项
   ↓
   ┌─────────────────────────────────┐
   │ for item in data:               │
   │   - 验证必需字段                 │
   │   - 获取指标名称                 │
   │   - 查找指标函数                 │
   └─────────────────────────────────┘
           ↓
4. 执行指标计算
   ↓
   ┌─────────────────────────────────┐
   │ score = eval_function(          │
   │     prediction,                 │
   │     ground_truth,               │
   │     **kwargs                    │
   │ )                               │
   └─────────────────────────────────┘
           ↓
5. 添加分数到结果
   ↓
   ┌─────────────────────────────────┐
   │ result = item.copy()            │
   │ result['score'] = score         │
   └─────────────────────────────────┘
           ↓
6. 返回结果列表
   ↓
   ┌─────────────────────────────────┐
   │ results = [                     │
   │   {..., 'score': 0.95},         │
   │   {..., 'score': 0.87},         │
   │   ...                           │
   │ ]                               │
   └─────────────────────────────────┘
```

### 评估流程步骤详解

#### 步骤 1：准备数据

准备包含预测和真实答案的数据列表：

```python
data = [
    {
        'prediction': '模型预测的答案',
        'ground_truth': '真实答案',
        'metric': 'em'  # 可选的额外参数
    },
    # ... 更多数据项
]
```

#### 步骤 2：调用批量评估

```python
results = evaluate_batch(
    data,               # 数据列表
    default_metric='f1' # 可选：默认指标
)
```

#### 步骤 3：验证和处理

系统对每个数据项执行：
1. 验证必需字段（`prediction` 和 `ground_truth`）
2. 获取指标名称（从数据项或默认值）
3. 检查指标是否已注册
4. 提取额外参数作为 kwargs

#### 步骤 4：执行指标计算

调用注册的指标函数：
```python
score = metric_function(
    prediction=item['prediction'],
    ground_truth=item['ground_truth'],
    **kwargs  # 额外参数
)
```

#### 步骤 5：错误处理

如果计算失败：
- 分数设置为 `0.0`
- 添加错误信息到 `evaluation_error` 字段
- 保留原始数据
- 打印警告

#### 步骤 6：返回结果

返回包含原始数据和分数的结果列表：
```python
[
    {'prediction': '...', 'ground_truth': '...', 'metric': 'em', 'score': 1.0},
    {'prediction': '...', 'ground_truth': '...', 'metric': 'f1', 'score': 0.75},
    ...
]
```

## 示例

### 基本用法

```python
from llmrouter.evaluation import evaluate_batch

data = [
    {'prediction': 'hello', 'ground_truth': 'hello', 'metric': 'em'},
    {'prediction': 'world', 'ground_truth': 'word', 'metric': 'f1'}
]

results = evaluate_batch(data)
# [
#     {'prediction': 'hello', 'ground_truth': 'hello', 'metric': 'em', 'score': 1.0},
#     {'prediction': 'world', 'ground_truth': 'word', 'metric': 'f1', 'score': 0.5}
# ]
```

### 使用默认指标

```python
results = evaluate_batch(data, default_metric='em')
# 所有没有 'metric' 键的项目将使用 'em'
```

### 带参数的自定义指标

```python
# 注册自定义指标
@evaluation_metric('length_check')
def length_metric(prediction: str, ground_truth: str, min_length: int = 5, **kwargs) -> float:
    return 1.0 if len(prediction) >= min_length else 0.0

# 使用它
data = [
    {
        'prediction': 'This is a long text',
        'ground_truth': 'short',
        'metric': 'length_check',
        'min_length': 10  # 作为 kwargs 传递
    }
]
results = evaluate_batch(data)
```

### 查看可用指标

```python
from llmrouter.evaluation import get_available_metrics

print(get_available_metrics())
# ['em', 'em_mc', 'cem', 'cemf1', 'f1', 'bert_score', 'gsm8k', ...]
```

## 与 `utils.evaluation` 的关系

`evaluation` 包使用 `llmrouter.utils.evaluation` 中的工具函数：

- 内置指标包装了 `f1_score()`、`exact_match_score()` 等工具函数
- 你也可以在你的自定义指标中直接使用这些工具：

```python
from llmrouter.utils.evaluation import f1_score, exact_match_score

@evaluation_metric('my_hybrid_metric')
def hybrid_metric(prediction: str, ground_truth: str, **kwargs) -> float:
    f1, _, _ = f1_score(prediction, ground_truth)
    em = exact_match_score(prediction, ground_truth)
    return (f1 + float(em)) / 2.0
```

## 更多示例

查看此目录中的 `example.py` 以获取综合示例，包括：
- 多种自定义指标注册方法
- 使用不同的内置指标
- 将自定义参数传递给指标

## API 参考

### 主要函数

- `evaluate_batch(data, default_metric=None)` - 批量评估预测
- `evaluation_metric(name)` - 注册指标的装饰器
- `register_custom_metric(name, func)` - 以编程方式注册指标
- `get_available_metrics()` - 列出所有已注册的指标

### 注册表

- `EVALUATION_METRICS` - 将指标名称映射到函数的字典
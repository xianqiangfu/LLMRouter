# 评估系统说明

## 简介

`evaluation` 包提供了一个基于装饰器的高级接口，用于批量评估模型预测与真实答案的匹配度。它使用灵活的指标注册系统，让您可以轻松添加自定义评估指标。

该系统采用分层设计：
- **`llmrouter.utils.evaluation`**：底层工具函数，提供评分函数、文本标准化、嵌入向量计算等功能
- **`llmrouter.evaluation`**：高层批量评估接口，基于装饰器的指标注册系统

## 评估系统架构

### 架构设计

评估系统采用**装饰器模式**配合**注册表**的设计：

```
┌─────────────────────────────────────────────────────────┐
│                    评估系统架构                           │
└─────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  Metric Registry     │  ← 全局指标注册表
│  EVALUATION_METRICS  │
└──────────┬───────────┘
           │ 注册
           ▼
┌──────────────────────┐
│  @evaluation_metric  │  ← 装饰器注册指标函数
│  Decorator           │
└──────────┬───────────┘
           │ 执行
           ▼
┌──────────────────────┐
│  evaluate_batch()    │  ← 批量评估处理器
│  Batch Evaluator     │
└──────────┬───────────┘
           │ 调用
           ▼
┌──────────────────────┐
│  Metric Functions    │  ← 具体评估指标函数
│  (em, f1, bert...)   │
└──────────────────────┘
```

### 核心组件

1. **指标注册表（EVALUATION_METRICS）**
   - 全局字典，存储所有已注册的评估指标
   - 键：指标名称（如 `'em'`, `'f1'`）
   - 值：评估函数对象

2. **装饰器（@evaluation_metric）**
   - 用于注册自定义评估指标
   - 自动将函数注册到全局注册表

3. **批量评估器（evaluate_batch）**
   - 处理批量评估请求
   - 从注册表查找指标函数
   - 执行评估并返回结果

### 工作流程

```
输入数据 → 指标查找 → 指标函数 → 评分计算 → 输出数据
   ↓          ↓          ↓          ↓         ↓
[dict]    EVALUATION_   eval_func  float   [dict+score]
          METRICS
```

1. **数据准备**：准备包含 `prediction`、`ground_truth` 和 `metric` 字段的数据列表
2. **指标查找**：`evaluate_batch()` 从 `EVALUATION_METRICS` 注册表查找对应的指标函数
3. **参数传递**：将 `prediction`、`ground_truth` 和额外参数（kwargs）传递给指标函数
4. **评分计算**：指标函数执行具体的评估逻辑，返回分数
5. **结果返回**：将分数添加到原始数据字典中，返回完整结果

## 评估指标列表

### 内置指标

系统默认注册了以下评估指标：

| 指标名称 | 全称 | 适用场景 | 计算方法 | 返回值范围 |
|---------|------|---------|---------|-----------|
| `em` | Exact Match | 答案需要完全相同的任务 | 标准化后文本完全一致 | 0.0 或 1.0 |
| `em_mc` | Exact Match (Multiple Choice) | 多选题任务 | 提取选项标记后比较 | 0.0 或 1.0 |
| `cem` | Contains Exact Match | 答案可能包含在长文本中的任务 | 预测包含真实答案或完全匹配 | 0.0 或 1.0 |
| `cemf1` | Contains Exact Match with F1 Fallback | 通用问答任务 | CEM 失败时回退到 F1 分数 | [0, 1] |
| `f1` | F1 Score | 需要评估部分匹配的任务 | 精确率和召回率的调和平均数 | [0, 1] |
| `bert_score` | BERT Semantic Similarity | 需要语义相似度评估的任务 | BERT 模型计算语义相似度 | [0, 1] |
| `gsm8k` | GSM8K Math Problem | 数学问题解决任务 | 提取并比较数字答案 | 0.0 或 1.0 |

### 指标详细说明

#### 1. 完全匹配 (EM)

**适用场景**：答案需要完全一致的任务，如分类任务、实体抽取等。

**计算步骤**：
1. 对预测和真实答案进行标准化：
   - 转为小写
   - 移除冠词（a, an, the）
   - 移除标点符号
   - 统一空格
2. 比较标准化后的文本是否完全相同

**返回值**：`1.0`（匹配）或 `0.0`（不匹配）

#### 2. 多选题完全匹配 (EM_MC)

**适用场景**：多选题任务，需要从选项中选择正确答案。

**计算步骤**：
1. 从预测中提取选项标记（如 `(A)`, `(B)` 等）
2. 将提取的选项与真实答案比较

**返回值**：`1.0`（匹配）或 `0.0`（不匹配）

#### 3. 包含匹配 (CEM)

**适用场景**：答案可能包含在较长文本中的任务，如阅读理解、信息检索等。

**计算步骤**：
1. 对预测和真实答案进行标准化
2. 检查是否满足以下任一条件：
   - 标准化后的预测和真实答案完全相同
   - 标准化后的真实答案包含在预测中

**返回值**：`1.0`（匹配）或 `0.0`（不匹配）

#### 4. 包含匹配 + F1 回退 (CEMF1)

**适用场景**：通用问答任务，在包含匹配失败时提供更细致的评分。

**计算步骤**：
1. 先尝试 CEM 评估
2. 如果 CEM 不匹配，则回退到 F1 分数
3. 返回最高分

**返回值**：`[0, 1]` 之间的浮点数

#### 5. F1 分数

**适用场景**：需要评估部分匹配的任务，如答案包含多个关键词的场景。

**计算步骤**：
1. 对预测和真实答案进行标准化
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

#### 6. BERT Score

**适用场景**：需要语义相似度评估的任务，如答案改写、同义替换等。

**计算步骤**：
1. 使用预训练的 BERT 模型（如 `bert-base-uncased`）
2. 计算预测和真实答案之间的词嵌入
3. 计算精确率、召回率和 F1 分数（基于嵌入的余弦相似度）

**返回值**：平均 F1 分数（`[0, 1]` 之间的浮点数）

**依赖**：需要安装 `bert-score` 包：
```bash
pip install bert-score
```

#### 7. GSM8K 数学题评估

**适用场景**：数学问题解决任务，需要评估计算结果。

**计算步骤**：
1. 从真实答案中提取数字（格式：`#### 123`）
2. 清理数字（移除逗号、美元符号、小数点）
3. 从预测中提取最后一个有效数字
4. 比较两个数字是否相同

**返回值**：`1.0`（匹配）或 `0.0`（不匹配）

### 文本标准化流程

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

## 评估方法和流程

### 完整评估流程

```
1. 准备数据阶段
   ↓
   ┌──────────────────────────────────────┐
   │ data = [                             │
   │   {'prediction': '预测答案1',       │
   │    'ground_truth': '真实答案1',      │
   │    'metric': 'em'},                  │
   │   {'prediction': '预测答案2',       │
   │    'ground_truth': '真实答案2',      │
   │    'metric': 'f1'},                  │
   │ ]                                    │
   └──────────────────────────────────────┘
           ↓
2. 调用批量评估
   ↓
   ┌──────────────────────────────────────┐
   │ results = evaluate_batch(data)       │
   └──────────────────────────────────────┘
           ↓
3. 遍历每个数据项
   ↓
   ┌──────────────────────────────────────┐
   │ for item in data:                    │
   │   - 验证必需字段                      │
   │   - 获取指标名称                      │
   │   - 查找指标函数                      │
   │   - 提取额外参数 (kwargs)             │
   └──────────────────────────────────────┘
           ↓
4. 执行指标计算
   ↓
   ┌──────────────────────────────────────┐
   │ score = eval_function(               │
   │     prediction=item['prediction'],   │
   │     ground_truth=item['ground_truth'],│
   │     **kwargs                         │
   │ )                                    │
   └──────────────────────────────────────┘
           ↓
5. 添加分数到结果
   ↓
   ┌──────────────────────────────────────┐
   │ result = item.copy()                 │
   │ result['score'] = score              │
   └──────────────────────────────────────┘
           ↓
6. 返回结果列表
   ↓
   ┌──────────────────────────────────────┐
   │ results = [                          │
   │   {..., 'score': 1.0},               │
   │   {..., 'score': 0.75},              │
   │   ...                                │
   │ ]                                    │
   └──────────────────────────────────────┘
```

### 评估步骤详解

#### 步骤 1：准备数据

准备包含预测和真实答案的数据列表：

```python
data = [
    {
        'prediction': '模型预测的答案',
        'ground_truth': '真实答案',
        'metric': 'em',  # 指定使用的评估指标
        'threshold': 0.8  # 可选的自定义参数
    },
    # ... 更多数据项
]
```

**必需字段**：
- `prediction`：模型预测的答案（字符串）
- `ground_truth`：真实答案（字符串）
- `metric`：评估指标名称（可选，可通过 default_metric 指定）

**可选字段**：
- 任何额外参数都会作为 kwargs 传递给评估函数

#### 步骤 2：调用批量评估

```python
from llmrouter.evaluation import evaluate_batch

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
- 打印警告信息

#### 步骤 6：返回结果

返回包含原始数据和分数的结果列表：

```python
[
    {'prediction': '...', 'ground_truth': '...', 'metric': 'em', 'score': 1.0},
    {'prediction': '...', 'ground_truth': '...', 'metric': 'f1', 'score': 0.75},
    ...
]
```

## 评估指南

### 快速开始

```python
from llmrouter.evaluation import evaluate_batch

# 准备数据
data = [
    {'prediction': 'hello world', 'ground_truth': 'hello', 'metric': 'f1'},
    {'prediction': 'exact match', 'ground_truth': 'exact match', 'metric': 'em'}
]

# 评估
results = evaluate_batch(data)

# 查看结果
for result in results:
    print(f"Score: {result['score']}")
```

### 选择合适的评估指标

| 任务类型 | 推荐指标 | 理由 |
|---------|---------|------|
| 分类任务 | `em` | 需要完全匹配 |
| 多选题 | `em_mc` | 专门处理选项标记 |
| 阅读理解 | `cem` | 答案通常包含在文本中 |
| 问答任务 | `cemf1` | 在包含匹配失败时提供更细致的评分 |
| 关键词提取 | `f1` | 评估部分匹配 |
| 答案改写 | `bert_score` | 评估语义相似度 |
| 数学计算 | `gsm8k` | 专门处理数学答案 |

### 使用默认指标

```python
# 为所有没有指定 'metric' 的项目使用默认指标
results = evaluate_batch(data, default_metric='em')
```

### 查看可用指标

```python
from llmrouter.evaluation import get_available_metrics

print(get_available_metrics())
# 输出: ['em', 'em_mc', 'cem', 'cemf1', 'f1', 'bert_score', 'gsm8k']
```

### 错误处理

如果评估失败，系统会：
- 设置分数为 `0.0`
- 添加 `evaluation_error` 字段包含错误信息
- 保留原始数据
- 打印警告信息

```python
# 结果示例
{
    'prediction': 'invalid',
    'ground_truth': 'answer',
    'metric': 'unknown_metric',
    'score': 0.0,
    'evaluation_error': "Unknown metric 'unknown_metric'"
}
```

### 批量评估最佳实践

1. **数据预处理**：确保预测和真实答案格式一致
2. **指标选择**：根据任务类型选择合适的评估指标
3. **默认指标**：使用 `default_metric` 参数简化代码
4. **错误处理**：检查 `evaluation_error` 字段以发现异常
5. **结果分析**：统计平均分数和分数分布

```python
import numpy as np

results = evaluate_batch(data)

# 计算平均分数
scores = [r['score'] for r in results if 'evaluation_error' not in r]
avg_score = np.mean(scores)
print(f"平均分数: {avg_score:.2f}")

# 检查错误
errors = [r for r in results if 'evaluation_error' in r]
if errors:
    print(f"发现 {len(errors)} 个评估错误")
```

## API 参考

### 主要函数

| 函数 | 说明 |
|------|------|
| `evaluate_batch(data, default_metric=None)` | 批量评估预测数据 |
| `evaluation_metric(name)` | 注册指标的装饰器 |
| `register_custom_metric(name, func)` | 以编程方式注册指标 |
| `get_available_metrics()` | 列出所有已注册的指标 |

### 注册表

- `EVALUATION_METRICS`：将指标名称映射到函数的字典

## 自定义指标

### 使用装饰器注册（推荐）

```python
from llmrouter.evaluation import evaluation_metric

@evaluation_metric('my_custom_metric')
def my_eval_function(prediction: str, ground_truth: str, threshold: float = 0.5, **kwargs) -> float:
    """
    自定义评估指标

    Args:
        prediction: 预测文本
        ground_truth: 真实答案
        threshold: 阈值参数
        **kwargs: 额外参数

    Returns:
        评估分数
    """
    # 你的评估逻辑
    return 1.0 if len(prediction) > threshold else 0.0
```

### 使用函数注册

```python
from llmrouter.evaluation import register_custom_metric

def my_metric(prediction: str, ground_truth: str, **kwargs) -> float:
    return 1.0 if prediction == ground_truth else 0.0

register_custom_metric('my_metric', my_metric)
```

### 指标函数签名

所有指标函数必须遵循以下签名：

```python
def metric_function(
    prediction: str,      # 必需：预测文本
    ground_truth: str,     # 必需：真实答案文本
    **kwargs               # 可选：额外参数
) -> float:               # 必需：返回浮点数分数
    ...
```

## 更多资源

- 查看 `example.py` 文件获取更多使用示例
- 查看 `batch_evaluator.py` 了解实现细节
- 查看 `llmrouter/utils/evaluation.py` 了解底层评估工具函数
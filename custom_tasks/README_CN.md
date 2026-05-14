# 自定义任务目录 (Custom Tasks)

本目录包含 LLMRouter 的用户自定义任务定义，包括任务名称、提示词模板和评估指标。

## 目录结构

```
custom_tasks/
├── __init__.py                  # 模块初始化文件
├── README_CN.md                 # 本文档（中文说明）
├── example_custom_task.py       # 任务格式化示例
├── complete_example.py          # 完整示例（任务+模板+指标）
└── task_prompts/                # 提示词模板目录
    └── task_*.yaml              # YAML 模板文件
```

## 快速开始

添加你的自定义任务组件，然后导入模块：

```python
import custom_tasks.my_tasks  # 导入时会触发注册

from llmrouter.utils import generate_task_query
from llmrouter.utils.evaluation import calculate_task_performance

# 使用你的自定义任务
prompt = generate_task_query('my_task_name', sample_data)

# 使用自动指标选择进行评估
score = calculate_task_performance(
    prediction="...",
    ground_truth="...",
    task_name="my_task_name"  # 指标会自动推断
)
```

---

## 任务注册机制

### 装饰器系统

LLMRouter 使用装饰器系统来注册任务和指标：

1. **任务注册**: `@register_prompt('task_name', default_metric='metric_name')`
2. **指标注册**: `@evaluation_metric('metric_name')`

### 注册流程

```
模块导入
    ↓
装饰器执行
    ↓
注册到全局注册表
    ↓
可供系统使用
```

### 注册表

- `PROMPT_REGISTRY` - 存储任务名称到格式化函数的映射
- `EVALUATION_METRICS` - 存储指标名称到评估函数的映射
- `TASK_METRIC_REGISTRY` - 存储任务名称到默认指标的映射

### 优先级

自定义任务优先于内置任务：

```
自定义任务 → 内置任务
自定义模板 → 内置模板
自定义指标 → 内置指标
```

---

## 如何创建自定义任务

### 步骤 1: 创建 YAML 提示词模板

在 `task_prompts/` 目录中创建模板文件：

```yaml
# task_prompts/task_my_task.yaml
template: |
  你是 [任务描述] 方面的专家。[指令说明]。
  请按照要求完成任务。
```

**命名规范**:
- 文件名格式: `task_{任务名称}.yaml`
- 必须包含 `template:` 键
- 支持多行文本

### 步骤 2: 创建任务格式化函数

在 `custom_tasks/` 目录中创建 Python 文件：

```python
# custom_tasks/my_task.py
from llmrouter.utils.prompting import register_prompt
from llmrouter.prompts import load_prompt_template

@register_prompt('my_task', default_metric='em')
def format_my_task_prompt(sample_data):
    """
    格式化自定义任务的提示词。

    Args:
        sample_data: 包含任务数据的字典

    Returns:
        dict: {"system": str, "user": str}
    """
    # 从 YAML 模板加载系统提示词
    system_prompt = load_prompt_template("task_my_task")

    # 从 sample_data 中提取数据并格式化用户查询
    user_query = f"请处理以下内容：{sample_data.get('input', '')}"

    return {"system": system_prompt, "user": user_query}
```

**关键点**:
- 使用 `@register_prompt()` 装饰器注册任务
- 函数必须返回 `{"system": str, "user": str}` 格式的字典
- `default_metric` 参数指定默认评估指标
- 使用 `load_prompt_template()` 加载模板

### 步骤 3: 导入并使用

```python
# 在主脚本中导入
import custom_tasks.my_task

# 使用任务
from llmrouter.utils import generate_task_query

prompt = generate_task_query('my_task', {
    'input': '你的数据'
})

# 输出:
# {
#     "system": "你是 [任务描述] 方面的专家。[指令说明]。",
#     "user": "请处理以下内容：你的数据"
# }
```

---

## 提示词模板系统

### 模板加载器

`load_prompt_template()` 函数按以下顺序搜索模板：

1. `custom_tasks/task_prompts/task_{name}.yaml` （优先）
2. `llmrouter/prompts/task_{name}.yaml` （后备）

### YAML 模板格式

```yaml
# 基础格式
template: |
  你是 [角色描述]。
  请执行以下任务：[任务说明]。

# 支持多行
template: |
  你是一位专业的 [角色]。

  你的职责是：
  1. [职责1]
  2. [职责2]
  3. [职责3]

  请按照要求完成任务。
```

### 示例模板

```yaml
# task_prompts/task_code_refine.yaml
template: |
  You are an expert code reviewer. Refine the following code to improve
  readability, performance, and best practices. Follow Python PEP 8 guidelines.
```

```yaml
# task_prompts/task_sentiment_analysis.yaml
template: |
  你是一位情感分析专家。请分析给定文本的情感倾向，
  并准确判断其为正面、负面还是中性情感。
```

### 模板最佳实践

1. **清晰的角色定义**: 明确说明 AI 的身份和能力
2. **具体指令**: 提供清晰的任务要求和输出格式
3. **示例**: 如有必要，提供输入输出示例
4. **约束条件**: 说明任何限制或特殊要求

---

## 自定义评估指标指南

### 指标函数定义

评估指标函数必须遵循以下签名：

```python
from llmrouter.evaluation import evaluation_metric

@evaluation_metric('my_metric')
def my_metric(prediction: str, ground_truth: str, **kwargs) -> float:
    """
    自定义评估指标。

    Args:
        prediction: 模型预测结果
        ground_truth: 真实标签
        **kwargs: 其他可选参数

    Returns:
        float: 评分，范围 0.0 到 1.0
    """
    # 你的评估逻辑
    return 1.0 if prediction == ground_truth else 0.0
```

### 指标使用

#### 方式 1: 直接指定指标

```python
from llmrouter.utils.evaluation import calculate_task_performance

score = calculate_task_performance(
    prediction="positive",
    ground_truth="positive",
    metric="my_metric"
)
```

#### 方式 2: 通过任务名称自动选择

```python
score = calculate_task_performance(
    prediction="positive",
    ground_truth="positive",
    task_name="my_task"  # 使用任务的 default_metric
)
```

### 内置评估指标

LLMRouter 提供以下内置指标：

| 指标名称 | 描述 | 适用场景 |
|---------|------|---------|
| `em` | 精确匹配 | 任何需要完全匹配的任务 |
| `em_mc` | 多选题精确匹配 | 多选题、选择题任务 |
| `cem` | 忽略大小写的精确匹配 | 不区分大小写的文本匹配 |
| `f1` | F1 分数 | 分类任务 |

### 自定义指标示例

#### 示例 1: 模糊匹配指标

```python
@evaluation_metric('fuzzy_match')
def fuzzy_match(prediction: str, ground_truth: str, **kwargs) -> float:
    """
    模糊匹配指标，处理预测结果包含额外文本的情况。
    """
    pred_clean = prediction.strip().lower()
    gt_clean = ground_truth.strip().lower()

    # 如果预测包含真实标签，则认为匹配
    if gt_clean in pred_clean:
        return 1.0

    return 0.0
```

#### 示例 2: 情感分析指标

```python
@evaluation_metric('sentiment_exact_match')
def sentiment_exact_match(prediction: str, ground_truth: str, **kwargs) -> float:
    """
    情感分析评估指标。
    """
    pred_clean = prediction.strip().lower()
    gt_clean = ground_truth.strip().lower()

    valid_sentiments = ['positive', 'negative', 'neutral']

    # 从预测中提取情感
    for sentiment in valid_sentiments:
        if sentiment in pred_clean and sentiment == gt_clean:
            return 1.0

    # 直接比较
    if pred_clean == gt_clean:
        return 1.0

    return 0.0
```

#### 示例 3: 数值范围指标

```python
@evaluation_metric('numeric_range_match')
def numeric_range_match(prediction: str, ground_truth: str, **kwargs) -> float:
    """
    数值范围匹配指标，允许一定的误差范围。
    """
    try:
        pred_val = float(prediction.strip())
        gt_val = float(ground_truth.strip())
        tolerance = kwargs.get('tolerance', 0.1)  # 默认 10% 误差

        diff = abs(pred_val - gt_val)
        if diff <= gt_val * tolerance:
            return 1.0
        elif diff <= gt_val * tolerance * 2:
            return 0.5
        else:
            return 0.0
    except (ValueError, TypeError):
        return 0.0
```

### 指标开发建议

1. **返回值范围**: 始终返回 0.0 到 1.0 之间的浮点数
2. **错误处理**: 对无效输入返回合理的默认值（如 0.0）
3. **数据清理**: 使用 `strip().lower()` 等方法清理输入
4. **灵活性**: 使用 `**kwargs` 接收可选参数
5. **文档**: 清晰说明指标的计算逻辑和适用场景

---

## 完整示例

### 示例 1: 代码审查任务

**任务文件** (`custom_tasks/code_review.py`):

```python
from llmrouter.utils.prompting import register_prompt
from llmrouter.prompts import load_prompt_template

@register_prompt('code_review', default_metric='em')
def format_code_review_prompt(sample_data):
    """格式化代码审查任务提示词"""
    system_prompt = load_prompt_template("task_code_review")

    code = sample_data.get("code", "")
    user_query = f"""请审查以下代码并提出改进建议：

代码：
{code}

审查意见："""

    return {"system": system_prompt, "user": user_query}
```

**模板文件** (`task_prompts/task_code_review.yaml`):

```yaml
template: |
  你是一位资深代码审查员，专注于代码质量、性能和安全性。
  请以建设性的方式提供反馈。
```

### 示例 2: 情感分析任务（含自定义指标）

**任务文件** (`custom_tasks/sentiment_analysis.py`):

```python
from llmrouter.utils.prompting import register_prompt
from llmrouter.evaluation import evaluation_metric
from llmrouter.prompts import load_prompt_template

@register_prompt('sentiment_analysis', default_metric='sentiment_exact_match')
def format_sentiment_analysis_prompt(sample_data):
    """格式化情感分析任务提示词"""
    system_prompt = load_prompt_template("task_sentiment_analysis")

    text = sample_data.get("text", "")
    user_query = f"""分析以下文本的情感倾向：

{text}

情感（positive/negative/neutral）："""

    return {"system": system_prompt, "user": user_query}


@evaluation_metric('sentiment_exact_match')
def sentiment_exact_match(prediction: str, ground_truth: str, **kwargs) -> float:
    """情感分析评估指标"""
    pred_clean = prediction.strip().lower()
    gt_clean = ground_truth.strip().lower()

    valid_sentiments = ['positive', 'negative', 'neutral']

    for sentiment in valid_sentiments:
        if sentiment in pred_clean:
            return 1.0 if sentiment == gt_clean else 0.0

    if pred_clean == gt_clean:
        return 1.0

    return 0.0
```

**模板文件** (`task_prompts/task_sentiment_analysis.yaml`):

```yaml
template: |
  你是一位情感分析专家。请分析给定文本的情感倾向，
  并准确判断其为正面（positive）、负面（negative）还是中性（neutral）。
```

### 示例 3: 多选题任务

**任务文件** (`custom_tasks/math_mc.py`):

```python
from llmrouter.utils.prompting import register_prompt
from llmrouter.prompts import load_prompt_template

@register_prompt('math_mc', default_metric='em_mc')
def format_math_mc_prompt(sample_data):
    """格式化数学多选题提示词"""
    system_prompt = load_prompt_template("task_math_mc")

    question = sample_data.get("question", "")
    options = sample_data.get("options", ["A", "B", "C", "D"])
    options_text = "\n".join([
        f"{opt}. {sample_data.get(f'option_{opt}', '')}" for opt in options
    ])

    user_query = f"""{question}

{options_text}

答案（填写选项字母）："""

    return {"system": system_prompt, "user": user_query}
```

**模板文件** (`task_prompts/task_math_mc.yaml`):

```yaml
template: |
  你是一位数学专家。请仔细阅读题目，从给定的选项中选择正确答案。
```

---

## 注意事项

1. **导入顺序**: 使用前必须导入自定义任务模块
2. **命名规范**: 遵循项目命名约定，避免冲突
3. **模板优先级**: 自定义模板会覆盖同名内置模板
4. **指标复用**: 可以直接使用内置指标，无需重复实现
5. **返回值格式**: 评估指标必须返回 0.0 到 1.0 的浮点数
6. **错误处理**: 在自定义函数中添加适当的错误处理

## 示例文件参考

- `example_custom_task.py` - 基础任务格式化示例
- `complete_example.py` - 完整示例（任务、模板、指标）
- `task_prompts/task_code_refine.yaml` - 提示词模板示例

## 相关链接

- [LLMRouter 主 README](../README_CN.md)
- [内置任务说明](../llmrouter/prompts/README_CN.md)
- [评估系统文档](../llmrouter/evaluation/README_CN.md)
# 自定义任务 (Custom Tasks)

本目录包含 LLMRouter 的用户自定义任务定义，包括任务名称、提示词模板和评估指标。

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

## 添加自定义组件

### 1. 任务名称注册

使用格式化函数注册任务名称：

```python
# custom_tasks/my_tasks.py
from llmrouter.utils.prompting import register_prompt
from llmrouter.prompts import load_prompt_template

@register_prompt('my_task_name', default_metric='my_metric')
def format_my_task_name_prompt(sample_data):
    system_prompt = load_prompt_template("task_my_task_name")
    # 从 sample_data 格式化用户查询
    user_query = f"Question: {sample_data.get('query', '')}"
    return {"system": system_prompt, "user": user_query}
```

**关键点：**
- 使用 `@register_prompt('task_name', default_metric='...')` 装饰器
- 函数必须返回 `{"system": str, "user": str}` 字典
- `default_metric` 将任务与其评估指标关联（可选）

### 2. 提示词模板

在 `task_prompts/` 中创建 YAML 文件：

```yaml
# task_prompts/task_my_task_name.yaml
template: |
  你是 [任务描述] 方面的专家。[指令说明]。
```

**关键点：**
- 文件名：`task_{task_name}.yaml`
- 包含 `template:` 键和系统提示词
- 统一加载器会自动发现

### 3. 评估指标注册

注册自定义评估指标函数：

```python
# custom_tasks/my_tasks.py
from llmrouter.evaluation import evaluation_metric

@evaluation_metric('my_metric')
def my_metric(prediction: str, ground_truth: str, **kwargs) -> float:
    # 你的评估逻辑
    return 1.0 if prediction == ground_truth else 0.0
```

**关键点：**
- 使用 `@evaluation_metric('metric_name')` 装饰器
- 函数签名：`(prediction: str, ground_truth: str, **kwargs) -> float`
- 返回 0.0 到 1.0 之间的分数

## 工作原理

**自动发现机制：**

1. **任务名称**：模块导入时注册到 `PROMPT_REGISTRY`
   - `generate_task_query()` 首先检查注册表
   - 自定义任务优先于内置任务

2. **评估指标**：模块导入时注册到 `EVALUATION_METRICS`
   - `calculate_task_performance()` 首先检查注册表
   - 适用于任何已注册的指标名称

3. **模板**：统一加载器首先搜索 `custom_tasks/task_prompts/`
   - 自定义模板覆盖同名内置模板
   - 自动搜索自定义和内置位置

4. **任务到指标的映射**：通过 `default_metric` 参数注册到 `TASK_METRIC_REGISTRY`
   - `calculate_task_performance()` 如果未指定指标，则自动使用默认指标
   - 如果没有自定义映射，则回退到内置映射

**无需修改代码：**
- 导入后现有代码会自动使用自定义组件
- 所有注册表都会在回退到内置项之前检查
- 导入顺序：自定义 → 内置

## 自定义任务格式化系统说明

自定义任务格式化系统允许你为特定任务定义专门的提示词格式。系统由以下组件组成：

### 格式化函数

每个任务都有一个格式化函数，负责：
- 从 YAML 模板加载系统提示词
- 从输入数据格式化用户查询
- 返回包含 `system` 和 `user` 键的字典

```python
@register_prompt('my_task')
def format_my_task_prompt(sample_data):
    system_prompt = load_prompt_template("task_my_task")
    user_query = f"处理以下内容：{sample_data.get('input', '')}"
    return {"system": system_prompt, "user": user_query}
```

### 统一模板加载器

`load_prompt_template()` 函数按以下顺序搜索模板：
1. `custom_tasks/task_prompts/task_{name}.yaml`
2. `llmrouter/prompts/task_{name}.yaml`

自定义模板优先级更高。

## 如何注册自定义评估指标

### 定义评估指标函数

评估指标函数接收模型预测和真实标签，返回 0.0 到 1.0 的分数：

```python
from llmrouter.evaluation import evaluation_metric

@evaluation_metric('exact_match_ignore_case')
def exact_match_ignore_case(prediction: str, ground_truth: str, **kwargs) -> float:
    """忽略大小写的精确匹配指标"""
    return 1.0 if prediction.strip().lower() == ground_truth.strip().lower() else 0.0
```

### 可用的内置指标

LLMRouter 提供以下内置评估指标：
- `em` (Exact Match) - 精确匹配
- `em_mc` (Exact Match for Multiple Choice) - 多选题精确匹配
- `cem` (Case-Insensitive Exact Match) - 忽略大小写的精确匹配
- `f1` - F1 分数（适用于分类任务）

### 任务与指标的关联

通过 `default_metric` 参数将任务与指标关联：

```python
@register_prompt('my_task', default_metric='my_custom_metric')
def format_my_task_prompt(sample_data):
    ...
```

这样在调用 `calculate_task_performance()` 时，只需提供 `task_name`，系统会自动使用默认指标。

## 自定义任务示例

### 示例 1：代码审查任务

```python
# custom_tasks/code_review.py
from llmrouter.utils.prompting import register_prompt
from llmrouter.prompts import load_prompt_template

@register_prompt('code_review', default_metric='em')
def format_code_review_prompt(sample_data):
    system_prompt = load_prompt_template("task_code_review")

    code = sample_data.get("code", "")
    user_query = f"""请审查以下代码并提出改进建议：

代码：
{code}

审查意见："""

    return {"system": system_prompt, "user": user_query}
```

配套模板 `task_prompts/task_code_review.yaml`：

```yaml
template: |
  你是一位资深代码审查员，专注于代码质量、性能和安全性。
  请以建设性的方式提供反馈。
```

### 示例 2：情感分析任务（含自定义指标）

```python
# custom_tasks/sentiment.py
from llmrouter.utils.prompting import register_prompt
from llmrouter.evaluation import evaluation_metric
from llmrouter.prompts import load_prompt_template

@register_prompt('sentiment', default_metric='sentiment_fuzzy_match')
def format_sentiment_prompt(sample_data):
    system_prompt = load_prompt_template("task_sentiment")

    text = sample_data.get("text", "")
    user_query = f"""分析以下文本的情感倾向：

{text}

情感（正面/负面/中性）："""

    return {"system": system_prompt, "user": user_query}


@evaluation_metric('sentiment_fuzzy_match')
def sentiment_fuzzy_match(prediction: str, ground_truth: str, **kwargs) -> float:
    """模糊匹配情感指标，处理预测结果可能包含额外文本的情况"""
    pred_lower = prediction.strip().lower()
    gt_lower = ground_truth.strip().lower()

    # 检查是否包含情感关键词
    for sentiment in ['正面', 'negative', '中性']:
        if sentiment in pred_lower:
            return 1.0 if sentiment == gt_lower else 0.0

    # 英文情感
    for sentiment in ['positive', 'negative', 'neutral']:
        if sentiment in pred_lower:
            return 1.0 if sentiment == gt_lower else 0.0

    return 0.0
```

### 示例 3：多选题任务

```python
# custom_tasks/multiple_choice.py
from llmrouter.utils.prompting import register_prompt
from llmrouter.prompts import load_prompt_template

@register_prompt('math_mc', default_metric='em_mc')
def format_math_mc_prompt(sample_data):
    system_prompt = load_prompt_template("task_math_mc")

    question = sample_data.get("question", "")
    options = sample_data.get("options", ["A", "B", "C", "D"])
    options_text = "\n".join([f"{opt}. {sample_data.get(f'option_{opt}', '')}" for opt in options])

    user_query = f"""{question}

{options_text}

答案（填写选项字母）："""

    return {"system": system_prompt, "user": user_query}
```

## 示例文件

- `example_custom_task.py` - 任务格式化示例
- `complete_example.py` - 包含任务、模板和指标的完整示例
- `task_prompts/task_code_refine.yaml` - 提示词模板示例

## 注意事项

- 使用前导入模块：`import custom_tasks.my_tasks`
- 自定义组件优先于内置组件
- 模板会自动在自定义和内置位置中搜索
- 如果内置指标满足需求，可以重用它们
- 确保评估指标函数返回 0.0 到 1.0 之间的浮点数
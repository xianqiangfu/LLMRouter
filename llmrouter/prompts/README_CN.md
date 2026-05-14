# Prompts 目录说明

本目录包含所有以 YAML 文件存储的提示词模板，按类别组织到子文件夹中。

## 目录结构

```
llmrouter/prompts/
├── __init__.py                    # 模板加载工具函数
├── task_prompts/                  # 评估基准任务专用提示词
│   ├── task_mc.yaml               # 多选题任务系统提示词
│   ├── task_gsm8k.yaml            # GSM8K 数学应用题系统提示词
│   ├── task_math.yaml             # MATH 数据集问题系统提示词
│   ├── task_mbpp.yaml             # MBPP 代码生成系统提示词
│   └── task_humaneval.yaml        # HumanEval 代码补全系统提示词
├── agentic_role/                  # 代理和多代理推理提示词
│   ├── agent_prompt.yaml          # 多代理推理的专用助手模型指令
│   ├── agent_decomp_cot.yaml      # 思维链聚合提示词
│   ├── agent_decomp.yaml          # 简单查询分解提示词
│   └── agent_decomp_route.yaml    # 分解+路由模板
├── router_prompts/                # 路由器专用提示词模板
│   ├── router_qwen.yaml           # Qwen 模型的 Router_R1 提示词
│   └── router_llama.yaml          # LLaMA 模型的 Router_R1 提示词
├── data_prompts/                  # 数据转换和处理提示词
│   └── data_conversion.yaml       # 数据格式转换提示词
└── README.md                      # 本文件
```

## 使用方法

```python
from llmrouter.prompts import load_prompt_template

# 加载模板（在所有子文件夹中递归搜索）
template = load_prompt_template("task_mc")
prompt = template.format(question="2+2 是多少？")

# 或者显式指定子文件夹路径
template = load_prompt_template("task_prompts/task_mc")
```

## 模板分类

### 任务提示词 (`task_prompts/`)
用于评估基准和任务的系统提示词：
- **task_mc.yaml**: 多选题（用于 mmlu、gpqa、commonsense_qa 等）
- **task_gsm8k.yaml**: GSM8K 数学应用题
- **task_math.yaml**: MATH 数据集问题
- **task_mbpp.yaml**: MBPP 代码生成
- **task_humaneval.yaml**: HumanEval 代码补全

### 代理角色提示词 (`agentic_role/`)
用于多代理推理和查询分解的提示词：
- **agent_prompt.yaml**: 多代理推理中专用助手模型的指令
- **agent_decomp_cot.yaml**: 用于聚合分解响应的思维链提示词
- **agent_decomp.yaml**: 简单查询分解提示词
- **agent_decomp_route.yaml**: 分解+路由模板（运行时填充）

### 路由器提示词 (`router_prompts/`)
路由器专用的提示词模板：
- **router_qwen.yaml**: Qwen 模型系列的 Router_R1 提示词模板
- **router_llama.yaml**: LLaMA 模型系列的 Router_R1 提示词模板

**注意**: Router_R1 将其提示词保存在 `llmrouter/models/Router_R1/prompt_pool.py` 中（硬编码）。这些 YAML 文件供参考或供其他路由器使用。

### 数据提示词 (`data_prompts/`)
用于数据格式转换和预处理的提示词：
- **data_conversion.yaml**: 数据格式转换的提示词模板

## 提示词模板系统

### 模板加载机制

`load_prompt_template()` 函数会在两个位置搜索模板：

1. **自定义任务目录**: `custom_tasks/task_prompts/`（优先级最高）
2. **内置提示词目录**: `llmrouter/prompts/`（后备）

搜索顺序：
- 首先搜索 `custom_tasks/task_prompts/`
- 如果未找到，搜索 `llmrouter/prompts/` 的所有子文件夹

### 任务格式化机制

提示词模板使用 Python 字符串格式化语法：

```yaml
# 示例：带占位符的模板
template: |
  Given the query '{query}', decompose it into sub-queries.
  {model_descriptions}

  Output each sub-query on a separate line.
```

使用时：
```python
template = load_prompt_template("agent_decomp")
formatted = template.format(
    query="如何提高机器学习模型性能？",
    model_descriptions="Model A: Good at math\nModel B: Good at coding"
)
```

### 占位符类型

1. **简单占位符**: `{variable_name}`
   ```python
   template.format(question="2+2 是多少？")
   ```

2. **模型列表占位符**: `{model_list}` 和 `{model_descriptions}`
   - 用于路由器提示词，在运行时动态填充模型信息

3. **双大括号占位符**: `{{variable_name}}`
   - 用于需要延迟替换的场景

## YAML 格式

每个 YAML 文件遵循以下结构：

```yaml
template: |
  Your prompt template string here.
  Can span multiple lines.
  Use {placeholder} for formatting.
```

## 加载模板

`load_prompt_template()` 函数会自动递归搜索所有子文件夹。您可以：

1. **仅使用文件名**（推荐）：
   ```python
   template = load_prompt_template("task_mc")  # 搜索所有子文件夹
   ```

2. **指定子文件夹路径**（显式）：
   ```python
   template = load_prompt_template("task_prompts/task_mc")  # 搜索特定子文件夹
   ```

这确保所有提示词字符串集中管理，便于编辑而无需修改 Python 代码。

## 如何添加自定义任务

### 步骤 1: 创建提示词模板

在 `custom_tasks/task_prompts/` 目录下创建 YAML 文件：

```bash
# 创建目录（如果不存在）
mkdir -p custom_tasks/task_prompts

# 创建模板文件
touch custom_tasks/task_prompts/task_my_task.yaml
```

模板文件内容：
```yaml
# custom_tasks/task_prompts/task_my_task.yaml
template: |
  You are an expert at [任务描述]. [指令].

  Given the input: {input}
  Provide your response in the specified format.
```

### 步骤 2: 创建任务格式化函数

在 `custom_tasks/` 目录下创建 Python 文件：

```python
# custom_tasks/my_tasks.py
from llmrouter.utils.prompting import register_prompt
from llmrouter.prompts import load_prompt_template

@register_prompt('my_task_name', default_metric='accuracy')
def format_my_task_name_prompt(sample_data):
    """格式化我的自定义任务提示词"""
    system_prompt = load_prompt_template("task_my_task")
    # 从 sample_data 格式化用户查询
    user_query = f"问题: {sample_data.get('question', '')}"
    return {"system": system_prompt, "user": user_query}
```

**关键点**：
- 使用 `@register_prompt('task_name', default_metric='...')` 装饰器
- 函数必须返回 `{"system": str, "user": str}` 字典
- `default_metric` 将任务与其评估指标关联（可选）

### 步骤 3: （可选）注册评估指标

如果需要自定义评估指标：

```python
# custom_tasks/my_tasks.py
from llmrouter.evaluation import evaluation_metric

@evaluation_metric('accuracy')
def accuracy_metric(prediction: str, ground_truth: str, **kwargs) -> float:
    """计算准确率"""
    return 1.0 if prediction == ground_truth else 0.0
```

**关键点**：
- 使用 `@evaluation_metric('metric_name')` 装饰器
- 函数签名：`(prediction: str, ground_truth: str, **kwargs) -> float`
- 返回 0.0 到 1.0 之间的分数

### 步骤 4: 使用自定义任务

```python
# 导入触发注册
import custom_tasks.my_tasks

from llmrouter.utils import generate_task_query
from llmrouter.utils.evaluation import calculate_task_performance

# 使用您的自定义任务
prompt = generate_task_query('my_task_name', {'question': '2+2 是多少？'})

# 使用自动指标选择进行评估
score = calculate_task_performance(
    prediction="4",
    ground_truth="4",
    task_name="my_task_name"  # 指标自动推断
)
```

## 自动发现机制

### 优先级顺序

1. **任务名称**: 导入模块时注册到 `PROMPT_REGISTRY`
   - `generate_task_query()` 首先检查注册表
   - 自定义任务优先于内置任务

2. **指标**: 导入模块时注册到 `EVALUATION_METRICS`
   - `calculate_task_performance()` 首先检查注册表
   - 适用于任何已注册的指标名称

3. **模板**: 统一加载器优先搜索 `custom_tasks/task_prompts/`
   - 自定义模板覆盖同名的内置模板
   - 自动搜索自定义和内置位置

4. **任务-指标映射**: 通过 `default_metric` 参数注册到 `TASK_METRIC_REGISTRY`
   - 如果未指定，`calculate_task_performance()` 自动使用默认指标
   - 如果没有自定义映射，回退到内置映射

### 无需修改代码

- 导入后现有代码自动使用自定义组件
- 所有注册表在回退到内置选项之前进行检查
- 导入顺序：自定义 → 内置

## 示例文件

参考 `custom_tasks/` 目录下的示例：
- `example_custom_task.py` - 示例任务格式化函数
- `complete_example.py` - 包含任务、模板和指标的完整示例
- `task_prompts/task_code_refine.yaml` - 示例提示词模板

## 注意事项

- 使用前导入模块：`import custom_tasks.my_tasks`
- 自定义组件优先于内置组件
- 模板自动在自定义和内置位置搜索
- 如果满足需求，可以使用内置指标（`cem`、`em_mc`、`f1` 等）
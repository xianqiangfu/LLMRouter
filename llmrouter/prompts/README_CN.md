# 提示词模板

本目录包含 LLMRouter 中用于评估 LLM 响应质量的提示词模板。

## 概述

提示词模板定义了用于评估不同类型任务（如代码生成、数学推理等）的提示词，这些提示词用于：
- 评估 LLM 在给定查询上的响应质量
- 为路由器生成训练数据
- 比较不同 LLM 的性能

## 目录结构

```
prompts/
├── __init__.py          # 模块初始化和提示词注册
├── base_prompt.py       # 基础提示词类
└── templates/           # 提示词模板文件
    ├── codegen_prompt.txt    # 代码生成任务提示词
    ├── math_prompt.txt       # 数学推理任务提示词
    ├── general_prompt.txt    # 通用任务提示词
    └── ...                    # 其他任务类型提示词
```

## 提示词模板系统

### 提示词类型

LLMRouter 支持以下类型的提示词模板：

| 提示词类型 | 用途 | 模板文件 |
|-----------|------|---------|
| `codegen` | 代码生成任务评估 | `codegen_prompt.txt` |
| `math` | 数学推理任务评估 | `math_prompt.txt` |
| `general` | 通用问答任务评估 | `general_prompt.txt` |
| `creative` | 创意写作任务评估 | `creative_prompt.txt` |
| `reasoning` | 逻辑推理任务评估 | `reasoning_prompt.txt` |

### 模板变量

提示词模板支持以下变量：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `{query}` | 用户查询 | "编写一个快速排序算法" |
| `{response}` | LLM 响应 | "def quicksort(arr):..." |
| `{llm_name}` | LLM 名称 | "gpt-4", "claude-3" |
| `{task}` | 任务类型 | "code_generation" |

## 使用方法

### 基础用法

```python
from llmrouter.prompts import get_prompt_template

# 获取提示词模板
prompt = get_prompt_template(task="codegen")

# 填充变量
formatted_prompt = prompt.format(
    query="编写一个 Python 函数计算斐波那契数列",
    response="def fibonacci(n):...",
    llm_name="gpt-4"
)

# 使用提示词评估
evaluator = LLMEvaluator()
score = evaluator.evaluate(formatted_prompt)
```

## 自定义提示词模板

### 创建新模板

1. 在 `templates/` 目录下创建新的模板文件（如 `custom_prompt.txt`）

2. 定义模板变量：

```
你是一个专业的评估助手。请评估以下{task}任务的响应质量。

查询：{query}
响应：{response}
使用的模型：{llm_name}

请从以下方面进行评估：
1. 准确性
2. 完整性
3. 可用性

评分范围：0-10分
```

3. 在 `__init__.py` 中注册新模板

## 提示词设计指南

### 好的提示词特点

1. **明确性**：清楚说明评估任务和标准
2. **结构化**：使用清晰的分段和编号
3. **一致性**：所有评估使用相同的格式和标准
4. **可量化**：评估标准可量化（如 0-10 分）
5. **无偏性**：不偏向任何特定的 LLM 或响应风格

## 相关文档

- [评估系统](../evaluation/README_CN.md)
- [数据生成](../../data/README_CN.md)

---

**文档版本**: 1.0
**最后更新**: 2026-05-15
**维护者**: LLMRouter Team

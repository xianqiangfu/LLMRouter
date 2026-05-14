# 代码规范说明文档

本文档定义了 LLMRouter 项目的代码规范，所有贡献者应遵循这些规范以确保代码的一致性和可维护性。

## 目录

- [命名规范](#命名规范)
- [注释规范](#注释规范)
- [代码格式规范](#代码格式规范)
- [提交规范](#提交规范)
- [代码审查清单](#代码审查清单)

---

## 命名规范

### 变量命名

使用小写字母和下划线的组合，名称应具有描述性。

```python
# 正确示例
model_name = "gpt-4"
query_embedding = [0.12, 0.33, 0.78]
user_id = "user_12345"
training_data = []
api_endpoint = "https://api.openai.com/v1"

# 错误示例
ModelName = "gpt-4"  # 避免大写开头
mn = "model"         # 避免缩写
data = []            # 名称太模糊
```

### 函数命名

使用小写字母和下划线的组合，动词开头，描述函数的功能。

```python
# 正确示例
def route_single(query):
    """路由单个查询"""
    pass

def load_model(path):
    """加载模型"""
    pass

def calculate_performance():
    """计算性能指标"""
    pass

# 错误示例
def RouteSingle():    # 避免大写开头
def route_query(q):   # 避免无意义的缩写
```

### 类命名

使用大驼峰命名法（PascalCase），每个单词的首字母大写。

```python
# 正确示例
class MetaRouter:
    """路由器基类"""
    pass

class KNNRouter:
    """KNN 路由器"""
    pass

class DataLoader:
    """数据加载器"""
    pass

# 错误示例
class meta_router:     # 避免小写开头
class KNNrouter:       # 保持一致的驼峰命名
```

### 常量命名

使用全大写字母和下划线的组合。

```python
# 正确示例
MAX_TOKENS = 2048
DEFAULT_TEMPERATURE = 0.7
ROUTER_TRAINER_REGISTRY = {}
API_KEYS_ENV_VAR = "API_KEYS"

# 错误示例
max_tokens = 2048         # 避免小写
MaxTokens = 2048          # 避免大驼峰
```

### 私有成员命名

使用前导下划线表示私有成员。

```python
class MyClass:
    def __init__(self):
        self._private_var = 42  # 私有变量
        self.public_var = 100   # 公共变量

    def _private_method(self):  # 私有方法
        pass

    def public_method(self):    # 公共方法
        pass
```

### 文件命名

使用小写字母和下划线的组合，模块名反映其功能。

```python
# 正确示例
router_train.py
meta_router.py
data_loader.py
router_helpers.py

# 错误示例
RouterTrain.py       # 避免大写开头
metaRouter.py        # 避免混合大小写
router.py            # 名称过于简单，应更具描述性
```

### 目录命名

使用小写字母和下划线的组合，目录名反映其功能。

```python
# 正确示例
llmrouter/models/
llmrouter/data/
llmrouter/utils/
custom_routers/

# 错误示例
LLMRouter/Models/    # 避免大写开头
customRouters/       # 避免混合大小写
```

---

## 注释规范

### 中文注释要求

所有注释和文档字符串应使用中文编写，确保团队成员能够理解。

```python
# 正确示例
# 获取训练数据的最佳模型
routing_best = self.routing_data_train.loc[
    self.routing_data_train.groupby("query")["performance"].idxmax()
].reset_index(drop=True)

# 初始化 KNN 分类器
self.knn_model = KNeighborsClassifier(**knn_params)

# 错误示例
# Get the best model for training data
routing_best = ...

# Initialize KNN classifier
self.knn_model = ...
```

### 模块级文档字符串

每个模块文件应包含详细的模块级文档字符串，描述模块的功能和主要特性。

```python
"""
meta_router 模块
================

本模块定义了 MetaRouter 基类，为所有 LLM 路由器提供统一的抽象接口。
MetaRouter 是所有路由器的基类，负责管理底层 PyTorch 模型，并提供标准的路由接口。

主要功能：
    - 管理底层 PyTorch 模型（nn.Module）
    - 可选地加载配置文件和数据
    - 提供标准的路由接口：route() / forward()
    - 提供基础工具方法：指标计算、模型保存和加载

训练逻辑与路由器解耦，由 Trainer 类负责处理。

使用方式：
    所有路由器实现都应继承自 MetaRouter 并实现其抽象方法：
    - route_batch(): 批量路由决策
    - route_single(): 单个样本路由决策
"""
```

### 类文档字符串

类文档字符串应详细描述类的用途、职责和主要属性。

```python
class MetaRouter(nn.Module, ABC):
    """
    MetaRouter 路由器基类
    --------------------

    所有 LLM 路由器的统一抽象基类。本类继承自 PyTorch 的 nn.Module 和抽象基类 ABC，
    为不同类型的路由器提供统一的接口规范。

    主要职责：
        - 管理底层 PyTorch 模型（nn.Module）
        - 可选地加载配置文件和数据集
        - 提供标准的路由接口：route() 和 forward()
        - 提供基础工具方法：指标计算、模型保存/加载

    训练逻辑与路由器解耦，由专门的 Trainer 类负责处理，保持本类的职责清晰。

    Attributes:
        model (nn.Module): 执行路由计算的底层 PyTorch 模型
        resources (Any): 可选的共享资源或上下文（如 tokenizer、环境等）
        cfg (dict): 从 YAML 配置文件加载的配置信息
        metric_weights (list): 指标权重列表，用于综合评估路由效果
    """
```

### 函数文档字符串

函数文档字符串应详细描述函数的功能、参数、返回值和可能的异常。

```python
def __init__(self, model: nn.Module, yaml_path: str | None = None, resources=None):
    """
    初始化 MetaRouter 路由器实例。

    Args:
        model (nn.Module):
            执行路由计算的底层 PyTorch 模型。所有路由器实现都必须提供此模型。
        yaml_path (str | None):
            可选的 YAML 配置文件路径。如果提供，将在初始化时加载配置和训练数据。
            配置文件格式应符合项目的 YAML 规范。
        resources (Any, optional):
            可选的共享资源或上下文对象，例如 tokenizer、环境变量等。
            可用于在不同组件间共享资源，避免重复加载。

    Raises:
        FileNotFoundError: 当 yaml_path 指定的文件不存在时抛出。

    Note:
        如果提供了 yaml_path，初始化过程会自动：
        - 解析 YAML 配置文件
        - 通过 DataLoader 加载数据集并附加到 self
        - 从配置中提取指标权重
    """
```

### 行内注释

行内注释用于解释复杂的逻辑或算法步骤。

```python
# 正确示例
# 选择性能最佳的模型用于每个查询
routing_best = self.routing_data_train.loc[
    self.routing_data_train.groupby("query")["performance"].idxmax()
].reset_index(drop=True)

# 准备 KNN 训练所需的嵌入和标签数组
query_embedding_id = routing_best["embedding_id"].tolist()
self.query_embedding_list = [self.query_embedding_data[i].numpy() for i in query_embedding_id]

# 错误示例
routing_best = self.routing_data_train.loc[
    self.routing_data_train.groupby("query")["performance"].idxmax()
].reset_index(drop=True)  # 选择最好的模型

# 代码应该自解释，避免在简单的代码上添加注释
x = x + 1  # 增加 x 的值
```

### TODO 和 FIXME 注释

使用 TODO 和 FIXME 标记需要改进或修复的代码。

```python
# TODO: 添加对多模态输入的支持
def route_single(self, query_input: dict) -> dict:
    pass

# FIXME: 这里的性能可能存在问题，需要优化
def compute_metrics(self, outputs, batch) -> dict:
    pass
```

---

## 代码格式规范

### PEP 8 规范

项目严格遵循 PEP 8 规范，推荐使用以下工具进行检查和格式化：

```bash
# 使用 black 格式化代码
black llmrouter/

# 使用 flake8 检查代码规范
flake8 llmrouter/

# 使用 isort 排序导入
isort llmrouter/
```

### 缩进

使用 4 个空格缩进，不使用制表符（Tab）。

```python
# 正确示例
def route_single(self, query):
    if query:
        embedding = self.get_embedding(query)
        model = self.predict(embedding)
        return {"model_name": model}

# 错误示例
def route_single(self, query):
	if query:      # 使用 Tab 缩进
		embedding = self.get_embedding(query)
```

### 行长度

建议每行不超过 88 个字符（black 默认设置），必要时换行。

```python
# 正确示例
long_variable_name = some_function_with_long_name(
    parameter1=value1,
    parameter2=value2,
    parameter3=value3,
)

# 错误示例
long_variable_name = some_function_with_long_name(parameter1=value1, parameter2=value2, parameter3=value3)  # 行过长
```

### 导入语句

导入语句应按照以下顺序组织，并用空行分隔：

1. 标准库导入
2. 第三方库导入
3. 本地模块导入

```python
# 正确示例
# 标准库
import os
import sys
from typing import Any, Dict, List, Optional

# 第三方库
import numpy as np
import torch
import torch.nn as nn
from sklearn.neighbors import KNeighborsClassifier
import yaml

# 本地模块
from llmrouter.models.meta_router import MetaRouter
from llmrouter.utils import load_model, get_longformer_embedding

# 错误示例
import yaml
import torch
from sklearn.neighbors import KNeighborsClassifier
import os
from llmrouter.models.meta_router import MetaRouter
import numpy as np
```

### 空行规则

- 顶层函数和类定义之间使用两个空行分隔
- 类内部的方法定义之间使用一个空行分隔
- 逻辑相关的代码块之间使用空行提高可读性

```python
# 正确示例
class MyClass:
    """示例类"""

    def method_one(self):
        """第一个方法"""
        pass

    def method_two(self):
        """第二个方法"""
        pass


def function_one():
    """第一个函数"""
    pass


def function_two():
    """第二个函数"""
    pass
```

### 类型注解

推荐使用类型注解提高代码可读性和类型安全性。

```python
# 正确示例
def route_single(self, query_input: dict) -> dict:
    """路由单个查询"""
    pass

def load_router(self, path: str) -> None:
    """加载路由器"""
    pass

from typing import Any, Dict, List, Optional, Tuple

def compute_metrics(self, outputs: Any, batch: Dict[str, Any]) -> Dict[str, float]:
    """计算指标"""
    pass
```

### 括号和引号

- 优先使用双引号而不是单引号
- 括号内部避免不必要的空格

```python
# 正确示例
message = "Hello, World!"
data = {"key": "value", "name": "LLMRouter"}
function_call(arg1, arg2)

# 错误示例
message = 'Hello, World!'  # 使用单引号
data = { 'key' : 'value' }  # 括号内多余空格
function_call( arg1, arg2 )  # 括号内多余空格
```

---

## 提交规范

### Commit Message 格式

使用简洁、描述性的提交信息，采用中文编写。

```bash
# 正确示例
git commit -m "为 data 目录添加中文 README 文档"

git commit -m "修复 KNNRouter 路由逻辑错误"

git commit -m "添加 ComfyUI 集成支持"

git commit -m "优化数据加载性能，减少内存占用"
```

### 提交信息结构

提交信息应包含以下要素：

1. **简洁的标题**：描述变更的核心内容
2. **详细的描述**（可选）：解释变更的原因和影响
3. **相关 Issue**（可选）：关联相关的 GitHub Issue

```bash
# 示例
git commit -m "修复 LLMRouter 初始化时的配置加载错误

- 修复了 YAML 配置文件不存在时的错误处理
- 改进了配置加载的错误提示信息
- 添加了配置验证逻辑

Fixes #123"
```

### 常用提交前缀

- `添加`：添加新功能或新文件
- `修复`：修复错误或缺陷
- `更新`：更新现有功能
- `优化`：优化性能或代码质量
- `重构`：重构代码结构
- `删除`：删除不需要的代码或文件
- `文档`：更新或添加文档

---

## 代码审查清单

### 代码质量

- [ ] 代码符合 PEP 8 规范
- [ ] 所有注释和文档字符串使用中文
- [ ] 变量和函数命名具有描述性
- [ ] 代码逻辑清晰，易于理解
- [ ] 没有重复代码
- [ ] 没有未使用的代码或导入

### 文档完整性

- [ ] 模块级文档字符串完整
- [ ] 类文档字符串包含用途、职责和属性说明
- [ ] 函数文档字符串包含参数、返回值和异常说明
- [ ] 复杂逻辑有必要的行内注释

### 功能正确性

- [ ] 代码功能符合需求
- [ ] 边界情况得到处理
- [ ] 错误和异常得到妥善处理
- [ ] 有必要的类型检查

### 测试覆盖

- [ ] 新功能有相应的测试
- [ ] 测试覆盖主要功能路径
- [ ] 测试用例包含边界情况
- [ ] 所有测试通过

### 性能考虑

- [ ] 避免不必要的计算或内存使用
- [ ] 大数据处理使用批量操作
- [ ] 资源（如文件、数据库连接）正确关闭
- [ ] 避免循环中的重复计算

### 安全性

- [ ] 敏感信息（API 密钥、密码）不硬编码
- [ ] 输入验证充分
- [ ] 没有安全漏洞（如 SQL 注入、XSS）
- [ ] 错误信息不泄露敏感信息

### 兼容性

- [ ] 代码兼容目标 Python 版本（3.10+）
- [ ] 依赖版本符合项目要求
- [ ] 向后兼容性考虑（如适用）

### 示例代码

```python
# 符合规范的代码示例
from typing import Any, Dict, List, Optional
import os
import yaml
from abc import ABC, abstractmethod

import torch
import torch.nn as nn

from llmrouter.data import DataLoader


class ExampleRouter(nn.Module, ABC):
    """
    示例路由器类
    ------------

    这是一个示例路由器实现，展示了项目的代码规范。

    主要功能：
        - 管理模型配置
        - 提供路由接口
        - 计算评估指标

    Attributes:
        model (nn.Module): 底层路由模型
        config (dict): 配置字典
    """

    def __init__(self, model: nn.Module, config_path: str | None = None):
        """
        初始化路由器。

        Args:
            model: 底层路由模型
            config_path: 可选的配置文件路径

        Raises:
            FileNotFoundError: 配置文件不存在时抛出
        """
        super().__init__()
        self.model = model
        self.config = {}

        if config_path is not None:
            self._load_config(config_path)

    def _load_config(self, path: str) -> None:
        """
        加载配置文件。

        Args:
            path: 配置文件路径

        Raises:
            FileNotFoundError: 文件不存在时抛出
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"配置文件不存在: {path}")

        with open(path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    @abstractmethod
    def route_single(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        路由单个查询。

        Args:
            query: 查询字典

        Returns:
            路由结果字典
        """
        raise NotImplementedError

    def compute_metrics(self, outputs: List[Dict]) -> Dict[str, float]:
        """
        计算评估指标。

        Args:
            outputs: 输出列表

        Returns:
            指标字典
        """
        # 计算准确率
        total = len(outputs)
        correct = sum(1 for o in outputs if o.get("correct", False))
        accuracy = correct / total if total > 0 else 0.0

        return {
            "accuracy": accuracy,
            "total": total,
            "correct": correct,
        }

    def save_model(self, path: str) -> None:
        """
        保存模型。

        Args:
            path: 保存路径
        """
        torch.save(self.state_dict(), path)
        print(f"模型已保存到: {path}")
```

---

## 工具推荐

### 代码格式化

```bash
# Black - 代码格式化工具
pip install black
black llmrouter/

# isort - 导入排序工具
pip install isort
isort llmrouter/
```

### 代码检查

```bash
# flake8 - 代码风格检查
pip install flake8
flake8 llmrouter/

# mypy - 类型检查
pip install mypy
mypy llmrouter/

# pylint - 代码质量检查
pip install pylint
pylint llmrouter/
```

### 预提交钩子

推荐使用 pre-commit 进行代码自动检查：

```bash
# 安装 pre-commit
pip install pre-commit

# 配置 .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 24.4.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
EOF

# 安装钩子
pre-commit install
```

---

## 总结

遵循以上代码规范可以：

1. 提高代码可读性和可维护性
2. 减少代码审查的时间成本
3. 降低引入 bug 的风险
4. 方便新成员快速上手

如有疑问或建议，请通过 GitHub Issue 提出。
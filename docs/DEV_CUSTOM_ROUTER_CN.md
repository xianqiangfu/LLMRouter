# 自定义路由器开发教程

本教程将指导您从零开始开发一个自定义 LLM 路由器，包括路由器实现、训练器开发、插件注册和测试。

---

## 目录

1. [路由器接口说明](#路由器接口说明)
2. [从零开始开发步骤](#从零开始开发步骤)
3. [完整示例代码](#完整示例代码)
4. [训练器开发（可选）](#训练器开发可选)
5. [插件注册](#插件注册)
6. [测试](#测试)
7. [常见问题](#常见问题)

---

## 路由器接口说明

### MetaRouter 基类

所有路由器都必须继承自 `MetaRouter` 基类。该基类定义了路由器的标准接口：

```python
from llmrouter.models.meta_router import MetaRouter
import torch.nn as nn

class MyRouter(MetaRouter):
    def __init__(self, model: nn.Module, yaml_path: str = None, resources=None):
        super().__init__(model, yaml_path, resources)
```

### 必须实现的抽象方法

#### 1. `route_batch(batch)` - 批量路由

```python
def route_batch(self, batch) -> Any:
    """
    对一批查询进行路由决策

    Args:
        batch: 输入批次，可以是列表、字典或张量

    Returns:
        路由输出，可以是以下形式之一：
        - logits: 路由器对各模型的预测分数
        - scores: 每个候选模型的匹配度评分
        - indices: 选中的模型索引或模型名称
    """
    raise NotImplementedError
```

#### 2. `route_single(batch)` - 单个查询路由

```python
def route_single(self, batch) -> Any:
    """
    对单个查询进行路由决策

    Args:
        batch: 单个查询输入

    Returns:
        路由输出
    """
    raise NotImplementedError
```

### 可选重写的方法

#### `forward(batch)` - PyTorch 前向传播

```python
def forward(self, batch) -> Any:
    """
    PyTorch 兼容的前向传播方法
    默认实现委托给 route_batch()
    """
    return self.route_batch(batch)
```

#### `compute_metrics(outputs, batch)` - 指标计算

```python
def compute_metrics(self, outputs, batch) -> dict:
    """
    计算路由性能指标

    Returns:
        指标字典，例如 {"accuracy": 0.85, "cost": 0.42}
    """
    return {}
```

### 基础工具方法

#### `save_router(path)` - 保存模型

```python
router.save_router("models/my_router.pt")
```

#### `load_router(path)` - 加载模型

```python
router.load_router("models/my_router.pt")
```

---

## 从零开始开发步骤

### 步骤 1：创建项目目录结构

```
custom_routers/
├── __init__.py
└── myrouter/
    ├── __init__.py
    ├── router.py      # 路由器实现
    ├── trainer.py     # 训练器实现（可选）
    └── config.yaml    # 配置文件
```

### 步骤 2：实现路由器类

在 `custom_routers/myrouter/router.py` 中实现路由器：

```python
from typing import Any, Dict, List
import torch.nn as nn
from llmrouter.models.meta_router import MetaRouter

class MyRouter(MetaRouter):
    """我的自定义路由器"""

    def __init__(self, yaml_path: str):
        # 创建底层模型（如果不需要训练，可以用 nn.Identity()）
        model = nn.Identity()
        super().__init__(model, yaml_path)

        # 从配置中加载参数
        self.hparam = self.cfg.get("hparam", {})

        # 获取可用的 LLM 列表
        if hasattr(self, 'llm_data') and self.llm_data:
            self.llm_names = list(self.llm_data.keys())
        else:
            raise ValueError("llm_data not found in config")

        # 初始化路由器参数
        self._initialize_params()

    def _initialize_params(self):
        """初始化路由器参数"""
        # 在这里实现你的初始化逻辑
        pass

    def route_single(self, query_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        路由单个查询

        Returns:
            包含以下字段的字典：
            - query: 原始查询
            - model_name: 选中的模型名称
        """
        # 实现路由逻辑
        selected_model = self._select_model(query_input)

        return {
            "query": query_input.get("query", ""),
            "model_name": selected_model,
        }

    def route_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """路由一批查询"""
        results = []
        for query in batch:
            result = self.route_single(query)
            results.append(result)
        return results

    def _select_model(self, query: Dict[str, Any]) -> str:
        """
        根据查询选择最合适的模型

        在这里实现你的路由策略
        """
        # 示例：随机选择（替换为你的逻辑）
        import random
        return random.choice(self.llm_names)
```

### 步骤 3：创建配置文件

在 `custom_routers/myrouter/config.yaml` 中创建配置：

```yaml
# LLM 候选模型数据路径
data_path:
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

  # 可选：测试数据路径
  query_data_test: 'data/example_data/query_data/default_query_test.jsonl'
  routing_data_test: 'data/example_data/routing_data/default_routing_test_data.jsonl'

# 指标权重（用于评估）
metric:
  weights:
    performance: 1
    cost: 0
    llm_judge: 0

# 路由器超参数
hparam:
  # 在这里添加你的超参数
  param1: value1
  param2: value2

# API 端点（用于调用被路由的模型）
api_endpoint: 'https://integrate.api.nvidia.com/v1'

# 模型保存路径
model_path:
  save_model_path: 'models/myrouter/checkpoint.pt'
  load_model_path: 'models/myrouter/checkpoint.pt'
```

### 步骤 4：创建 `__init__.py` 文件

在 `custom_routers/myrouter/__init__.py` 中：

```python
from .router import MyRouter

__all__ = ["MyRouter"]
```

在 `custom_routers/__init__.py` 中：

```python
# 该文件可以为空
```

---

## 完整示例代码

### 示例 1：简单随机路由器

```python
"""
Simple Random Router - 完整示例
=================================
"""

import random
from typing import Any, Dict, List
import torch.nn as nn
from llmrouter.models.meta_router import MetaRouter


class RandomRouter(MetaRouter):
    """
    随机路由器 - 演示基础接口
    """

    def __init__(self, yaml_path: str):
        # 创建虚拟模型（不需要实际计算）
        dummy_model = nn.Identity()
        super().__init__(model=dummy_model, yaml_path=yaml_path)

        # 获取超参数
        hparam = self.cfg.get("hparam", {})
        self.seed = hparam.get("seed", None)

        if self.seed is not None:
            random.seed(self.seed)

        # 获取可用 LLM 列表
        if hasattr(self, 'llm_data') and self.llm_data:
            self.llm_names = list(self.llm_data.keys())
        else:
            raise ValueError("llm_data not found in config")

        print(f"✅ RandomRouter initialized with {len(self.llm_names)} LLMs")

    def route_single(self, query_input: Dict[str, Any]) -> Dict[str, Any]:
        """随机路由单个查询"""
        selected_model = random.choice(self.llm_names)

        return {
            "query": query_input.get("query", ""),
            "model_name": selected_model,
            "predicted_llm": selected_model,
            "confidence": 1.0,
            "method": "random",
        }

    def route_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """随机路由一批查询"""
        results = []
        for query in batch:
            result = self.route_single(query)
            results.append(result)
        return results
```

### 示例 2：基于关键词的路由器

```python
"""
Keyword Router - 基于关键词的路由器
=====================================
"""

import re
from typing import Any, Dict, List
import torch.nn as nn
from llmrouter.models.meta_router import MetaRouter


class KeywordRouter(MetaRouter):
    """
    基于关键词的路由器
    """

    def __init__(self, yaml_path: str):
        dummy_model = nn.Identity()
        super().__init__(model=dummy_model, yaml_path=yaml_path)

        # 从配置中获取关键词映射
        self.keyword_map = self.cfg.get("hparam", {}).get("keyword_map", {})
        self.default_model = self.cfg.get("hparam", {}).get("default_model", None)

        if not self.keyword_map:
            raise ValueError("keyword_map not found in hparam")

        print(f"✅ KeywordRouter initialized with {len(self.keyword_map)} keyword rules")

    def route_single(self, query_input: Dict[str, Any]) -> Dict[str, Any]:
        """根据关键词路由"""
        query = query_input.get("query", "").lower()

        # 查找匹配的关键词
        selected_model = self.default_model
        matched_keyword = None

        for keyword, model_name in self.keyword_map.items():
            if keyword.lower() in query:
                selected_model = model_name
                matched_keyword = keyword
                break

        return {
            "query": query_input.get("query", ""),
            "model_name": selected_model,
            "matched_keyword": matched_keyword,
            "method": "keyword",
        }

    def route_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量路由"""
        return [self.route_single(q) for q in batch]
```

对应的配置文件 `config.yaml`：

```yaml
data_path:
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

hparam:
  keyword_map:
    "数学": "model1"
    "编程": "model2"
    "翻译": "model3"
  default_model: "model1"
```

### 示例 3：基于简单特征的机器学习路由器

```python
"""
Simple Feature Router - 基于特征的路由器
=========================================
"""

import torch
import torch.nn as nn
from typing import Any, Dict, List
from llmrouter.models.meta_router import MetaRouter


class SimpleFeatureNN(nn.Module):
    """简单的特征提取和分类网络"""

    def __init__(self, input_dim: int, num_classes: int):
        super().__init__()
        self.classifier = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(x)


class SimpleFeatureRouter(MetaRouter):
    """
    基于特征的机器学习路由器
    """

    def __init__(self, yaml_path: str):
        # 创建特征提取和分类模型
        input_dim = self.cfg.get("hparam", {}).get("input_dim", 10)
        num_classes = self.cfg.get("hparam", {}).get("num_classes", 2)

        model = SimpleFeatureNN(input_dim, num_classes)
        super().__init__(model=model, yaml_path=yaml_path)

        # 获取模型名称映射
        self.llm_names = list(self.llm_data.keys())
        self.num_classes = len(self.llm_names)
        self.idx_to_model = {i: name for i, name in enumerate(self.llm_names)}

        # 如果有训练数据，准备训练
        if hasattr(self, 'routing_data_train'):
            self._prepare_training_data()

    def _extract_features(self, query: str) -> torch.Tensor:
        """从查询中提取简单特征"""
        features = torch.zeros(10)  # 示例：10维特征

        # 简单特征：长度、标点符号数量、数字数量等
        features[0] = len(query) / 100.0  # 查询长度
        features[1] = query.count('?') / 10.0  # 问号数量
        features[2] = query.count('!') / 10.0  # 感叹号数量
        features[3] = sum(c.isdigit() for c in query) / 10.0  # 数字数量
        features[4] = sum(c.isalpha() for c in query) / 100.0  # 字母数量
        features[5] = query.count(',') / 10.0  # 逗号数量
        features[6] = query.count('.') / 10.0  # 句号数量
        features[7] = query.count('\n') / 10.0  # 换行符数量
        features[8] = 1.0 if '?' in query else 0.0  # 是否包含问号
        features[9] = 1.0 if '!' in query else 0.0  # 是否包含感叹号

        return features.unsqueeze(0)

    def _prepare_training_data(self):
        """准备训练数据"""
        # 提取每个查询的特征和标签
        features = []
        labels = []

        for _, row in self.routing_data_train.iterrows():
            query = row.get("query", "")
            model_name = row.get("model_name", "")

            if model_name in self.idx_to_model:
                feature = self._extract_features(query)
                label = [k for k, v in self.idx_to_model.items() if v == model_name][0]

                features.append(feature)
                labels.append(label)

        if features:
            self.train_features = torch.cat(features)
            self.train_labels = torch.tensor(labels)
        else:
            self.train_features = None
            self.train_labels = None

    def route_single(self, query_input: Dict[str, Any]) -> Dict[str, Any]:
        """路由单个查询"""
        query = query_input.get("query", "")
        features = self._extract_features(query)

        # 前向传播获取预测
        self.eval()
        with torch.no_grad():
            logits = self.model(features)
            pred_idx = torch.argmax(logits, dim=-1).item()
            confidence = torch.softmax(logits, dim=-1)[0, pred_idx].item()

        return {
            "query": query,
            "model_name": self.idx_to_model[pred_idx],
            "predicted_llm": self.idx_to_model[pred_idx],
            "confidence": confidence,
            "method": "feature_ml",
        }

    def route_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量路由"""
        return [self.route_single(q) for q in batch]

    def save_router(self, path: str):
        """保存模型"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'idx_to_model': self.idx_to_model,
        }, path)
        print(f"💾 Router saved to: {path}")

    def load_router(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path, map_location='cpu')
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.idx_to_model = checkpoint['idx_to_model']
        print(f"📂 Router loaded from: {path}")
```

---

## 训练器开发（可选）

### BaseTrainer 基类

如果您的路由器需要训练，创建一个继承自 `BaseTrainer` 的训练器：

```python
from llmrouter.models.base_trainer import BaseTrainer
import torch


class MyRouterTrainer(BaseTrainer):
    """
    自定义路由器训练器
    """

    def __init__(self, router, config: dict, device: str = "cpu"):
        """
        Args:
            router: 路由器实例
            config: 配置字典
            device: 训练设备
        """
        super().__init__(router, device=device, config=config)

        # 获取超参数
        self.hparam = config.get("hparam", {})
        self.lr = self.hparam.get("lr", 0.001)
        self.epochs = self.hparam.get("epochs", 10)

        # 创建优化器
        self.optimizer = torch.optim.Adam(
            self.router.model.parameters(),
            lr=self.lr
        )

        # 定义损失函数
        self.criterion = torch.nn.CrossEntropyLoss()

    def loss_func(self, outputs: torch.Tensor, batch: dict) -> torch.Tensor:
        """
        计算损失

        Args:
            outputs: 路由器输出
            batch: 包含标签的批次

        Returns:
            损失值
        """
        # 假设 batch 包含 'labels' 字段
        labels = batch.get('labels')
        return self.criterion(outputs, labels)

    def train(self, dataloader=None):
        """
        执行训练循环

        Args:
            dataloader: 可选的数据加载器
        """
        self.router.model.train()

        for epoch in range(self.epochs):
            total_loss = 0

            # 如果路由器有内置的训练数据
            if dataloader is None and hasattr(self.router, 'train_features'):
                # 使用路由器的内置数据进行训练
                dataset = torch.utils.data.TensorDataset(
                    self.router.train_features,
                    self.router.train_labels
                )
                dataloader = torch.utils.data.DataLoader(
                    dataset,
                    batch_size=self.hparam.get("batch_size", 32),
                    shuffle=True
                )

            # 训练循环
            for batch_features, batch_labels in dataloader:
                # 清空梯度
                self.optimizer.zero_grad()

                # 前向传播
                outputs = self.router.model(batch_features.to(self.device))

                # 计算损失
                loss = self.loss_func(outputs, {'labels': batch_labels.to(self.device)})

                # 反向传播
                loss.backward()
                self.optimizer.step()

                total_loss += loss.item()

            avg_loss = total_loss / len(dataloader)
            print(f"Epoch {epoch + 1}/{self.epochs}, Loss: {avg_loss:.4f}")

        # 保存模型
        save_path = self.hparam.get("save_model_path", "models/myrouter/checkpoint.pt")
        self.router.save_router(save_path)
        print(f"✅ Training completed, model saved to {save_path}")
```

### 训练器示例：简单的随机路由器训练器

```python
"""
RandomRouter Trainer - 示例训练器
==================================
"""

from llmrouter.models.base_trainer import BaseTrainer


class RandomRouterTrainer(BaseTrainer):
    """
    RandomRouter 的训练器
    由于随机路由器不需要训练，这是一个占位符实现
    """

    def __init__(self, router, config: dict, device: str = "cpu"):
        super().__init__(router, device=device, config=config)
        print("⚠️  RandomRouter 不需要训练")

    def train(self, dataloader=None):
        """训练（空操作）"""
        print("✅ RandomRouter 'training' 完成（无需实际训练）")

    def loss_func(self, outputs, batch):
        """损失计算（未实现）"""
        raise NotImplementedError("RandomRouter 不支持损失计算")
```

### 在 `trainer.py` 中导出训练器

```python
from .trainer import MyRouterTrainer

__all__ = ["MyRouter", "MyRouterTrainer"]
```

---

## 插件注册

### 自动发现机制

LLMRouter 提供自动插件发现功能，路由器会自动从以下目录发现：

1. `./custom_routers/` - 项目根目录
2. `~/.llmrouter/plugins/` - 用户目录
3. `$LLMROUTER_PLUGINS` 环境变量指定的目录

### 目录结构要求

```
custom_routers/
└── myrouter/
    ├── __init__.py         # 导出路由器类
    ├── router.py           # 路由器实现
    └── trainer.py          # 训练器实现（可选）
```

### 导出路由器类

在 `custom_routers/myrouter/__init__.py` 中：

```python
from .router import MyRouter

# 如果有训练器，也一并导出
try:
    from .trainer import MyRouterTrainer
    __all__ = ["MyRouter", "MyRouterTrainer"]
except ImportError:
    __all__ = ["MyRouter"]
```

### 验证插件是否注册成功

运行以下命令查看已注册的路由器：

```bash
llmrouter list-routers
```

你应该能在输出中看到你的自定义路由器：

```
Routers available for INFERENCE:
----------------------------------------------------------------------
  myrouter                  - MyRouter

Routers available for TRAINING:
----------------------------------------------------------------------
  myrouter                  - MyRouter / MyRouterTrainer
```

### 手动注册（可选）

如果自动发现不工作，可以手动注册路由器：

在 `llmrouter/models/__init__.py` 中添加：

```python
# 手动导入自定义路由器
try:
    from custom_routers.myrouter import MyRouter, MyRouterTrainer
    __all__.append("MyRouter")
    __all__.append("MyRouterTrainer")
except ImportError:
    pass
```

---

## 测试

### 推理测试

创建测试脚本 `tests/inference_test/test_myrouter.py`：

```python
import argparse
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from llmrouter.models import MyRouter


def main():
    # 默认配置路径
    default_yaml = os.path.join(
        project_root, "custom_routers", "myrouter", "config.yaml"
    )

    parser = argparse.ArgumentParser(description="测试 MyRouter")
    parser.add_argument(
        "--yaml_path",
        type=str,
        default=default_yaml,
        help=f"配置文件路径 (默认: {default_yaml})"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="Hello, how are you?",
        help="测试查询"
    )
    args = parser.parse_args()

    # 验证配置文件
    if not os.path.exists(args.yaml_path):
        raise FileNotFoundError(f"配置文件未找到: {args.yaml_path}")

    # 初始化路由器
    print(f"📄 使用配置文件: {args.yaml_path}")
    router = MyRouter(args.yaml_path)
    print("✅ MyRouter 初始化成功!")

    # 测试单个查询路由
    print("\n🔍 测试 route_single():")
    result = router.route_single({"query": args.query})
    print(f"查询: {args.query}")
    print(f"结果: {result}")

    # 测试批量路由
    print("\n🔍 测试 route_batch():")
    batch = [
        {"query": "What is AI?"},
        {"query": "How to code in Python?"},
        {"query": "Translate to Chinese"}
    ]
    results = router.route_batch(batch)
    for i, (query, result) in enumerate(zip(batch, results)):
        print(f"{i+1}. 查询: {query['query']}")
        print(f"   结果: {result}")

    print("\n✅ 所有测试通过!")


if __name__ == "__main__":
    main()
```

运行推理测试：

```bash
python tests/inference_test/test_myrouter.py
```

或使用 CLI：

```bash
llmrouter infer --router myrouter --config custom_routers/myrouter/config.yaml --query "Hello"
```

### 训练测试

创建测试脚本 `tests/train_test/test_myrouter.py`：

```python
import argparse
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from llmrouter.models import MyRouter
from custom_routers.myrouter.trainer import MyRouterTrainer


def main():
    default_yaml = os.path.join(
        project_root, "custom_routers", "myrouter", "config.yaml"
    )

    parser = argparse.ArgumentParser(description="测试 MyRouter 训练")
    parser.add_argument(
        "--yaml_path",
        type=str,
        default=default_yaml,
        help=f"配置文件路径 (默认: {default_yaml})"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "cuda"],
        help="训练设备"
    )
    args = parser.parse_args()

    if not os.path.exists(args.yaml_path):
        raise FileNotFoundError(f"配置文件未找到: {args.yaml_path}")

    # 初始化路由器
    print(f"📄 使用配置文件: {args.yaml_path}")
    router = MyRouter(args.yaml_path)
    print("✅ MyRouter 初始化成功!")

    # 初始化训练器
    import yaml
    with open(args.yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    print("\n🏋️  初始化训练器...")
    trainer = MyRouterTrainer(
        router=router,
        config=config,
        device=args.device
    )

    # 开始训练
    print("\n🏋️  开始训练...")
    trainer.train()

    print("\n✅ 训练测试完成!")


if __name__ == "__main__":
    main()
```

运行训练测试：

```bash
python tests/train_test/test_myrouter.py --device cpu
```

或使用 CLI：

```bash
llmrouter train --router myrouter --config custom_routers/myrouter/config.yaml --device cpu
```

---

## 常见问题

### Q1: 路由器没有被自动发现？

**A:** 检查以下几点：
1. 目录结构是否正确
2. `__init__.py` 是否存在
3. 路由器类是否正确导出
4. 类名是否以 `Router` 结尾（可选但推荐）

### Q2: 如何调试路由器？

**A:** 在 CLI 中使用详细模式：

```bash
llmrouter infer --router myrouter --config config.yaml --query "Hello" --verbose
```

或在插件系统中启用详细输出：

```python
plugin_registry = discover_and_register_plugins(verbose=True)
```

### Q3: 路由器可以访问哪些数据？

**A:** 通过 YAML 配置，路由器可以访问：

- `llm_data`: 候选 LLM 列表及配置
- `query_data_test`: 测试查询数据
- `routing_data_test`: 路由决策历史数据

这些数据在初始化时自动加载到路由器实例。

### Q4: 如何在不同设备上运行？

**A:** 使用 CLI 的 `--device` 参数：

```bash
llmrouter train --router myrouter --config config.yaml --device cuda
```

或在代码中指定：

```python
trainer = MyRouterTrainer(router, config, device="cuda")
```

### Q5: 路由器输出格式有什么要求？

**A:** 路由器输出应至少包含：

```python
{
    "query": str,           # 原始查询
    "model_name": str,      # 选中的模型名称
}
```

可选字段：

- `predicted_llm`: 替代模型名称字段
- `confidence`: 路由置信度
- `method`: 路由方法名称

---

## 参考资源

- [MetaRouter 源码](../llmrouter/models/meta_router.py)
- [BaseTrainer 源码](../llmrouter/models/base_trainer.py)
- [RandomRouter 示例](../custom_routers/randomrouter/)
- [MLPRouter 示例](../llmrouter/models/mlprouter/)
- [插件系统文档](../llmrouter/plugin_system.py)

---

## 下一步

完成本教程后，您可以：

1. 查看更多内置路由器实现
2. 阅读数据准备文档
3. 尝试不同的路由策略
4. 参与项目贡献
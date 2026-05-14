# 自定义路由器

本目录包含 LLMRouter 的用户自定义路由器实现。

## 快速开始

使用任何自定义路由器：

```bash
# 推理
llmrouter infer --router <router_name> \
  --config custom_routers/<router_name>/config.yaml \
  --query "您的问题"

# 训练（如果支持）
llmrouter train --router <router_name> \
  --config custom_routers/<router_name>/config.yaml
```

## 可用的自定义路由器

### 1. RandomRouter（随机路由器）

**类型**：基线（无需训练）

**描述**：从可用候选中随机选择一个 LLM。用作对比基线。

**使用方法**：
```bash
llmrouter infer --router randomrouter \
  --config custom_routers/randomrouter/config.yaml \
  --query "什么是 AI？" \
  --route-only
```

**特性**：
- ✅ 实现简单
- ✅ 无需训练
- ✅ 适合作为对比基线
- ✅ 可配置随机种子

### 2. ThresholdRouter（阈值路由器）

**类型**：可训练路由器

**描述**：基于预估的查询难度进行路由。使用神经网络将查询分类为简单/复杂，并相应地路由。

**核心概念**：
- 简单查询 → 较小/便宜的模型
- 复杂查询 → 较大/能力强的模型
- 从历史路由数据中学习难度评估

**训练**：
```bash
llmrouter train --router thresholdrouter \
  --config custom_routers/thresholdrouter/config.yaml
```

**推理**：
```bash
llmrouter infer --router thresholdrouter \
  --config custom_routers/thresholdrouter/config.yaml \
  --query "解释量子纠缠"
```

**特性**：
- ✅ 神经网络难度评估器
- ✅ 可配置阈值
- ✅ 完整训练流程
- ✅ 灵活的模型选择

**超参数**：
- `threshold`：难度阈值（0.0 - 1.0）
- `small_model`：高效模型的名称
- `large_model`：能力强的模型的名称
- `embedding_dim`：查询嵌入维度
- `hidden_dim`：隐藏层大小
- `learning_rate`：训练学习率
- `train_epoch`：训练轮数

## 自定义路由器插件系统

### 插件发现机制

插件系统自动在以下位置发现路由器：

1. `./custom_routers/`（当前目录）⭐ 推荐
2. `~/.llmrouter/plugins/`（用户主目录）
3. `$LLMROUTER_PLUGINS` 环境变量

### 环境变量设置

```bash
# Linux/Mac
export LLMROUTER_PLUGINS="/path/to/plugins1:/path/to/plugins2"

# Windows
set LLMROUTER_PLUGINS=C:\path\to\plugins1;C:\path\to\plugins2
```

## 如何创建自定义路由器

详细指南请参阅 [CUSTOM_ROUTER_SUMMARY.md](../CUSTOM_ROUTER_SUMMARY.md)。

### 最小模板

```python
# custom_routers/my_router/router.py
from llmrouter.models.meta_router import MetaRouter
import torch.nn as nn

class MyRouter(MetaRouter):
    def __init__(self, yaml_path: str):
        model = nn.Identity()
        super().__init__(model=model, yaml_path=yaml_path)
        self.llm_names = list(self.llm_data.keys())

    def route_single(self, query_input: dict) -> dict:
        # 您的路由逻辑
        selected = self.llm_names[0]
        return {
            "query": query_input.get("query", ""),
            "model_name": selected,
            "predicted_llm": selected,
        }

    def route_batch(self, batch: list) -> list:
        return [self.route_single(q) for q in batch]
```

### 目录结构

```
custom_routers/
├── README.md                    # 本文件
├── __init__.py                  # 包标记
├── randomrouter/                # 示例 1：简单基线
│   ├── __init__.py
│   ├── router.py
│   ├── trainer.py
│   └── config.yaml
├── thresholdrouter/             # 示例 2：可训练路由器
│   ├── __init__.py
│   ├── router.py
│   ├── trainer.py
│   └── config.yaml
└── your_router/                 # 您的自定义路由器
    ├── __init__.py
    ├── router.py
    └── config.yaml
```

## 如何注册自定义路由器

### 步骤 1：创建路由器目录

在 `custom_routers/` 下创建新的子目录：

```bash
mkdir custom_routers/my_router
cd custom_routers/my_router
```

### 步骤 2：创建路由器文件

创建以下文件：

1. **`__init__.py`**（包标记文件，可为空）
```python
"""我的自定义路由器"""
from .router import MyRouter

__all__ = ['MyRouter']
```

2. **`router.py`**（路由器实现）
```python
from llmrouter.models.meta_router import MetaRouter
import torch.nn as nn
from typing import Any, Dict, List

class MyRouter(MetaRouter):
    """
    我的自定义路由器
    """

    def __init__(self, yaml_path: str):
        """初始化路由器"""
        # 创建您的模型（如果需要）
        model = nn.Identity()

        # 初始化父类
        super().__init__(model=model, yaml_path=yaml_path)

        # 获取可用 LLM 名称
        self.llm_names = list(self.llm_data.keys())

        print(f"✅ MyRouter 已初始化，包含 {len(self.llm_names)} 个 LLM")

    def route_single(self, query_input: Dict[str, Any]) -> Dict[str, Any]:
        """路由单个查询"""
        # 实现您的路由逻辑
        selected_llm = self.llm_names[0]  # 简单示例：选择第一个

        return {
            "query": query_input.get("query", ""),
            "model_name": selected_llm,
            "predicted_llm": selected_llm,
        }

    def route_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """路由批量查询"""
        return [self.route_single(q) for q in batch]
```

3. **`config.yaml`**（配置文件，可选但推荐）
```yaml
data_path:
  llm_data: 'path/to/llm_candidates.json'

hparam:
  my_param: value
```

### 步骤 3：验证路由器已注册

```bash
# 列出所有可用的路由器（包括自定义路由器）
llmrouter list-routers
```

如果您的路由器已成功注册，它将出现在列表中。

### 步骤 4：测试路由器

```bash
# 仅测试路由（不进行 API 调用）
llmrouter infer --router my_router \
  --config custom_routers/my_router/config.yaml \
  --query "测试查询" \
  --route-only
```

## RandomRouter 示例详细说明

RandomRouter 是一个简单的基线路由器，它随机选择一个 LLM 作为目标模型。

### 核心代码

```python
class RandomRouter(MetaRouter):
    def __init__(self, yaml_path: str):
        # 创建虚拟模型（MetaRouter 要求，但不实际使用）
        dummy_model = nn.Identity()

        # 初始化父类 - 这将加载配置和数据
        super().__init__(model=dummy_model, yaml_path=yaml_path)

        # 提取超参数
        hparam = self.cfg.get("hparam", {})
        seed = hparam.get("seed", None)

        if seed is not None:
            random.seed(seed)  # 设置随机种子以保证可重现性

        # 获取可用的 LLM 名称列表
        self.llm_names = list(self.llm_data.keys())

    def route_single(self, query_input: Dict[str, Any]) -> Dict[str, Any]:
        """通过随机选择 LLM 来路由单个查询"""
        selected_llm = random.choice(self.llm_names)

        return {
            "query": query_input.get("query", ""),
            "model_name": selected_llm,
            "predicted_llm": selected_llm,
            "confidence": 1.0,
            "method": "random",
        }
```

### 配置文件示例

```yaml
data_path:
  llm_data: 'path/to/llm_candidates.json'

hparam:
  seed: 42  # 可选：设置随机种子
```

### 适用场景

- 作为性能对比的基线
- 测试和调试路由系统
- 验证基础功能

## ThresholdRouter 示例详细说明

ThresholdRouter 基于查询难度进行路由。它使用神经网络来评估查询的难度，并根据阈值选择模型。

### 核心代码

```python
class DifficultyEstimator(nn.Module):
    """用于估计查询难度的简单 MLP"""

    def __init__(self, input_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()  # 输出 [0, 1] 范围内的难度分数
        )

    def forward(self, x):
        return self.network(x)


class ThresholdRouter(MetaRouter):
    def __init__(self, yaml_path: str):
        # 创建难度评估器模型
        difficulty_model = DifficultyEstimator(embedding_dim, hidden_dim)

        # 初始化父类
        super().__init__(model=difficulty_model, yaml_path=yaml_path)

        # 提取超参数
        self.threshold = hparam.get('threshold', 0.5)
        self.small_model = hparam.get('small_model', None)
        self.large_model = hparam.get('large_model', None)

    def route_single(self, query_input: Dict[str, Any]) -> Dict[str, Any]:
        """基于难度评估路由单个查询"""
        # 获取查询嵌入
        embedding = query_input['embedding']
        if not isinstance(embedding, torch.Tensor):
            embedding = torch.tensor(embedding, dtype=torch.float32)

        # 估计难度
        difficulty = self._estimate_difficulty(embedding)

        # 根据阈值选择模型
        selected_model = self.small_model if difficulty < self.threshold else self.large_model

        return {
            "query": query_input.get("query", ""),
            "model_name": selected_model,
            "predicted_llm": selected_model,
            "difficulty_score": difficulty,
            "threshold": self.threshold,
            "method": "threshold",
        }
```

### 配置文件示例

```yaml
data_path:
  llm_data: 'path/to/llm_candidates.json'

hparam:
  threshold: 0.5           # 难度阈值
  small_model: 'gpt-3.5-turbo'      # 小模型名称
  large_model: 'gpt-4'             # 大模型名称
  embedding_dim: 768               # 查询嵌入维度
  hidden_dim: 128                  # 隐藏层维度
  learning_rate: 0.001             # 学习率
  train_epoch: 10                  # 训练轮数

model_path:
  save_model_path: 'checkpoints/threshold_router.pt'  # 模型保存路径
  load_model_path: null           # 模型加载路径（训练后设置）
```

### 适用场景

- 需要根据查询复杂度动态选择模型
- 优化成本（简单查询使用便宜模型）
- 保证质量（复杂查询使用高级模型）

## 验证您的路由器

```bash
# 列出所有可用的路由器（包括自定义路由器）
llmrouter list-routers

# 仅测试路由（不进行 API 调用）
llmrouter infer --router your_router \
  --config custom_routers/your_router/config.yaml \
  --query "测试查询" \
  --route-only

# 启用详细输出
LLMROUTER_DEBUG=1 llmrouter infer --router your_router \
  --config config.yaml --query "测试" --verbose
```

## 测试您的路由器

### 单元测试

```python
# test_my_router.py
from custom_routers.my_router import MyRouter

def test_router():
    router = MyRouter("custom_routers/my_router/config.yaml")

    result = router.route_single({"query": "什么是 AI？"})

    assert "model_name" in result
    assert result["model_name"] in router.llm_names
    print("✅ 路由器测试通过")

if __name__ == "__main__":
    test_router()
```

### 集成测试

```bash
# 使用实际 LLM API 调用进行测试
llmrouter infer --router my_router \
  --config custom_routers/my_router/config.yaml \
  --query "将 'hello' 翻译成西班牙语" \
  --verbose
```

## 路由器设计模式

### 1. 基于规则的路由器

```python
def route_single(self, query_input):
    query = query_input['query'].lower()

    if 'code' in query or 'program' in query:
        return {"model_name": "code-specialized-model"}
    elif len(query) < 50:
        return {"model_name": "small-fast-model"}
    else:
        return {"model_name": "large-capable-model"}
```

### 2. 基于嵌入的路由器

```python
def route_single(self, query_input):
    embedding = self._get_embedding(query_input['query'])
    similarity_scores = self._compute_similarity(embedding)
    best_model = max(similarity_scores, key=similarity_scores.get)
    return {"model_name": best_model}
```

### 3. 成本感知路由器

```python
def route_single(self, query_input):
    difficulty = self._estimate_difficulty(query_input)

    # 路由到能够处理该难度的最便宜模型
    for model in sorted(self.llm_data.items(), key=lambda x: x[1]['cost']):
        if model[1]['capability'] >= difficulty:
            return {"model_name": model[0]}
```

### 4. 集成路由器

```python
def route_single(self, query_input):
    # 获取多个子路由器的预测
    votes = [r.route_single(query_input) for r in self.sub_routers]

    # 多数投票
    from collections import Counter
    model_counts = Counter(v['model_name'] for v in votes)
    best_model = model_counts.most_common(1)[0][0]

    return {"model_name": best_model}
```

## 常见模式

### 缓存嵌入

```python
class CachedEmbeddingRouter(MetaRouter):
    def __init__(self, yaml_path: str):
        super().__init__(...)
        self.embedding_cache = {}

    def _get_embedding(self, query):
        if query not in self.embedding_cache:
            self.embedding_cache[query] = compute_embedding(query)
        return self.embedding_cache[query]
```

### 记录路由决策

```python
def route_single(self, query_input):
    result = self._do_routing(query_input)

    # 记录决策
    with open('routing_log.jsonl', 'a') as f:
        log_entry = {
            'timestamp': time.time(),
            'query': query_input['query'],
            'routed_to': result['model_name'],
            'confidence': result.get('confidence')
        }
        f.write(json.dumps(log_entry) + '\n')

    return result
```

## 成功提示

1. **从 RandomRouter 开始**：首先理解接口
2. **使用示例数据**：在使用自定义数据之前先测试提供的数据
3. **增量实现**：在进行优化之前先让基本路由工作
4. **添加日志**：帮助调试和理解路由行为
5. **版本控制**：使用 git 跟踪更改
6. **记录决策**：注释为什么以某种方式路由

## 分享您的路由器

如果您的路由器满足以下条件，请考虑分享：
- 解决了常见问题
- 展示了新颖技术
- 实现了良好性能

提交方式：
1. GitHub Pull Request
2. 社区 Slack 频道
3. 独立包发布

## 支持

- 文档：[CUSTOM_ROUTER_SUMMARY.md](../CUSTOM_ROUTER_SUMMARY.md)
- GitHub Issues：报告错误或请求功能
- 示例：研究 `randomrouter` 和 `thresholdrouter`
- 社区：加入我们的 Slack 进行讨论

---

愉快路由！🚀
# MF 路由器 (矩阵分解路由器)

## 概述

**MF 路由器** (Matrix Factorization Router) 使用双线性矩阵分解来学习查询和大语言模型的潜在嵌入表示。它通过在共享的潜在空间中计算亲和度来为每个查询预测最佳模型，类似于推荐系统中使用的协同过滤技术。

## 论文参考

该路由器的灵感来源于 **RouteLLM** 和矩阵分解方法：

- **[RouteLLM: Learning to Route LLMs with Preference Data](https://arxiv.org/abs/2406.18665)**
  - Ong, I., et al. (2024). arXiv:2406.18665. 发表于 ICLR 2025。
  - 提出了在人类偏好数据上训练的矩阵分解路由器。

- **矩阵分解**: Koren, Y., Bell, R., & Volinsky, C. (2009). "Matrix factorization techniques for recommender systems." Computer.

该方法将 LLM 路由视为推荐问题：给定查询，推荐性能最佳的模型。

## 工作原理

### 架构

```
查询 → Longformer 嵌入 → 投影 → 潜在空间
                                           ↓
                                      交互
                                           ↓
模型嵌入 (可学习) ────────────→ 评分 → LLM 选择
```

### 双线性评分函数

路由器使用以下公式计算路由分数：

```
δ(M, q) = w2^T (v_m ⊙ (W1 * v_q))
```

其中：
- `v_q`: 投影到潜在空间的查询嵌入
- `v_m`: 可学习的模型嵌入
- `⊙`: 逐元素乘积 (Hadamard 乘积)
- `W1`: 线性投影矩阵
- `w2`: 最终评分向量

### 训练过程

1. **成对样本生成**：
   - 对于每个查询，识别性能最佳的模型 (胜者)
   - 创建成对数据：(query, winner, loser)，包含所有其他模型

2. **成对排序损失**：
   - 优化目标：`δ(winner, q) > δ(loser, q)`
   - 使用 logistic 损失保证可微性

3. **潜在空间学习**：
   - 联合学习查询投影 `W1` 和模型嵌入 `P`
   - 归一化嵌入有助于提升泛化能力

## 配置参数

### 训练超参数 (配置中的 `hparam`)

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `latent_dim` | int | `128` | 模型潜在嵌入空间的维度。数值越高模型容量越大。范围：64-256。 |
| `text_dim` | int | `768` | Longformer 查询嵌入的维度 (固定为 768)。 |
| `lr` | float | `0.001` | Adam 优化器的学习率。典型范围：0.0001-0.01。 |
| `epochs` | int | `5` | 训练轮数。对于较大的数据集可增加此值。 |
| `batch_size` | int | `64` | 训练批次大小。较大的值可加速训练但占用更多内存。范围：32-256。 |
| `noise_alpha` | float | `0.0` | 可选的添加到查询嵌入的高斯噪声，用于正则化。范围：0.0-0.1。 |

### 数据路径

| 参数 | 描述 |
|-----------|-------------|
| `routing_data_train` | 包含查询-LLM 性能对的训练数据 (JSONL 格式) |
| `query_embedding_data` | 预计算的 Longformer 查询嵌入 (PyTorch 张量文件) |
| `llm_data` | LLM 候选模型信息 |

### 模型路径

| 参数 | 用途 | 使用场景 |
|-----------|---------|-------|
| `save_model_path` | 保存训练模型的路径 | 训练时：保存模型 state_dict 为 `.pkl` 文件 |
| `load_model_path` | 加载推理模型的路径 | 测试时：加载训练好的模型权重 |

## CLI 使用方法

MF 路由器可以通过 `llmrouter` 命令行接口使用：

### 训练

```bash
# 训练 MF 路由器
llmrouter train --router mfrouter --config configs/model_config_train/mfrouter.yaml

# 使用 GPU 加速训练
llmrouter train --router mfrouter --config configs/model_config_train/mfrouter.yaml --device cuda

# 使用静默模式训练
llmrouter train --router mfrouter --config configs/model_config_train/mfrouter.yaml --quiet
```

### 推理

```bash
# 路由单个查询
llmrouter infer --router mfrouter --config configs/model_config_test/mfrouter.yaml \
    --query "解释神经网络"

# 从文件路由查询
llmrouter infer --router mfrouter --config configs/model_config_test/mfrouter.yaml \
    --input queries.jsonl --output results.json

# 仅路由 (不调用 LLM API)
llmrouter infer --router mfrouter --config configs/model_config_test/mfrouter.yaml \
    --query "什么是深度学习?" --route-only
```

### 交互式聊天

```bash
# 启动聊天界面
llmrouter chat --router mfrouter --config configs/model_config_test/mfrouter.yaml

# 使用自定义端口启动
llmrouter chat --router mfrouter --config configs/model_config_test/mfrouter.yaml --port 8080

# 创建可公开分享的链接
llmrouter chat --router mfrouter --config configs/model_config_test/mfrouter.yaml --share
```

---

## 使用示例

### 训练 MF 路由器

```python
from llmrouter.models import MFRouter, MFRouterTrainer

# 使用训练配置初始化路由器
router = MFRouter(yaml_path="configs/model_config_train/mfrouter.yaml")

# 创建训练器
trainer = MFRouterTrainer(router=router, device="cpu")

# 训练模型
trainer.train()
# 模型保存到 save_model_path
```

**命令行方式：**
```bash
python tests/train_test/test_mfrouter.py --yaml_path configs/model_config_train/mfrouter.yaml
```

### 推理

```python
from llmrouter.models import MFRouter

# 初始化路由器
router = MFRouter(yaml_path="configs/model_config_test/mfrouter.yaml")

# 路由查询
query = {"query": "解释神经网络"}
result = router.route_single(query)
print(f"选中的模型: {result['model_name']}")
```

## YAML 配置示例

```yaml
data_path:
  routing_data_train: 'data/example_data/routing_data/default_routing_train_data.jsonl'
  query_embedding_data: 'data/example_data/routing_data/query_embeddings_longformer.pt'
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

model_path:
  save_model_path: 'saved_models/mfrouter/mfrouter.pkl'

hparam:
  latent_dim: 128
  text_dim: 768
  lr: 0.001
  epochs: 5
  batch_size: 64
  noise_alpha: 0.0

metric:
  weights:
    performance: 1
    cost: 0
```

## 优势

- ✅ **潜在空间学习**: 学习有意义的查询-模型表示
- ✅ **协同过滤**: 利用跨查询和模型的模式
- ✅ **可扩展性**: 使用学习的嵌入进行高效推理
- ✅ **灵活容量**: 可根据数据规模调整潜在维度

## 局限性

- ❌ **冷启动问题**: 新模型需要重新训练以获得嵌入
- ❌ **嵌入依赖**: 需要预计算的查询嵌入
- ❌ **可解释性有限**: 潜在空间不易解释
- ❌ **成对训练**: 需要所有模型对进行训练

## 何时使用 MF 路由器

**适用场景：**
- 中等到大型数据集，包含多样化查询
- 多个具有不同能力的模型
- 希望学习查询-模型亲和度
- 具有协同过滤思维

**考虑替代方案：**
- 小型数据集 → KNN 路由器
- 需要可解释性 → SVM/MLP 路由器
- 实时模型更新 → 在线学习方法

## 相关路由器

- **图路由器**: 同样学习结构化表示
- **MLP/SVM 路由器**: 有监督的替代方案
- **KNN 路由器**: 基于实例的方法，无潜在空间

---

如有问题或建议，请参考主 LLMRouter 文档或在 GitHub 上提交 issue。
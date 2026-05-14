# GMT 个性化路由器说明文档

## 论文参考

- **[GMTRouter: Personalized LLM Router over Multi-turn User Interactions](https://arxiv.org/abs/2511.08590)**
  - Xie, E., et al. (2025). arXiv:2511.08590.
  - 提出基于图神经网络的个性化路由，通过用户偏好学习优化模型选择。

## 重要提示

**GMT 路由器使用了与其他路由器完全不同的架构和数据格式。**

- **原始仓库**: https://github.com/ulab-uiuc/GMTRouter
- **训练状态**: ✅ **已完全集成到 LLMRouter** - 可通过 LLMouter CLI 进行训练和推理
- **数据格式**: 特殊的 JSONL 格式，包含嵌入向量和评分（见下文）

## 概述

GMT 路由器是一种专为多轮对话设计的个性化 LLM 路由器。它使用**异构图神经网络（HeteroGNN）**来学习用户偏好，并在对话会话中优化模型选择。

### 与其他路由器的关键区别

| 方面 | GMT 路由器 | 其他路由器 (KNN, MLP 等) |
|--------|-----------|----------------------------|
| **架构** | 具有 5 种节点类型的异构图神经网络 | 单一模型（分类器、排序器） |
| **数据格式** | 包含嵌入向量和评分的特殊 JSONL | 标准查询-响应对 |
| **学习方式** | 成对偏好学习 | 分类/排序 |
| **个性化** | 每用户偏好嵌入 | 无个性化 |
| **多轮对话** | 内置对话上下文跟踪 | 单轮或基本历史记录 |
| **图结构** | 21 种边类型，5 种节点类型 | 无图结构 |

## GMT 路由器原理

### 异构图结构

GMT 路由器将路由建模为具有 **5 种节点类型**的异构图：

1. **用户节点**: 学习的用户偏好嵌入（初始化为零，训练过程中更新）
2. **会话节点**: 对话会话表示（跟踪多轮交互）
3. **查询节点**: 来自预训练语言模型（PLM）的查询嵌入
4. **LLM 节点**: 来自 PLM 的模型嵌入
5. **响应节点**: 响应质量表示（基于评分）

### 21 种边类型

图包含 21 种有向边类型，用于建模各种关系：

- **用户-会话边**: `own`, `owned_by`
- **查询-响应边**: `answered_by`, `answered_to`
- **时间边**: `next`, `prev`（用于会话和查询）
- **LLM 关系边**: `receive`, `generate`, `response_to`
- 以及 13 种其他边类型...

### 用户偏好学习

GMT 路由器的核心是用户偏好学习机制：

1. ** pairwise 比较**: 对于同一用户在同一问题上的两个 LLM 响应，系统会比较它们的评分
2. **偏好嵌入**: 每个用户有一个可学习的嵌入向量，随着交互不断更新
3. **上下文感知**: 结合查询上下文和用户历史偏好进行模型选择

### 模型组件

#### 1. 异构图神经网络（HeteroGNN）

使用 HGT（异构图 Transformer）层：
- 单轮任务：2 层
- 多轮对话：3 层
- 在异构节点类型之间聚合信息

**工作原理**:
- 接收图数据（节点特征和边索引）
- 通过多层 HGT 变换传递信息
- 输出聚合后的节点嵌入

#### 2. 偏好预测器（PreferencePredictor）

基于交叉注意力机制：
- 根据用户嵌入和查询上下文对 LLM 候选模型进行评分
- 输出每个模型的偏好分数

**工作原理**:
```python
# 查询作为查询向量，用户和 LLM 作为键值对
context = [user_embedding, llm_embedding]
attn_output = cross_attention(query_embedding, context, context)
score = mlp(attn_output)  # 输出偏好分数
```

### 训练流程

1. **数据加载**: 加载 JSONL 格式的用户交互数据
2. **图构建**: 构建具有 5 种节点类型和 21 种边类型的异构图
3. **模型初始化**: 创建 HeteroGNN + PreferencePredictor 架构
4. **成对学习**: 在成对比较上训练（胜者 vs 败者）
5. **评估**: 每 N 轮验证一次（使用 AUC 或准确率）
6. **检查点保存**: 保存最佳模型和定期检查点

**损失函数**:
```python
# 二元交叉熵损失
label = [1.0, 0.0]  # [胜者, 败者]
scores = [score_winner, score_loser]
loss = binary_cross_entropy_with_logits(scores, label)
```

## 配置参数和数据要求

### 数据格式要求

#### JSONL 结构

GMT 路由器需要**特殊的 JSONL 格式**（非标准 LLMouter 格式）：

```json
{
  "judge": "user_001",
  "model": "gpt-4",
  "question_id": "12345",
  "turn": 1,
  "conversation": [
    {
      "query": "什么是机器学习？",
      "query_emb": [0.123, -0.456, 0.789, ...],
      "response": "机器学习是人工智能的一个子集...",
      "rating": 4.5
    }
  ],
  "model_emb": [0.234, -0.567, 0.891, ...],
  "encoder": "sentence-transformers/all-mpnet-base-v2"
}
```

#### 字段说明

| 字段 | 类型 | 描述 |
|-------|------|-------------|
| `judge` | string | 用户标识符（如 "user_001"） |
| `model` | string | LLM 模型名称（如 "gpt-4", "claude-2"） |
| `question_id` | string | 唯一的问题/任务标识符 |
| `turn` | int | 多轮对话中的轮次编号（1, 2, 3, ...） |
| `conversation` | array | 对话轮次列表（见下文） |
| `model_emb` | array | 来自 PLM 的 LLM 嵌入向量 |
| `encoder` | string | 用于嵌入的 PLM 模型（可选） |

#### 对话轮次结构

`conversation` 数组中的每一轮包含：

```json
{
  "query": "查询文本",
  "query_emb": [0.1, 0.2, ...],     // 来自 PLM 的查询嵌入
  "response": "响应文本",            // 可选
  "rating": 4.5                      // 质量评分（0-5 或 0-1）
}
```

### 支持的数据集

- **chatbot_arena**: 来自 Chatbot Arena 的真实用户偏好
- **gsm8k**: 小学数学问题
- **mmlu**: 大规模多任务语言理解基准
- **mt_bench**: 多轮对话基准

### 配置参数

#### GMT 路由器特定配置（`gmt_config`）

- **`num_gnn_layers`** (int, 默认: `2`)
  - HeteroGNN 中 HGT（异构图 Transformer）层的数量
  - 推荐：大多数任务使用 2 层
  - 范围：2-4

- **`hidden_dim`** (int, 默认: `128`)
  - 图节点嵌入的隐藏维度
  - 范围：64-256

- **`dropout`** (float, 默认: `0.1`)
  - 训练期间的正则化 dropout 率
  - 范围：0.0-0.3

- **`personalization`** (bool, 默认: `true`)
  - 启用用户偏好学习
  - 启用时，路由查询需要 `user_id` 字段
  - 学习随交互演变的每用户嵌入

#### 训练参数（`train`）

- **`epochs`** (int, 默认: `350`)
  - 训练轮数
  - GMT 路由器通常在 200-350 轮收敛

- **`lr`** (float, 默认: `5e-4`)
  - 优化器的学习率
  - 推荐：5e-4（适用于大多数数据集）

- **`prediction_count`** (int, 默认: `256`)
  - 每个训练批次的成对偏好预测数量
  - 较高的值提供更稳定的梯度但训练速度较慢

- **`objective`** (string, 默认: `"auc"`)
  - 训练目标指标
  - 选项：`"auc"`（曲线下面积）或 `"accuracy"`

- **`binary`** (bool, 默认: `true`)
  - 使用成对偏好学习（二元分类）
  - 推荐对基于偏好的路由保持 `true`

- **`eval_every`** (int, 默认: `5`)
  - 每隔多少轮进行验证
  - 模型每 N 轮在验证集上评估一次

- **`seed`** (int, 默认: `136`)
  - 用于可重复性的随机种子
  - 确保训练运行之间结果一致

## 训练和推理示例

### 训练示例

#### 1. 准备数据

```bash
# 下载数据集（从 GMT 路由器仓库获取最新链接）
wget "https://drive.google.com/uc?export=download&id=[dataset_id]" -O GMTRouter_dataset.tar.gz

# 提取归档
tar -xzvf GMTRouter_dataset.tar.gz

# 移动数据文件夹到仓库根目录
mv data ./
```

#### 2. 配置训练参数

编辑 `configs/model_config_train/gmtrouter.yaml`:

```yaml
dataset:
  name: mt_bench          # 选择：chatbot_arena, gsm8k, mmlu, mt_bench
  path: ./data

train:
  epochs: 350             # 训练轮数
  lr: 5e-4                # 学习率（推荐 5e-4）
  prediction_count: 256   # 每批次的成对预测数
  objective: auc          # 指标：auc 或 accuracy
  binary: true            # 成对比较学习
  eval_every: 5           # 验证频率
  seed: 136               # 随机种子

gmt_config:
  num_gnn_layers: 2       # HGT 层数（单轮 2 层，多轮 3 层）
  hidden_dim: 128         # 节点嵌入的隐藏维度
  dropout: 0.1            # 正则化 dropout 率
  personalization: true   # 启用用户偏好学习

checkpoint:
  root: ./models
  save_every: 25          # 检查点频率

data_path:
  training_set: ./data/mt_bench/training_set.jsonl
  valid_set: ./data/mt_bench/valid_set.jsonl
  test_set: ./data/mt_bench/test_set.jsonl

model_path:
  save_model_path: ./saved_models/gmtrouter/gmtrouter.pt
  load_model_path: ./saved_models/gmtrouter/gmtrouter.pt
```

#### 3. 开始训练

```bash
# 使用 GPU 训练 GMT 路由器（推荐）
llmouter train --router gmtrouter --config configs/model_config_train/gmtrouter.yaml --device cuda

# 使用安静模式训练
llmouter train --router gmtrouter --config configs/model_config_train/gmtrouter.yaml --device cuda --quiet
```

#### 4. 训练输出示例

```
======================================================================
GMT 路由器训练
======================================================================
从 ./data/mt_bench/training_set.jsonl 加载训练数据...
检测到格式：gmtrouter
构建异构图...
  - 用户：150, 会话：450, 查询：1200, LLM：8, 响应：1200
  - 边类型：21
  - 成对比较：3600

训练配置：
  设备：cuda
  轮数：350
  学习率：5e-4
  隐藏维度：128
  GNN 层数：2
  目标：auc
  二元分类：True

轮次 5/350 - 训练损失：0.4523, 训练 AUC：0.7245 - 验证损失：0.4012, 验证 AUC：0.7856
  → 已保存最佳模型到 ./saved_models/gmtrouter/gmtrouter.pt
...
训练完成！
最佳 AUC：0.8934（轮次 245）
```

### 推理示例

#### 1. 单查询路由

```python
from llmouter.models.gmtrouter import GMT 路由器

# 使用测试配置初始化
router = GMT 路由器(yaml_path='configs/model_config_test/gmtrouter.yaml')

# 带用户上下文的路由
query = {
    "query_text": "用简单的术语解释量子计算",
    "user_id": "user_123",          # 个性化必需
    "session_id": "session_456",    # 可选
    "turn": 1,                       # 可选
    "conversation_history": []       # 可选：之前的轮次
}

result = router.route_single(query)
print(result)
# {
#   "model_name": "gpt-4",
#   "confidence": 0.87,
#   "user_preference": 0.92,
#   "reasoning": "基于用户 user_123 的学习偏好选择..."
# }
```

#### 2. 多轮对话

```python
user_id = "user_789"
session_id = "session_123"

conversation = [
    "什么是机器学习？",
    "它与深度学习有什么区别？",
    "你能给我一个实际例子吗？"
]

for turn, query_text in enumerate(conversation, start=1):
    query = {
        "query_text": query_text,
        "user_id": user_id,
        "session_id": session_id,
        "turn": turn
    }

    result = router.route_single(query)
    print(f"轮次 {turn}: {result['model_name']} (置信度: {result['confidence']:.2f})")
```

#### 3. 批量路由

```python
batch = [
    {"query_text": "解决 2+2", "user_id": "user_001"},
    {"query_text": "写一首诗", "user_id": "user_001"},
    {"query_text": "调试这段代码", "user_id": "user_002"}
]

results = router.route_batch(batch)
for q, r in zip(batch, results):
    print(f"{q['query_text']}: {r['model_name']}")
```

#### 4. 更新用户反馈

```python
# 记录用户反馈以改进未来的路由
router.update_user_feedback(
    user_id="user_123",
    query="什么是 AI？",
    model="gpt-4",
    rating=4.5  # 用户评分（0-5 分制）
)
```

#### 5. 命令行推理

```bash
# 路由单个查询
llmouter infer --router gmtrouter --config configs/model_config_test/gmtrouter.yaml \
    --query "用简单的术语解释量子计算"

# 从文件路由查询
llmouter infer --router gmtrouter --config configs/model_config_test/gmtrouter.yaml \
    --input queries.jsonl --output results.json

# 仅路由（不调用 LLM API）
llmouter infer --router gmtrouter --config configs/model_config_test/gmtrouter.yaml \
    --query "解决这个微积分问题" --route-only

# 启动聊天界面
llmouter chat --router gmtrouter --config configs/model_config_test/gmtrouter.yaml

# 使用自定义端口启动聊天界面
llmouter chat --router gmtrouter --config configs/model_config_test/gmtrouter.yaml --port 8080

# 创建可公开共享的链接
llmouter chat --router gmtrouter --config configs/model_config_test/gmtrouter.yaml --share
```

## 适用场景和优缺点

### 适用场景

#### ✅ 理想用例

- **个性化聊天机器人**: 服务于长期用户的系统
- **多用户平台**: 具有不同用户配置文件的应用程序
- **对话式 AI**: 基于上下文构建的多轮对话
- **偏好敏感任务**: 路由取决于用户口味的任务（创意写作、推荐）
- **长期交互**: 用户在数周/数月内参与的情况

#### ❌ 不推荐的情况

- **匿名用户**: 无法构建用户配置文件
- **单轮任务**: 没有对话历史可以利用
- **简单路由**: 对于基本查询→模型映射，开销不值得
- **无用户反馈**: 没有评分无法学习偏好
- **冷启动关键**: 需要为新用户立即获得最佳性能

### 优点

1. **个性化**: 随着时间推移学习个人用户偏好
2. **多轮感知**: 显式建模对话上下文
3. **丰富的图结构**: 5 种节点类型和 21 种边类型捕获复杂关系
4. **偏好学习**: 成对比较训练镜像人类判断
5. **可扩展**: 高效的图操作处理许多用户/会话
6. **自适应**: 用户嵌入随着交互不断演化

### 缺点

1. **复杂的设置**: 需要 PyTorch Geometric 和特定的数据格式
2. **冷启动**: 没有历史记录的新用户获得通用路由
3. **数据要求**: 需要带评分的用户交互数据
4. **训练复杂性**: 数据格式与其他路由器不兼容
5. **内存**: 存储用户/会话嵌入（可能增长很大）
6. **与 LLMouter 不同**: 特殊数据格式与其他路由器不兼容

## 与其他路由器的比较

| 路由器 | 个性化 | 多轮对话 | 基于图 | 训练复杂度 | 冷启动 |
|--------|--------|----------|--------|------------|--------|
| **GMT 路由器** | ✅ 是 | ✅ 是 | ✅ HeteroGNN | 🔴 高 | 🔴 差 |
| GraphRouter | ❌ 否 | ❌ 否 | ✅ GNN | 🟡 中 | ✅ 好 |
| KNNMultiRoundRouter | ❌ 否 | ✅ 是 | ❌ 否 | 🟢 低 | ✅ 好 |
| Router-R1 | ❌ 否 | ✅ 是 | ❌ 否 | 🟢 预训练 | ✅ 好 |
| MLPRouter | ❌ 否 | ❌ 否 | ❌ 否 | 🟢 低 | ✅ 好 |

## 技术要求

- **Python**: 3.11.13
- **PyTorch**: 2.6+ with CUDA 12.4+
- **PyTorch Geometric**: 2.6.1
- **transformers**: ≥ 4.43
- **scikit-learn**: ≥ 1.3
- **GPU**: 推荐用于训练（8GB+ VRAM）

## 故障排除

### 问题: "GMT 路由器模型未加载"

**解决方案**: 您需要训练好的检查点。选择以下之一：
1. 使用原始 GMT 路由器仓库进行训练
2. 将预训练检查点放置在 `./models/gmtrouter_checkpoint.pt`

### 问题: "PyTorch Geometric 导入错误"

**解决方案**: 安装 PyTorch Geometric:
```bash
pip install torch-geometric==2.6.1
```

### 问题: "用户未找到 - 使用回退路由"

**解决方案**: 这对新用户来说是正常的。路由器需要从交互历史中学习用户偏好。经过足够的交互后，将学习用户嵌入并且路由将变得个性化。

### 问题: "数据格式不正确"

**解决方案**: GMT 路由器需要带有嵌入向量和评分的特殊 JSONL 格式。见上文"数据格式要求"部分。您不能使用标准 LLMouter 查询文件。

## 参考资源

- **GMT 路由器仓库**: https://github.com/ulab-uiuc/GMTRouter
- **HGT 论文**: "Heterogeneous Graph Transformer" (Hu et al., WWW 2020)
- **PyTorch Geometric 文档**: https://pytorch-geometric.readthedocs.io/
- **偏好学习**: Bradley-Terry 模型、成对比较

## 示例输出

```python
>>> router = GMT 路由器('configs/model_config_test/gmtrouter.yaml')
>>> query = {
...     "query_text": "解决这个微积分问题",
...     "user_id": "student_042",
...     "session_id": "homework_session_1",
...     "turn": 3
... }
>>> result = router.route_single(query)
>>> print(result)
{
    'model_name': 'gpt-4',
    'confidence': 0.91,
    'user_preference': 0.94,
    'reasoning': '基于用户 student_042 的学习偏好和对话上下文选择'
}
```

## 聊天界面差异

在 LLMouter 聊天界面中使用 GMT 路由器时：

- **需要用户 ID**: 每个用户应该有一个持久 ID
- **会话跟踪**: 会话维护对话上下文
- **反馈收集**: 可选择收集评分以改进路由
- **预热期**: 最初的几个查询可能使用回退路由

聊天设置示例：

```python
# 在聊天界面中
from llmouter.models.gmtrouter import GMT 路由器

router = GMT 路由器('configs/model_config_test/gmtrouter.yaml')

# 对于每条用户消息
query = {
    "query_text": user_input,
    "user_id": current_user_id,      # 来自登录/会话
    "session_id": chat_session_id,
    "turn": turn_number
}

routing_result = router.route_single(query)
selected_model = routing_result['model_name']

# 获得响应后，可选择收集评分
# router.update_user_feedback(current_user_id, user_input, selected_model, rating)
```

## 许可证

GMT 路由器使用 MIT 许可证发布。详细信息请参阅原始仓库。
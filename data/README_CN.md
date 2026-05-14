# 数据目录说明

本文档介绍 LLMRouter 项目的数据目录结构、支持的数据集类型以及数据文件格式。

## 目录结构

```
data/
├── charades_ego/           # Charades-Ego 数据集（视频理解）
├── chatbot_arena/          # Chatbot Arena 数据集
├── dcrouter_preprocessed/  # DCRouter 预处理数据
├── default_data/           # 默认路由训练和测试数据
├── example_data/           # 示例数据和文档
├── human_eval/             # HumanEval 数据集（代码生成）
├── mbpp/                   # MBPP 数据集（代码生成）
├── mt_bench/               # MT-Bench 数据集
└── multimodal_tasks/       # 多模态任务数据
```

## 主要目录说明

### example_data

示例数据目录，包含：
- `assets/`: 资源文件
- `README.md`: 示例数据说明文档

此目录用于演示数据格式和使用方法。

### multimodal_tasks

多模态任务数据目录，支持视觉-语言模型（VLM）集成，用于处理图像和视频数据。

支持 3 个数据集和 5 种多模态任务：

1. **Geometry3K**（几何问题求解）
   - 图形几何问题的视觉推理任务
   - 结合图像描述和文本推理

2. **MathVista**（视觉数学推理）
   - 包含图表、公式的复杂数学问题
   - 需要 VLM 提供视觉上下文

3. **Charades-Ego**（视频理解）
   - 第一人称和第三人称视频配对数据集
   - 支持三种任务类型：
     - Activity Recognition（活动识别）
     - Object Recognition（物体识别）
     - Verb Recognition（动词识别）

### default_data

默认路由训练和测试数据，包含：
- `default_routing_train_data.jsonl`: 训练数据（JSONL 格式）
- `default_routing_test_data.jsonl`: 测试数据（JSONL 格式）
- `default_routing_train_data.csv`: 训练数据（CSV 格式）
- `default_routing_test_data.csv`: 测试数据（CSV 格式）

### 其他数据集

- **charades_ego**: 完整的 Charades-Ego 数据集处理流程
- **chatbot_arena**: Chatbot Arena 竞赛数据集
- **dcrouter_preprocessed**: DCRouter 相关预处理数据
- **human_eval**: HumanEval 代码生成评估数据集
- **mbpp**: Mostly Basic Python Problems 数据集
- **mt_bench**: 多轮对话基准测试数据集

## 数据文件格式

### JSONL 格式

JSONL（JSON Lines）是 LLMRouter 使用的主要数据格式，每行是一个独立的 JSON 对象。

**训练数据格式示例：**

```json
{
  "task_name": "agentverse-logicgrid",
  "query": "问题描述...",
  "ground_truth": "C",
  "metric": "em_mc",
  "choices": {"text": ["1", "2", "3"], "labels": ["A", "B", "C"]},
  "task_id": null,
  "model_name": "llama3-chatqa-1.5-8b",
  "response": "B",
  "token_num": 453,
  "input_tokens": 449,
  "output_tokens": 4,
  "response_time": 1.7864494324,
  "api_key_used": "rivTkKeBPm",
  "performance": 0.0,
  "embedding_id": 61,
  "user_id": null,
  "fig_id": null
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_name` | string | 任务名称 |
| `query` | string | 查询问题或输入文本 |
| `ground_truth` | string | 正确答案 |
| `metric` | string | 评估指标（如 `em_mc` 表示多选完全匹配） |
| `choices` | object | 选项配置（用于选择题） |
| `task_id` | string/null | 任务 ID |
| `model_name` | string | 使用的模型名称 |
| `response` | string | 模型响应 |
| `token_num` | number | 总 token 数 |
| `input_tokens` | number | 输入 token 数 |
| `output_tokens` | number | 输出 token 数 |
| `response_time` | number | 响应时间（秒） |
| `api_key_used` | string | 使用的 API 密钥 |
| `performance` | number | 性能得分 |
| `embedding_id` | number | 嵌入向量 ID |
| `user_id` | string/null | 用户 ID（用于个性化路由） |
| `fig_id` | string/null | 图像/视频 ID |

### CSV 格式

CSV 格式提供与 JSONL 相同的信息，便于使用表格工具查看和分析。

## 支持的数据集类型

LLMRouter 支持以下类型的数据集：

1. **代码生成**
   - HumanEval
   - MBPP

2. **多轮对话**
   - MT-Bench
   - Chatbot Arena

3. **多模态任务**
   - Geometry3K（几何问题）
   - MathVista（视觉数学）
   - Charades-Ego（视频理解）

4. **逻辑推理**
   - AgentVerse Logic Grid

5. **通用任务**
   - 自定义分类任务
   - 自定义问答任务

## 数据文件用途

### 训练用途

- **路由器训练**: 使用包含多个模型响应的数据训练路由器，学习将查询路由到最佳模型
- **模型评估**: 评估不同模型在各种任务上的性能
- **特征学习**: 学习查询嵌入和模型匹配特征

### 测试用途

- **路由器评估**: 评估训练好的路由器在新数据上的性能
- **性能基准**: 作为不同路由算法的比较基准
- **模型选择**: 测试和验证模型选择策略

### 多模态用途

- **视觉理解**: 结合 VLM 提供的图像/视频描述
- **跨模态路由**: 在视觉和文本之间进行智能路由
- **场景感知**: 根据视觉上下文选择合适的模型

## 数据生成流程

LLMRouter 提供完整的数据生成管道：

1. **原始数据加载**: 从各种基准数据集加载数据
2. **模型调用**: 自动调用多个 LLM API 生成响应
3. **性能评估**: 评估每个模型的性能
4. **特征提取**: 提取查询嵌入和其他特征
5. **格式转换**: 转换为标准 JSONL/CSV 格式

详细文档请参考各数据集子目录中的 README.md 文件。

## 相关文档

- [example_data/README.md](./example_data/README.md) - 示例数据说明
- [multimodal_tasks/README.md](./multimodal_tasks/README.md) - 多模态任务指南
- [charades_ego/README.md](./charades_ego/README.md) - Charades-Ego 集成指南
- [主项目 README](../README.md) - LLMRouter 项目文档
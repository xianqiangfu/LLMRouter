# ComfyUI 可视化界面

LLMRouter 提供了强大的 **可视化界面**，通过 [ComfyUI](https://github.com/Comfy-Org/ComfyUI) 将路由管道的交互方式彻底革新。您无需编辑 YAML 文件或运行终端脚本，只需拖拽、连接节点即可构建完整的工作流。

## 功能特性

### 可视化配置
- 忘掉复杂的 YAML 配置文件和终端命令
- 直接在画布上调整参数（如样本大小、模型候选等）
- 通过复选框选择数据集和 LLM 模型

### 端到端自动化
- 无缝连接节点构建完整管道：数据生成 → 路由器训练 → 评估
- 自动执行数据生成、API 调用评估、嵌入提取等步骤

### 实时监控
- 跟踪查询生成、嵌入提取和模型训练的状态
- 即时查看可视化反馈和结果

### 模块化设计
- 通过拖拽、放置和连接节点来自定义管道
- 支持数据集选择、LLM 选择和路由器组合

## 安装与设置

### 前置条件
您必须先安装 [ComfyUI](https://github.com/Comfy-Org/ComfyUI)。

### 安装步骤

要安装 LLMRouter 自定义节点，需要创建两个符号链接（软链接）。

#### 1. 链接自定义节点
这将允许 ComfyUI 在 ComfyUI 的 "Nodes" 类别中加载 LLMRouter Python 后端逻辑。

```bash
ln -s /path/to/LLMRouter/ComfyUI /path/to/ComfyUI/custom_nodes/LLMRouter
```

#### 2. 链接工作流示例（可选）
这将允许您在 ComfyUI 的 "Workflows" 类别中查看预配置的工作流。

```bash
ln -s /path/to/LLMRouter/ComfyUI/workflows/llm_router_example.json /path/to/ComfyUI/user/default/workflows/llm_router_example.json
```

#### 3. 运行应用程序

要启动带有 LLMRouter 节点的 ComfyUI 服务器：

```bash
python /path/to/ComfyUI/main.py
```

#### 4. 远程访问与端口转发

如果您在远程服务器（例如计算集群）上运行 ComfyUI 并希望本地访问界面，可以使用 SSH 隧道。建立隧道后，在 `http://127.0.0.1:8188` 访问界面。

## 使用指南

### 查找节点

要使用这些节点：

1. 打开 ComfyUI 网页界面
2. 使用 **Node Library** 侧边栏或 **右键点击** 画布
3. 导航到 **`LLMRouter`** 类别
4. 您将找到按功能组织的节点：
   - **Data**（数据）：`Select Datasets`、`Select LLMs`、`Generate Data`
   - **Single-Round**（单轮）：`KNN Router`、`SVM Router`、`MLP Router` 等
   - **Multi-Round / Agentic**（多轮/代理）：用于复杂任务的专业路由器
   - **Personalized**（个性化）：`GMT Router (Personalized)`
   - **Multi-Round**（多轮）：`Router-R1`

### 节点说明

#### 数据管道节点

**1. DatasetSelector（选择数据集）**
- 功能：从 13 个基准数据集中选择数据集用于路由
- 输出：
  - `selected_datasets`：选择的数据集名称（逗号分隔）
  - `charades_ego_path`：Charades-Ego 数据集路径（如果选择了该数据集）
- 支持的数据集：
  - Natural QA、Trivia QA、MMLU、GPQA
  - MBPP、HumanEval
  - GSM8K、Commonsense QA、MATH
  - Openbook QA、ARC-Challenge、Geometry3K、MathVista
  - Charades-Ego（Activity/Object/Verb）

**2. LLMSelector（选择 LLM）**
- 功能：从 LLM 候选列表中选择要使用的模型
- 参数：
  - `llm_config_path`：LLM 配置文件路径（默认使用 `default_llm.json`）
  - 模型选择复选框：qwen2.5-7b-instruct、llama-3.1-8b-instruct 等
- 输出：
  - `llms`：过滤后的 LLM 配置文件路径

**3. GenerateData（生成数据）**
- 功能：统一的数据生成节点，生成查询数据、运行 API 评估管道和生成 LLM 嵌入
- 输入：
  - `selected_datasets`：选择的数据集列表
  - `charades_ego_path`：Charades-Ego 数据集路径
  - `llms`：LLM 配置文件路径
  - `sample_size`：每个数据集的样本大小（默认：10）
  - `workers`：API 调用的并发工作线程数（默认：10）
  - `output_dir`：输出目录路径
- 输出：
  - `data_dir`：包含所有生成文件的目录路径

#### 单轮路由器节点

**SmallestLLMNode（最小 LLM 基线）**
- 总是路由到最小的模型
- 支持调整性能、成本和 LLM 评判的权重

**LargestLLMNode（最大 LLM 基线）**
- 总是路由到最大的模型
- 支持调整性能、成本和 LLM 评判的权重

**KNNRouterNode（KNN 路由器）**
- 基于 K-近邻的路由策略
- 可调参数：邻居数、权重、算法、叶子大小、距离度量等

**SVMRouterNode（SVM 路由器）**
- 基于支持向量机的路由策略
- 可调参数：核函数、C 值、gamma、概率输出等

**MLPRouterNode（MLP 路由器）**
- 基于多层感知机的路由策略
- 可调参数：隐藏层大小、激活函数、学习率、训练轮数等

**MFRouterNode（矩阵分解路由器）**
- 基于矩阵分解的路由策略
- 可调参数：潜在维度、文本维度、学习率、训练轮数等

**EloRouterNode（Elo 路由器）**
- 基于 Elo 评分的路由策略
- 使用模型历史性能进行智能路由

**DCRouterNode（双对比路由器）**
- 基于双对比学习的路由策略
- 可调参数：backbone 模型、隐藏状态维度、相似度函数、训练步数等

**AutomixRouterNode（AutoMix 路由器）**
- 自动模型混合策略
- 支持多种路由方法：POMDP、Threshold、SelfConsistency

**HybridLLMNode（混合 LLM 路由器）**
- 混合 LLM 路由策略
- 支持确定性、概率性和转换分数路由模式

**GraphRouterNode（图神经网络路由器）**
- 基于图神经网络的路由策略
- 可调参数：隐藏维度、学习率、权重衰减、训练轮数等

**CausalLMRouterNode（因果语言模型路由器）**
- 基于因果语言模型的路由器
- 支持 LoRA 微调、混合精度训练等

#### 多轮路由器节点

**RouterR1Node**
- 预训练的 Router-R1 模型，用于多轮对话
- 支持多种模型变体：Qwen2.5-3B、Llama-3.2-3B 等

#### 个性化路由器节点

**GMTRouterNode（GMT 个性化路由器）**
- 基于图神经网络的个性化路由器
- 学习用户偏好和历史交互模式

#### 代理路由器节点

**KNNMultiRoundRouterNode（KNN 多轮代理路由器）**
- 基于代理的 KNN 路由器，用于复杂任务
- 支持多轮推理和任务分解

**LLMMultiRoundRouterNode（LLM 多轮代理路由器）**
- 基于代理的 LLM 路由器，用于复杂任务
- 使用 LLM 进行动态路由决策

### 加载示例

要使用即用型示例：

1. 点击 **`Workflows`** 标签
2. 选择 **`llm_router_example.json`**
3. 这将加载一个完整的管道

## 工作流示例

### 示例工作流结构

提供的示例工作流 `llm_router_example.json` 包含以下组件：

```
数据准备层：
├── DatasetSelector（选择数据集）
├── LLMSelector（选择 LLM）
└── GenerateData（生成数据）

路由器评估层（并行）：
├── SmallestLLMNode → PreviewAny
├── LargestLLMNode → PreviewAny
├── KNNRouterNode → PreviewAny
├── SVMRouterNode → PreviewAny
├── MLPRouterNode → PreviewAny
├── MFRouterNode → PreviewAny
├── EloRouterNode → PreviewAny
├── DCRouterNode → PreviewAny
├── AutomixRouterNode → PreviewAny
├── HybridLLMNode → PreviewAny
├── GraphRouterNode → PreviewAny
├── CausalLMRouterNode → PreviewAny
├── RouterR1Node → PreviewAny
├── GMTRouterNode → PreviewAny
├── KNNMultiRoundRouterNode → PreviewAny
└── LLMMultiRoundRouterNode → PreviewAny
```

### 创建自定义工作流

#### 1. 数据生成工作流

1. 添加 `DatasetSelector` 节点
   - 勾选您要使用的数据集
   - 如果选择 Charades-Ego，提供数据集路径

2. 添加 `LLMSelector` 节点
   - 配置 LLM 配置文件路径
   - 勾选要使用的模型

3. 添加 `GenerateData` 节点
   - 将 `DatasetSelector` 的 `selected_datasets` 输出连接到 `GenerateData` 的 `selected_datasets` 输入
   - 将 `DatasetSelector` 的 `charades_ego_path` 输出连接到 `GenerateData` 的 `charades_ego_path` 输入
   - 将 `LLMSelector` 的 `llms` 输出连接到 `GenerateData` 的 `llms` 输入
   - 设置 `sample_size`（例如：10-100）
   - 设置 `workers`（例如：10）
   - 设置 `output_dir`（例如：`data/my_data`）

4. 执行工作流
   - 点击 "Queue Prompt" 执行
   - 系统将自动生成查询数据、调用 API 评估、生成嵌入和路由数据

#### 2. 路由器训练和评估工作流

1. 从数据生成工作流获取 `data_dir` 输出

2. 添加路由器节点（例如：`KNNRouterNode`）
   - 将 `GenerateData` 的 `data_dir` 输出连接到路由器节点的 `data_dir` 输入
   - 调整路由器超参数（如邻居数、核函数等）

3. 添加 `PreviewAny` 节点
   - 将路由器节点的 `results` 输出连接到 `PreviewAny` 的 `source` 输入
   - 这将显示训练和评估结果

4. 执行工作流
   - 点击 "Queue Prompt" 执行
   - 系统将训练路由器并在测试集上评估

### 工作流最佳实践

1. **数据生成缓存**：`GenerateData` 节点会检查配置是否更改，如果配置未更改且数据已存在，则跳过重新生成

2. **参数调整**：在训练路由器时，从默认超参数开始，然后逐步调整以获得更好的性能

3. **并行评估**：可以同时连接多个路由器节点到同一个 `data_dir`，以比较不同路由器的性能

4. **结果查看**：使用 `PreviewAny` 节点查看路由器的评估结果，包括：
   - 总查询数
   - 成功路由数
   - 平均性能得分
   - 路由分布（每个模型处理的查询数）

## 支持的路由器

### 单轮路由器（11 个）

| 路由器 | 说明 | 可训练 |
|--------|------|:------:|
| Smallest LLM | 总是路由到最小模型 | 否 |
| Largest LLM | 总是路由到最大模型 | 否 |
| KNN Router | K-近邻路由 | 是 |
| SVM Router | 支持向量机路由 | 是 |
| MLP Router | 多层感知机路由 | 是 |
| MF Router | 矩阵分解路由 | 是 |
| Elo Router | Elo 评分路由 | 是 |
| RouterDC | 双对比学习路由 | 是 |
| AutoMix Router | 自动模型混合 | 是 |
| Hybrid LLM Router | 混合 LLM 路由 | 是 |
| Graph Router | 图神经网络路由 | 是 |
| CausalLM Router | 因果语言模型路由 | 是 |

### 多轮路由器（1 个）

| 路由器 | 说明 | 可训练 |
|--------|------|:------:|
| Router-R1 | 预训练多轮路由模型 | 否 |

### 个性化路由器（1 个）

| 路由器 | 说明 | 可训练 |
|--------|------|:------:|
| GMT Router | 图神经网络个性化路由 | 是 |

### 代理路由器（2 个）

| 路由器 | 说明 | 可训练 |
|--------|------|:------:|
| KNN Multi-Round Router | KNN 多轮代理路由 | 是 |
| LLM Multi-Round Router | LLM 多轮代理路由 | 否 |

## API 密钥配置

在使用 ComfyUI 界面之前，需要设置 API 密钥环境变量以进行 LLM API 调用：

```bash
# 服务提供商字典格式（推荐）
export API_KEYS='{"NVIDIA": "nvidia-key-1,nvidia-key-2", "OpenAI": ["openai-key-1", "openai-key-2"], "Anthropic": "anthropic-key-1"}'

# 或者使用数组格式
export API_KEYS='["your-key-1", "your-key-2", "your-key-3"]'

# 或逗号分隔格式
export API_KEYS='key1,key2,key3'

# 或单个密钥
export API_KEYS='your-api-key'
```

## 故障排除

### 节点未显示在节点库中

1. 确认已正确创建符号链接
2. 重启 ComfyUI 服务器
3. 检查 Python 环境是否安装了 LLMRouter

### 数据生成失败

1. 检查 API 密钥是否正确设置
2. 确认 LLM 配置文件路径正确
3. 查看 ComfyUI 控制台输出的错误信息

### 路由器训练失败

1. 确认数据目录包含所有必需的文件
2. 检查是否有足够的内存和磁盘空间
3. 尝试减小 `batch_size` 或训练轮数

## 相关文档

- [LLMRouter 主 README](../README.md)
- [数据生成管道](../llmrouter/data/README.md)
- [训练路由器](../llmrouter/cli/README.md)
- [ComfyUI 官方文档](https://docs.comfyanonymous.github.io/ComfyUI/)

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](../LICENSE) 文件。
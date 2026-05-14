# LLMRouter Jupyter Notebooks

本目录包含所有 LLMRouter 方法的训练和推理 Jupyter Notebook。

## 目录作用

`notebooks/` 目录提供了完整的教学和实践环境，帮助用户：

- 理解不同路由器的工作原理
- 学习如何训练和部署各种路由器
- 快速评估和比较不同路由器的性能
- 在实际项目中应用 LLMRouter

## 目录结构

```
notebooks/
├── data_preparation/          # 共享数据准备
│   └── 01_data_preparation.ipynb
├── knnrouter/                 # K-近邻路由器
│   ├── 01_knnrouter_training.ipynb
│   └── 02_knnrouter_inference.ipynb
├── svmrouter/                 # 支持向量机路由器
│   ├── 01_svmrouter_training.ipynb
│   └── 02_svmrouter_inference.ipynb
├── mlprouter/                 # 多层感知机路由器
│   ├── 01_mlprouter_training.ipynb
│   └── 02_mlprouter_inference.ipynb
├── mfrouter/                  # 矩阵分解路由器
│   ├── 01_mfrouter_training.ipynb
│   └── 02_mfrouter_inference.ipynb
├── dcrouter/                  # 双对比路由器
│   ├── 01_dcrouter_training.ipynb
│   └── 02_dcrouter_inference.ipynb
├── graphrouter/               # 图神经网络路由器
│   ├── 01_graphrouter_training.ipynb
│   └── 02_graphrouter_inference.ipynb
├── causallm_router/           # 因果语言模型路由器
│   ├── 01_causallm_router_training.ipynb
│   └── 02_causallm_router_inference.ipynb
├── automix_router/            # 自动 LLM 混合路由器
│   ├── 01_automix_router_training.ipynb
│   └── 02_automix_router_inference.ipynb
├── hybrid_llm_router/         # 混合 LLM 路由器
│   ├── 01_hybrid_llm_router_training.ipynb
│   └── 02_hybrid_llm_router_inference.ipynb
├── gmtrouter/                 # 基于图的多轮路由器
│   ├── 01_gmtrouter_training.ipynb
│   └── 02_gmtrouter_inference.ipynb
├── elorouter/                 # Elo 评级路由器（仅推理）
│   └── 01_elorouter_inference.ipynb
├── smallest_llm/              # SmallestLLM 基线（仅推理）
│   └── 01_smallest_llm_inference.ipynb
├── largest_llm/               # LargestLLM 基线（仅推理）
│   └── 01_largest_llm_inference.ipynb
├── router_r1/                 # RouterR1 智能体路由器（仅推理）
│   └── 01_router_r1_inference.ipynb
├── knnmultiroundrouter/       # KNN 多轮路由器
│   ├── 01_knnmultiroundrouter_training.ipynb
│   └── 02_knnmultiroundrouter_inference.ipynb
└── llmmultiroundrouter/       # LLM 多轮路由器（仅推理）
    └── 01_llmmultiroundrouter_inference.ipynb
```

## 子目录和路由器说明

### 数据准备
- **data_preparation/**: 共享的数据准备流程，用于下载基准数据集、生成查询数据、创建查询嵌入和（可选）调用 LLM API 获取路由数据。

### 传统机器学习路由器
- **knnrouter/**: K-近邻路由器，基于查询相似度进行路由选择，简单且可解释性强。
- **svmrouter/**: 支持向量机路由器，适用于高维数据的分类任务。
- **mlprouter/**: 多层感知机路由器，通过神经网络学习复杂的决策边界。
- **mfrouter/**: 矩阵分解路由器，基于协同过滤的思想进行路由。

### 深度学习路由器
- **dcrouter/**: 双对比路由器，使用 Transformer 架构实现高精度路由。
- **graphrouter/**: 图神经网络路由器，利用图结构捕捉查询和模型之间的关系模式。
- **causallm_router/**: 因果语言模型路由器，通过微调 LLM 实现复杂查询的路由。
- **automix_router/**: 自动 LLM 混合路由器，使用 POMDP 模型实现成本高效的路由决策。
- **hybrid_llm_router/**: 混合 LLM 路由器，结合多种方法实现二分类路由。
- **gmtrouter/**: 基于图的多轮路由器，使用异构图神经网络实现个性化多轮对话路由。

### 基线和特殊路由器
- **elorouter/**: 基于 Elo 评级系统的路由器，无需训练，适合简单场景。
- **smallest_llm/**: 最小 LLM 基线，总是路由到最小的模型，作为成本效率基准。
- **largest_llm/**: 最大 LLM 基线，总是路由到最大的模型，作为性能上限基准。
- **router_r1/**: RouterR1 智能体路由器，具备复杂推理能力。

### 多轮路由器
- **knnmultiroundrouter/**: KNN 多轮路由器，处理多步骤查询场景。
- **llmmultiroundrouter/**: LLM 多轮路由器，零样本处理多轮对话。

## Jupyter Notebook 用途

Notebook 文件按照以下编号约定：

- `01_*_training.ipynb`: 训练笔记本，包含模型训练、参数调优和模型保存
- `02_*_inference.ipynb`: 推理笔记本，用于模型加载、预测和评估

## 环境要求

### 基础依赖
- Python >= 3.8
- Jupyter Notebook 或 JupyterLab
- llmrouter-lib
- transformers
- torch

### GPU 要求
- **推荐使用 GPU**: CausalLMRouter、DCRouter、GraphRouter、GMTRouter
- **可选使用 GPU**: LLMMultiRoundRouter
- **无需 GPU**: KNNRouter、SVMRouter、MLPRouter、MFRouter、EloRouter、SmallestLLM、LargestLLM

### 安装依赖
```bash
pip install llmrouter-lib transformers torch jupyter
```

## 使用指南

### 快速开始

#### 1. 数据准备

在训练任何路由器之前，先运行数据准备笔记本：

```bash
cd notebooks/data_preparation
jupyter notebook 01_data_preparation.ipynb
```

这将完成以下操作：
- 下载基准数据集
- 生成查询数据（训练集/测试集）
- 创建查询嵌入
- （可选）调用 LLM API 获取路由数据

#### 2. 训练路由器

每个路由器都有对应的训练笔记本。例如，训练 KNNRouter：

```bash
cd notebooks/knnrouter
jupyter notebook 01_knnrouter_training.ipynb
```

#### 3. 推理/测试

训练完成后，使用推理笔记本：

```bash
cd notebooks/knnrouter
jupyter notebook 02_knnrouter_inference.ipynb
```

### 使用 Google Colab

所有笔记本都兼容 Google Colab。使用方法：

1. 将笔记本上传到 Colab
2. 安装依赖：
   ```python
   !pip install llmrouter-lib transformers torch
   ```
3. 克隆仓库（用于获取数据和配置）：
   ```python
   !git clone https://github.com/ulab-uiuc/LLMRouter.git
   %cd LLMRouter
   ```
4. 运行 notebook 单元格

### 配置文件

训练配置位于：
- `configs/model_config_train/` - 训练配置
- `configs/model_config_test/` - 推理配置

### API 密钥设置

如需完整推理（调用 LLM API），请设置环境变量：

```python
import os
os.environ['OPENAI_API_KEY'] = 'your-key'
os.environ['ANTHROPIC_API_KEY'] = 'your-key'
# 或设置多个密钥：
os.environ['API_KEYS'] = '["key1", "key2"]'
```

### 路由器对比

| 路由器 | 类型 | 需要训练 | 需要 GPU | 最适合场景 |
|--------|------|----------|----------|------------|
| KNNRouter | 分类 | 是 | 否 | 简单、可解释的路由 |
| SVMRouter | 分类 | 是 | 否 | 高维数据 |
| MLPRouter | 神经网络 | 是 | 否 | 复杂决策边界 |
| MFRouter | 矩阵分解 | 是 | 否 | 协同过滤 |
| DCRouter | Transformer | 是 | 推荐 | 高精度路由 |
| GraphRouter | GNN | 是 | 推荐 | 关系模式 |
| CausalLMRouter | LLM 微调 | 是 | 必须 | 复杂查询 |
| AutomixRouter | POMDP | 是 | 否 | 成本高效路由 |
| HybridLLMRouter | MLP | 是 | 否 | 二分类路由 |
| GMTRouter | 异构图网络 | 是 | 推荐 | 个性化多轮对话 |
| EloRouter | 基于评级 | 否 | 否 | 基线/简单场景 |
| SmallestLLM | 基线 | 否 | 否 | 成本效率基准 |
| LargestLLM | 基线 | 否 | 否 | 性能上限 |
| RouterR1 | 智能体 | 否 | 必须 | 复杂推理 |
| KNNMultiRoundRouter | 多轮 KNN | 是 | 否 | 多步骤查询 |
| LLMMultiRoundRouter | 多轮 LLM | 否 | 可选 | 零样本多轮 |

## 常见问题

### 内存溢出（OOM）
- 在配置中减小 `batch_size`
- 对较小的模型使用 CPU 代替 GPU
- 对大模型启用梯度检查点

### 缺少数据
- 先运行 `01_data_preparation.ipynb`
- 检查配置文件中的数据路径
- 验证所有必需文件是否存在

### 导入错误
- 安装所有依赖：`pip install llmrouter-lib`
- 确保在正确的目录中
- 检查 Python 路径是否包含项目根目录

## 自定义路由器

如需创建自定义路由器，请参考：
- `custom_router/01_creating_custom_routers.ipynb` - 自定义路由器创建教程

此教程将指导您：
- 了解路由器接口
- 实现自定义路由逻辑
- 训练和评估自定义路由器
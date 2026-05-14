# LLMRouter 数据生成流程图

## 流程说明

数据生成流程将原始基准数据集转换为路由器训练所需的格式化数据。

```mermaid
graph TB
    subgraph Start["数据生成开始"]
        A[Start<br/>加载配置文件] --> B[选择数据集]
    end

    subgraph DataLoad["数据加载 (从 16 个基准数据集)"]
        B --> C[NaturalQA]
        B --> D[TriviaQA]
        B --> E[MMLU]
        B --> F[GPQA]
        B --> G[MBPP]
        B --> H[HumanEval]
        B --> I[GSM8K]
        B --> J[CommonsenseQA]
        B --> K[MATH]
        B --> L[OpenbookQA]
        B --> M[ARC-Challenge]
        B --> N[Geometry3K<br/>多模态]
        B --> O[MathVista<br/>多模态]
        B --> P[Charades-Ego Activity<br/>多模态视频]
        B --> Q[Charades-Ego Object<br/>多模态视频]
        B --> R[Charades-Ego Verb<br/>多模态视频]
    end

    subgraph QueryExtraction["查询数据提取"]
        C --> S1[提取 question/<br/>golden_answers]
        D --> S2[提取 question/<br/>answer]
        E --> S3[提取 question/<br/>choices/<br/>answer]
        F --> S4[提取 Question/<br/>Correct Answer]
        G --> S5[提取 text/<br/>test_list]
        H --> S6[提取 prompt/<br/>test]
        I --> S7[提取 question/<br/>answer]
        J --> S8[提取 question/<br/>choices/<br/>answerKey]
        K --> S9[提取 problem/<br/>solution]
        L --> S10[提取 problem/<br/>answer<br/>VLM 描述图像]
        M --> S11[提取 question/<br/>answer<br/>VLM 描述图像]
        P --> S12[提取视频/<br/>标签]
        Q --> S13[提取视频/<br/>标签]
        R --> S14[提取视频/<br/>标签]

        S1 --> T1[构建查询数据<br/>task_name, query,<br/>ground_truth, metric,<br/>choices, task_id]
        S2 --> T1
        S3 --> T1
        S4 --> T1
        S5 --> T1
        S6 --> T1
        S7 --> T1
        S8 --> T1
        S9 --> T1
        S10 --> T1
        S11 --> T1
        S12 --> T1
        S13 --> T1
        S14 --> T1
    end

    subgraph DataSplit["数据集划分"]
        T1 --> U1[随机打乱数据]
        U1 --> U2[按比例划分<br/>训练集 80% / 测试集 20%]
        U2 --> U3[保存为 JSONL 格式<br/>query_data_train.jsonl<br/>query_data_test.jsonl]
    end

    subgraph LLMEmbedding["LLM 嵌入生成"]
        U3 --> V1[加载 LLM 元数据<br/>default_llm.json]
        V1 --> V2[为每个 LLM 生成嵌入<br/>基于 feature 字段<br/>使用 Longformer 模型]
        V2 --> V3[保存 LLM 嵌入<br/>default_llm_embeddings.json]
    end

    subgraph APICalling["API 调用与评估"]
        V3 --> W1[加载查询数据<br/>训练集 & 测试集]
        W1 --> W2[创建查询-模型组合<br/>N 个查询 × M 个模型]
        W2 --> W3[并行调用 LLM API<br/>使用 LiteLLM Router<br/>ThreadPoolExecutor]
        W3 --> W4[格式化查询提示词<br/>根据任务类型]
        W4 --> W5[获取模型响应<br/>response, tokens,<br/>response_time]
    end

    subgraph Evaluation["性能评估"]
        W5 --> X1[根据指标类型评估<br/>em, em_mc, f1_score,<br/>GSM8K, MATH, code_eval,<br/>cem, bert_score]
        X1 --> X2[计算 performance 分数<br/>response vs ground_truth]
        X2 --> X3[汇总统计<br/>按任务类别<br/>按模型]
    end

    subgraph RoutingData["路由数据生成"]
        X3 --> Y1[生成查询嵌入<br/>使用嵌入模型]
        Y1 --> Y2[合并所有数据<br/>查询嵌入 + LLM 嵌入<br/>+ 性能分数]
        Y2 --> Y3[生成路由标签<br/>选择最佳 LLM]
        Y3 --> Y4[保存路由数据<br/>routing_data_train.jsonl<br/>routing_data_test.jsonl]
        Y2 --> Y5[保存统一嵌入<br/>query_embeddings.pt]
    end

    subgraph End["数据生成完成"]
        Y4 --> Z[End<br/>数据生成完成]
        Y5 --> Z
    end

    %% 样式定义
    classDef startEnd fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef dataLoad fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef process fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef evaluation fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef output fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    class A,Z startEnd
    class C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R dataLoad
    class S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12,S13,S14,T1,U1,U2,U3,V1,V2,V3,W1,W2,W3,W4,W5,Y1,Y2,Y3 process
    class X1,X2,X3 evaluation
    class Y4,Y5 output
```

## 关键步骤说明

### 1. 数据加载
从 16 个不同的基准数据集加载原始数据：
- **文本任务**: NaturalQA, TriviaQA, MMLU, GPQA, CommonsenseQA, OpenbookQA, ARC-Challenge
- **数学任务**: GSM8K, MATH
- **代码任务**: MBPP, HumanEval
- **多模态任务**: Geometry3K, MathVista, Charades-Ego (Activity/Object/Verb)

### 2. 查询数据提取
统一数据格式，提取以下字段：
- `task_name`: 任务类型
- `query`: 查询文本（对于多模态任务，包含 VLM 生成的图像描述）
- `ground_truth`: 标准答案
- `metric`: 评估指标类型
- `choices`: 选择题选项（如适用）
- `task_id`: 任务唯一标识

### 3. 数据集划分
随机打乱数据，按 80/20 比例划分为训练集和测试集。

### 4. LLM 嵌入生成
为每个 LLM 候选生成嵌入向量：
- 基于 `feature` 字段（LLM 特征描述）
- 使用 Longformer 模型生成嵌入
- 保存为 JSON 格式

### 5. API 调用与评估
对每个查询调用所有候选 LLM：
- 使用 LiteLLM Router 管理多模型调用
- 支持并行处理（ThreadPoolExecutor）
- 根据任务类型格式化提示词
- 记录响应、token 数、响应时间

### 6. 性能评估
根据不同的评估指标计算性能分数：
- **EM/EM_MC**: 精确匹配（普通/多选题）
- **F1 Score**: F1 分数
- **GSM8K**: 数学题评估
- **MATH**: 数学题 LaTeX 格式评估
- **Code Eval**: 代码执行评估（HumanEval/MBPP）
- **CEM**: 字符级精确匹配
- **BERT Score**: 语义相似度

### 7. 路由数据生成
生成最终的路由训练数据：
- 生成查询嵌入向量
- 合并所有数据（查询嵌入、LLM 嵌入、性能分数）
- 选择性能最佳的 LLM 作为路由标签
- 保存为 JSONL 格式

## 输出文件

- `query_data_train.jsonl`: 训练集查询数据
- `query_data_test.jsonl`: 测试集查询数据
- `default_llm_embeddings.json`: LLM 嵌入数据
- `query_embeddings.pt`: 查询嵌入向量
- `routing_data_train.jsonl`: 训练集路由数据
- `routing_data_test.jsonl`: 测试集路由数据
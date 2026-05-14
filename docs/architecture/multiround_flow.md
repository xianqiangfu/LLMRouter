# MultiRound Router 多轮路由流程图

## 流程概述

MultiRound Router 专为复杂的多轮对话场景设计，通过查询分解 → 子查询路由 → 独立执行 → 结果聚合的流水线处理复杂查询。每个子查询独立路由到最适合的模型。

## 详细流程图

```mermaid
flowchart TD
    Start([开始]) --> Input[接收查询输入]
    Input --> CheckMode{检查模式}
    CheckMode -->|聊天模式| StrMode[字符串输入]
    CheckMode -->|评估模式| DictMode[字典输入]

    StrMode --> Decompose[分解查询为子查询]
    DictMode --> ParseDict[解析任务信息]
    ParseDict --> CheckTask{有任务名?}
    CheckTask -->|是| Format[应用任务格式化]
    CheckTask -->|否| Decompose
    Format --> Decompose

    Decompose --> DecompPrompt[构建分解提示]
    DecompPrompt --> DecompExec{分解执行方式}
    DecompExec -->|本地LLM| LocalDecomp[使用本地LLM分解]
    DecompExec -->|API| APIDecomp[使用API分解]
    LocalDecomp --> ParseSubQ[解析子查询列表]
    APIDecomp --> ParseSubQ

    ParseSubQ --> InitSub[初始化子查询列表]
    InitSub --> LoopStart{子查询循环}

    LoopStart -->|有未处理子查询| RouteSub[路由单个子查询]
    RouteSub --> LoadKNN[加载KNN模型]
    LoadKNN --> SubEmbed[生成子查询嵌入]
    SubEmbed --> SubLongformer[使用Longformer生成向量]
    SubLongformer --> SubPredict[KNN预测最佳模型]
    SubPredict --> SubModel[获得模型名称]

    SubModel --> ExecSub[执行子查询]
    ExecSub --> ExecPrompt[构建执行提示]
    ExecPrompt --> GetSubAPI[获取API端点]
    GetSubAPI --> CallSubAPI[调用API]
    CallSubAPI --> ParseResp[解析响应]
    ParseResp --> Store[存储结果到列表]

    Store --> LoopStart
    LoopStart -->|所有子查询完成| Aggregate[聚合响应]

    Aggregate --> CheckTaskType{任务类型?}
    CheckTaskType -->|多选题| MCAgg[多选题聚合逻辑]
    CheckTaskType -->|其他| StdAgg[标准聚合逻辑]

    MCAgg --> MCAggPrompt[构建多选题聚合提示]
    StdAgg --> StdAggPrompt[构建标准聚合提示]

    MCAggPrompt --> AggExec{聚合执行方式}
    StdAggPrompt --> AggExec

    AggExec -->|本地LLM| LocalAgg[使用本地LLM聚合]
    AggExec -->|API| APIAgg[使用API聚合]

    LocalAgg --> FinalAnswer[获得最终答案]
    APIAgg --> FinalAnswer

    FinalAnswer --> CheckFinalMode{最终模式?}
    CheckFinalMode -->|聊天模式| StrOutput([返回字符串])
    CheckFinalMode -->|评估模式| CalcTokens[计算总token数]

    CalcTokens --> CheckGT{有基准答案?}
    CheckGT -->|是| CalcPerf[计算性能指标]
    CheckGT -->|否| BuildDict
    CalcPerf --> BuildDict[构建完整结果字典]

    BuildDict --> DictOutput([返回字典])

    style Start fill:#e1f5e1
    style StrOutput fill:#e1f5e1
    style DictOutput fill:#e1f5e1
    style Decompose fill:#fff4e1
    style RouteSub fill:#ffe1f5
    style Aggregate fill:#e1f5ff
    style LoopStart fill:#ffffe1
```

## 子流程：查询分解

```mermaid
flowchart TD
    Input([原始查询]) --> BuildPrompt[构建分解提示]
    BuildPrompt --> CheckLocal{本地LLM可用?}
    CheckLocal -->|是| InitLLM[初始化本地LLM]
    CheckLocal -->|否| Single[返回单个查询]

    InitLLM --> ChatTmpl[应用聊天模板]
    ChatTmpl --> Sample[生成采样参数]
    Sample --> Generate[生成文本]
    Generate --> Strip[清理输出]

    Strip --> ParseLines[解析输出行]
    ParseLines --> Filter[过滤空行和短行]
    Filter --> CheckEmpty{有子查询?}
    CheckEmpty -->|否| UseOriginal[使用原始查询]
    CheckEmpty -->|是| SubQList([子查询列表])

    UseOriginal --> SubQList

    style Input fill:#e1f5e1
    style SubQList fill:#e1f5e1
    style Generate fill:#ffe1f5
```

## 子流程：子查询路由与执行

```mermaid
flowchart TD
    Input([子查询]) --> Embed[生成嵌入]
    Embed --> KNN[KNN预测模型]
    KNN --> ModelName[获得模型名称]

    ModelName --> Lookup[查找API配置]
    Lookup --> CheckDirect{直接匹配?}
    CheckDirect -->|是| DirectGet[直接获取端点]
    CheckDirect -->|否| Search[搜索配置]

    DirectGet --> BuildReq[构建请求]
    Search --> BuildReq

    BuildReq --> CallAPI[调用API]
    CallAPI --> Parse[解析响应]
    Parse --> Result([执行结果])

    style Input fill:#e1f5e1
    style Result fill:#e1f5e1
    style Embed fill:#fff4e1
    style KNN fill:#fff4e1
    style CallAPI fill:#ffe1f5
```

## 子流程：响应聚合

```mermaid
flowchart TD
    Input([原始查询<br/>子查询列表<br/>响应列表]) --> FormatInfo[格式化辅助信息]

    FormatInfo --> Loop{遍历子查询}
    Loop -->|有未处理| AddInfo[添加子查询和响应]
    AddInfo --> Loop

    Loop -->|全部完成| CheckTask{任务类型}

    CheckTask -->|多选题| MCPrompt[多选题提示]
    CheckTask -->|其他| StdPrompt[标准提示]

    MCPrompt --> CheckLocal{本地LLM可用?}
    StdPrompt --> CheckLocal

    CheckLocal -->|是| LocalExec[本地LLM执行]
    CheckLocal -->|否| APIExec[API执行]

    LocalExec --> GenAnswer[生成最终答案]
    APIExec --> GenAnswer

    GenAnswer --> Output([最终答案])

    style Input fill:#e1f5e1
    style Output fill:#e1f5e1
    style MCPrompt fill:#ffe1f5
    style StdPrompt fill:#ffe1f5
    style GenAnswer fill:#e1f5ff
```

## 数据流说明

1. **输入阶段**:
   - 支持字符串（聊天模式）和字典（评估模式）两种输入
   - 可选任务格式化（如 MMLU、GSM8K 等）

2. **分解阶段**:
   - 使用本地 LLM 或 API 将复杂查询分解为多个子查询
   - 如果分解失败，回退到原始查询

3. **路由阶段**（对每个子查询）:
   - 使用 KNN 算法独立路由每个子查询
   - 每个子查询可能被路由到不同的模型

4. **执行阶段**（对每个子查询）:
   - 使用特定任务的 Agent Prompt
   - 调用路由模型的 API 获取响应

5. **聚合阶段**:
   - 根据任务类型选择聚合策略
   - 多选题任务使用特定的格式和规则
   - 其他任务使用标准的 COT（Chain of Thought）聚合

6. **输出阶段**:
   - 聊天模式：仅返回最终答案字符串
   - 评估模式：返回包含 token 统计和性能指标的完整字典

## 支持的多选题任务

以下任务使用多选题聚合逻辑：
- `commonsense_qa`
- `openbook_qa`
- `arc_challenge`
- `mmlu`
- `gpqa`

## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| base_model | 用于分解和聚合的基座模型 | Qwen/Qwen2.5-3B-Instruct |
| use_local_llm | 是否使用本地LLM | false |
| knn_model_path | KNN模型路径 | - |
| n_neighbors | K近邻数量 | 5 |
| metric | 距离度量 | cosine |

## 依赖关系

- `Longformer`: 用于生成查询嵌入
- `KNeighborsClassifier`: KNN 分类器
- `vllm`: 本地 LLM 推理（可选）
- `llm_data.json`: 模型配置数据
- `call_api`: API 调用工具函数
- `load_prompt_template`: 提示模板加载器

## 提示模板

路由器使用三种主要提示模板：
1. **agent_decomp**: 查询分解提示
2. **agent_prompt**: 子查询执行提示
3. **agent_decomp_cot**: 标准 COT 聚合提示

多选题聚合使用内置的特定提示格式。
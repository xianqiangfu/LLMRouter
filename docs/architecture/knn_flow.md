# KNN Router 路由流程图

## 流程概述

KNN Router 使用 K-近邻（K-Nearest Neighbors）分类器根据查询嵌入选择最合适的语言模型。

## 详细流程图

```mermaid
flowchart TD
    Start([开始]) --> Input[接收查询输入]
    Input --> LoadConfig[加载配置文件]
    LoadConfig --> LoadKNN[加载预训练KNN模型]

    LoadKNN --> Embed[生成查询嵌入]
    Embed --> Longformer[使用Longformer模型生成向量表示]
    Longformer --> Predict[KNN预测]

    Predict --> Search[在训练数据中搜索K个近邻]
    Search --> Vote[近邻模型投票]
    Vote --> SelectModel[选择最佳模型]

    SelectModel --> CheckTask{是否有任务名?}
    CheckTask -->|是| Format[应用任务特定格式化]
    CheckTask -->|否| GetAPI
    Format --> GetAPI[获取API端点]

    GetAPI --> CallAPI[调用API执行查询]
    CallAPI --> Parse[解析响应]

    Parse --> CheckGT{是否有基准答案?}
    CheckGT -->|是| CalcPerf[计算性能指标]
    CheckGT -->|否| BuildResult
    CalcPerf --> BuildResult[构建结果字典]

    BuildResult --> Output([返回结果])

    style Start fill:#e1f5e1
    style Output fill:#e1f5e1
    style Predict fill:#fff4e1
    style Search fill:#fff4e1
    style Vote fill:#fff4e1
```

## 子流程：KNN 预测详情

```mermaid
flowchart TD
    Input([查询嵌入向量]) --> CalcDist[计算与所有训练样本的距离]
    CalcDist --> Sort[按距离排序]
    Sort --> TopK[选择K个最近邻]
    TopK --> GetLabels[获取近邻的模型标签]
    GetLabels --> CountVotes[统计各模型出现次数]
    CountVotes --> Majority[选择出现次数最多的模型]
    Majority --> Output([预测结果: 模型名称])

    style Input fill:#e1f5e1
    style Output fill:#e1f5e1
```

## 数据流说明

1. **输入**: 查询文本（query）
2. **嵌入生成**: 使用 Longformer 模型将文本转换为固定维度的向量
3. **KNN 搜索**: 在训练数据嵌入中查找最相似的 K 个样本
4. **投票决策**: 基于近邻样本的模型标签进行多数投票
5. **输出**: 路由的模型名称 + API 执行结果

## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| n_neighbors | K近邻数量 | 2 |
| metric | 距离度量方式 | cosine |
| algorithm | 搜索算法 | auto |

## 依赖关系

- `Longformer`: 用于生成查询嵌入
- `sklearn.neighbors.KNeighborsClassifier`: KNN 分类器
- `llm_data.json`: 模型配置数据
- `call_api`: API 调用工具函数
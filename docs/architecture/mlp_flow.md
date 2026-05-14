# MLP Router 路由流程图

## 流程概述

MLP Router 使用多层感知机（Multi-Layer Perceptron）神经网络根据查询嵌入选择最合适的语言模型。现在支持 PyTorch 实现以利用 GPU 加速。

## 详细流程图

```mermaid
flowchart TD
    Start([开始]) --> Input[接收查询输入]
    Input --> LoadConfig[加载配置文件]
    LoadConfig --> InitMLP[初始化MLP分类器]

    InitMLP --> CheckFormat{检查模型格式}
    CheckFormat -->|PyTorch| LoadPT[加载PyTorch模型状态]
    CheckFormat -->|sklearn| LoadSK[加载sklearn模型]
    LoadPT --> MoveGPU{可用GPU?}
    MoveGPU -->|是| ToGPU[移动到GPU]
    MoveGPU -->|否| SetEval
    ToGPU --> SetEval[设置为评估模式]

    LoadSK --> SetEval

    SetEval --> Embed[生成查询嵌入]
    Embed --> Longformer[使用Longformer模型生成向量表示]
    Longformer --> TensorConvert[转换为PyTorch张量]

    TensorConvert --> Forward[MLP前向传播]
    Forward --> Hidden[隐藏层计算]
    Hidden --> Activation[激活函数ReLU/Tanh]
    Activation --> Output[输出层计算]

    Output --> Predict[预测类别索引]
    Predict --> IndexToModel[索引转模型名称]

    IndexToModel --> CheckTask{是否有任务名?}
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
    style Forward fill:#e1f5ff
    style Hidden fill:#e1f5ff
    style Activation fill:#e1f5ff
    style Output fill:#e1f5ff
    style CheckFormat fill:#ffe1f5
    style LoadPT fill:#ffe1f5
    style LoadSK fill:#ffe1f5
```

## 子流程：MLP 网络结构

```mermaid
flowchart LR
    Input([输入嵌入<br/>维度: input_dim]) --> H1[隐藏层1<br/>Linear + Activation]
    H1 --> H2[隐藏层2<br/>Linear + Activation]
    H2 --> HN[...]
    HN --> Out[输出层<br/>Linear + Softmax]
    Out --> Predict([预测类别<br/>维度: num_classes])

    style Input fill:#e1f5e1
    style Predict fill:#e1f5e1
    style H1 fill:#fff4e1
    style H2 fill:#fff4e1
    style HN fill:#fff4e1
    style Out fill:#ffe1f5
```

## 子流程：模型推理

```mermaid
flowchart TD
    Input([查询嵌入向量]) --> Unsqueeze[添加批次维度]
    Unsqueeze --> Device{设备选择}
    Device -->|GPU| GPU[移动到GPU]
    Device -->|CPU| CPU[保持在CPU]
    GPU --> NoGrad[禁用梯度计算]
    CPU --> NoGrad
    NoGrad --> Forward[执行前向传播]
    Forward --> Logits[获取输出logits]
    Logits --> ArgMax[取最大值索引]
    ArgMax --> Lookup[查找对应的模型名称]
    Lookup --> Output([预测结果])

    style Input fill:#e1f5e1
    style Output fill:#e1f5e1
    style NoGrad fill:#ffe1f5
```

## 数据流说明

1. **输入**: 查询文本（query）
2. **嵌入生成**: 使用 Longformer 模型将文本转换为固定维度的向量
3. **张量转换**: 将 NumPy 数组转换为 PyTorch 张量
4. **MLP 推理**: 通过多层神经网络计算类别概率
5. **输出解析**: 将类别索引映射回模型名称
6. **最终输出**: 路由的模型名称 + API 执行结果

## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| hidden_layer_sizes | 隐藏层尺寸列表 | [128, 64] |
| activation | 激活函数 | relu |
| lr | 学习率 | 0.001 |
| epochs | 训练轮数 | 100 |
| batch_size | 批次大小 | 32 |
| alpha | L2正则化系数 | 0.0001 |

## 激活函数选项

- `relu`: ReLU (默认)
- `tanh`: 双曲正切
- `logistic`: Sigmoid
- `identity`: 线性激活

## 依赖关系

- `Longformer`: 用于生成查询嵌入
- `PyTorch`: MLP 神经网络实现
- `llm_data.json`: 模型配置数据
- `call_api`: API 调用工具函数
- `load_model`: 模型加载工具函数

## 模型兼容性

MLPRouter 支持两种模型格式：
1. **PyTorch 模型** (新格式): 支持 GPU 加速，推荐使用
2. **sklearn 模型** (旧格式): 向后兼容，仅 CPU

格式自动检测，无需手动配置。
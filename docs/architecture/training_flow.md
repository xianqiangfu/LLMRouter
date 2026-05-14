# LLMRouter 训练流程图

## 流程说明

训练流程将准备好的数据用于训练路由器模型，使其能够智能选择最合适的 LLM。

```mermaid
graph TB
    subgraph Start["训练开始"]
        A[Start<br/>启动训练命令<br/>llmrouter train --config config.yaml] --> B[加载配置文件]
    end

    subgraph ConfigLoad["配置加载"]
        B --> C1[解析 YAML 配置<br/>data_path, model_path,<br/>hparam, router_name]
        C1 --> C2[初始化 DataLoader<br/>项目根目录路径]
    end

    subgraph DataLoad["数据加载"]
        C2 --> D1[加载查询数据<br/>query_data_train.jsonl]
        C2 --> D2[加载查询嵌入<br/>query_embeddings.pt]
        C2 --> D3[加载路由数据<br/>routing_data_train.jsonl]
        C2 --> D4[加载 LLM 嵌入<br/>default_llm_embeddings.json]
        C2 --> D5[加载 LLM 元数据<br/>default_llm.json]
    end

    subgraph RouterInit["路由器初始化"]
        D1 --> E1[选择路由器类型<br/>KNN/SVM/MLP/MF/ELO/<br/>RouterDC/AutoMix/HybridLLM/<br/>Graph/CausalLM/GMT/Personalized]
        E1 --> E2[实例化路由器类<br/>继承 MetaRouter 基类]
        E2 --> E3[加载训练数据<br/>query_embeddings<br/>label_indices]
        E3 --> E4[初始化模型结构<br/>input_dim, num_classes,<br/>hidden_layers]
    end

    subgraph ModelSetup["模型设置"]
        E4 --> F1[设置超参数<br/>lr, epochs, batch_size,<br/>weight_decay]
        F1 --> F2[选择设备<br/>CUDA/CPU]
        F2 --> F3[定义损失函数<br/>CrossEntropyLoss/<br/>自定义损失]
        F3 --> F4[初始化优化器<br/>Adam/SGD/<br/>自定义优化器]
    end

    subgraph TrainingLoop["训练循环"]
        F4 --> G1[检查初始模型<br/>加载预训练权重<br/>如果存在]
        G1 --> G2[准备数据加载器<br/>TensorDataset + DataLoader<br/>shuffle=True]
        G2 --> G3{训练轮次<br/>epoch < epochs}

        G3 -->|True| G4[训练模式<br/>model.train]
        G4 --> G5[批次迭代<br/>for batch in dataloader]
        G5 --> G6[前向传播<br/>logits = model batch_X]
        G6 --> G7[计算损失<br/>loss = criterion logits batch_y]
        G7 --> G8[梯度清零<br/>optimizer.zero_grad]
        G8 --> G9[反向传播<br/>loss.backward]
        G9 --> G10[参数更新<br/>optimizer.step]
        G10 --> G11[记录损失<br/>epoch_losses.append]

        G11 --> G12{批次结束?}
        G12 -->|否| G5
        G12 -->|是| G13[计算平均损失<br/>avg_loss = mean epoch_losses]

        G13 --> G14[评估模式<br/>model.eval]
        G14 --> G15[计算训练准确率<br/>with no_grad predictions]
        G15 --> G16{打印进度<br/>epoch % 10 == 0<br/>or epoch == epochs - 1}
        G16 -->|是| G17[打印日志<br/>Epoch N/M - Loss=X<br/>Accuracy=Y]
        G16 -->|否| G18[继续训练]
        G17 --> G18
        G18 --> G3

        G3 -->|False| G19[训练完成]
    end

    subgraph Evaluation["模型评估"]
        G19 --> H1[评估模式<br/>model.eval]
        H1 --> H2[加载测试数据<br/>query_data_test.jsonl<br/>routing_data_test.jsonl]
        H2 --> H3[计算测试集性能<br/>accuracy, F1, etc.]
        H3 --> H4[汇总评估结果<br/>按任务类别<br/>按模型]
    end

    subgraph ModelSave["模型保存"]
        H4 --> I1[创建输出目录<br/>model_path]
        I1 --> I2[保存模型权重<br/>state_dict]
        I2 --> I3[保存元数据<br/>超参数, 配置信息]
        I3 --> I4[验证保存成功]
    end

    subgraph End["训练完成"]
        I4 --> J[End<br/>训练流程完成]
        H4 --> J
    end

    %% 样式定义
    classDef startEnd fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef config fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef dataLoad fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef modelInit fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef training fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef evaluation fill:#e0f7fa,stroke:#0097a7,stroke-width:2px
    classDef output fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    class A,J startEnd
    class B,C1,C2 config
    class D1,D2,D3,D4,D5 dataLoad
    class E1,E2,E3,E4,F1,F2,F3,F4 modelInit
    class G1,G2,G3,G4,G5,G6,G7,G8,G9,G10,G11,G12,G13,G14,G15,G16,G17,G18,G19 training
    class H1,H2,H3,H4 evaluation
    class I1,I2,I3,I4 output
```

## 关键步骤说明

### 1. 配置加载
解析 YAML 配置文件，获取以下配置：
- **data_path**: 数据文件路径
- **model_path**: 模型保存路径
- **hparam**: 超参数（学习率、批次大小、轮次等）
- **router_name**: 路由器类型

### 2. 数据加载
加载训练所需的所有数据：
- `query_data_train.jsonl`: 训练集查询数据
- `query_embeddings.pt`: 查询嵌入向量
- `routing_data_train.jsonl`: 路由标签数据
- `default_llm_embeddings.json`: LLM 嵌入
- `default_llm.json`: LLM 元数据

### 3. 路由器初始化
根据配置选择并实例化路由器：
- **单轮路由器**: KNN, SVM, MLP, MF, ELO, RouterDC, AutoMix, HybridLLM, Graph, CausalLM
- **多轮路由器**: Router-R1
- **个性化路由器**: GMT, Personalized
- **代理路由器**: KNN Multi-Round, LLM Multi-Round

### 4. 模型设置
配置训练环境和模型参数：
- **设备选择**: CUDA（如可用）或 CPU
- **损失函数**: CrossEntropyLoss 或自定义损失
- **优化器**: Adam、SGD 或自定义优化器
- **超参数**: 学习率、批次大小、权重衰减等

### 5. 训练循环
执行模型训练：
1. **前向传播**: 计算模型输出
2. **损失计算**: 计算预测与真实标签的损失
3. **梯度清零**: 清空历史梯度
4. **反向传播**: 计算梯度
5. **参数更新**: 根据梯度更新模型参数

定期打印训练进度和性能指标。

### 6. 模型评估
在测试集上评估模型性能：
- 加载测试数据
- 计算准确率等指标
- 按任务类别和模型汇总结果

### 7. 模型保存
保存训练好的模型：
- 保存模型权重（state_dict）
- 保存元数据和配置
- 验证保存成功

## 支持的路由器类型

| 路由器类型 | 说明 | 特点 |
|-----------|------|------|
| KNN | K-近邻路由 | 基于相似度选择 |
| SVM | 支持向量机 | 分类边界清晰 |
| MLP | 多层感知机 | 深度神经网络 |
| MF | 矩阵分解 | 潜在特征学习 |
| ELO | ELO 评分 | 动态性能评估 |
| RouterDC | 双对比学习 | 对比学习优化 |
| AutoMix | 自动模型混合 | 模型组合策略 |
| HybridLLM | 混合 LLM 路由 | 结合多种策略 |
| Graph | 图神经网络 | 图结构建模 |
| CausalLM | 因果语言模型 | 因果关系建模 |
| GMT | 图多任务个性化 | 多任务学习 |
| Personalized | 个性化路由 | 用户偏好建模 |

## 训练输出

- 模型权重文件（`.pkl` 或 `.pt`）
- 训练日志
- 评估结果报告
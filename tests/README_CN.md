# Tests 测试目录

本目录包含 LLMRouter 项目的所有测试代码，确保代码质量和功能正确性。

## 目录作用

`tests/` 目录是项目的测试代码库，用于：
- 验证各种路由器的功能和性能
- 测试训练和推理流程
- 确保 API 和插件系统的稳定性
- 维护代码覆盖率和质量标准

## 目录结构

```
tests/
├── inference_test/      # 推理测试
├── train_test/          # 训练测试
├── test_openclaw_http_tool_calls.py   # OpenCLaw HTTP 工具调用测试
├── test_plugin_system.py              # 插件系统测试
└── test_websocket.py                  # WebSocket 测试
```

## 测试分类

### 推理测试 (inference_test/)

推理测试用于验证各种路由器在推理阶段的行为和性能。

| 测试文件 | 路由器类型 | 说明 |
|---------|-----------|------|
| `test_automix_router.py` | AutoMix Router | 自动混合路由器测试 |
| `test_causallm_router.py` | CausalLLM Router | 因果语言模型路由器测试 |
| `test_dcrouter.py` | DC Router | 动态选择路由器测试 |
| `test_elorouter.py` | Elo Router | Elo 评分路由器测试 |
| `test_gmtrouter.py` | GMT Router | GMT 路由器测试 |
| `test_graphrouter.py` | Graph Router | 图路由器测试 |
| `test_hyrbridllm.py` | Hybrid LLM | 混合 LLM 测试 |
| `test_knnmultiroundrouter.py` | KNN Multi-Round Router | KNN 多轮路由器测试 |
| `test_knnrouter.py` | KNN Router | K-最近邻路由器测试 |
| `test_largest_router.py` | Largest Router | 最大模型路由器测试 |
| `test_llmmultiroundrouter.py` | LLM Multi-Round Router | LLM 多轮路由器测试 |
| `test_mfrouter.py` | MF Router | 矩阵分解路由器测试 |
| `test_mlprouter.py` | MLP Router | 多层感知机路由器测试 |
| `test_router_r1.py` | Router R1 | R1 路由器测试 |
| `test_smallest_router.py` | Smallest Router | 最小模型路由器测试 |
| `test_svmrouter.py` | SVM Router | 支持向量机路由器测试 |

### 训练测试 (train_test/)

训练测试用于验证路由器在训练阶段的功能。

| 测试文件 | 路由器类型 | 说明 |
|---------|-----------|------|
| `test_automix_router.py` | AutoMix Router | 自动混合路由器训练测试 |
| `test_causallm_router.py` | CausalLLM Router | 因果语言模型路由器训练测试 |
| `test_dcrouter.py` | DC Router | 动态选择路由器训练测试 |
| `test_elorouter.py` | Elo Router | Elo 评分路由器训练测试 |
| `test_gmtrouter.py` | GMT Router | GMT 路由器训练测试 |
| `test_graphrouter.py` | Graph Router | 图路由器训练测试 |
| `test_hybrid_llm.py` | Hybrid LLM | 混合 LLM 训练测试 |
| `test_knnmultiroundrouter.py` | KNN Multi-Round Router | KNN 多轮路由器训练测试 |
| `test_knnrouter.py` | KNN Router | K-最近邻路由器训练测试 |
| `test_mfrouter.py` | MF Router | 矩阵分解路由器训练测试 |
| `test_mlprouter.py` | MLP Router | 多层感知机路由器训练测试 |
| `test_svmrouter.py` | SVM Router | 支持向量机路由器训练测试 |

### 系统测试

| 测试文件 | 说明 |
|---------|------|
| `test_openclaw_http_tool_calls.py` | OpenCLaw HTTP 工具调用接口测试 |
| `test_plugin_system.py` | 插件系统功能测试 |
| `test_websocket.py` | WebSocket 连接和通信测试 |

## 测试框架

本项目使用 **pytest** 作为主要测试框架。

### 主要依赖

- `pytest`: 测试框架
- `torch`: PyTorch 深度学习框架
- `transformers`: Hugging Face Transformers
- `scikit-learn`: 机器学习工具库

## 测试运行方法

### 运行所有测试

```bash
pytest tests/
```

### 运行特定测试类型

运行推理测试：
```bash
pytest tests/inference_test/
```

运行训练测试：
```bash
pytest tests/train_test/
```

运行系统测试：
```bash
pytest tests/test_plugin_system.py
pytest tests/test_websocket.py
```

### 运行单个测试文件

```bash
pytest tests/inference_test/test_knnrouter.py
```

### 运行特定测试函数

```bash
pytest tests/inference_test/test_knnrouter.py::test_knn_router_inference
```

### 显示详细输出

```bash
pytest tests/ -v
```

### 显示打印输出

```bash
pytest tests/ -s
```

### 生成覆盖率报告

```bash
pytest tests/ --cov=llmrouter --cov-report=html
```

覆盖率报告将生成在 `htmlcov/` 目录中。

### 并行运行测试

安装 pytest-xdist：
```bash
pip install pytest-xdist
```

并行运行测试（使用所有 CPU 核心）：
```bash
pytest tests/ -n auto
```

## 测试覆盖率要求

- 目标测试覆盖率：**80%+**
- 核心路由器模块覆盖率：**90%+**
- API 接口覆盖率：**85%+**

## 测试最佳实践

1. **命名规范**: 测试文件以 `test_` 开头，测试函数以 `test_` 开头
2. **独立性**: 每个测试应该是独立的，不依赖其他测试的执行顺序
3. **清理资源**: 测试结束后清理临时文件和资源
4. **使用 fixture**: 合理使用 pytest fixture 进行测试数据准备
5. **断言清晰**: 使用清晰的断言信息，便于定位问题

## 常见问题

### 测试失败怎么办？

1. 查看详细的错误信息：`pytest tests/ -v`
2. 检查环境依赖是否正确安装
3. 确认测试数据路径是否正确
4. 查看是否有 GPU 资源限制（某些推理测试可能需要 GPU）

### 跳过耗时测试

```bash
pytest tests/ -m "not slow"
```

### 仅运行标记的测试

```bash
pytest tests/ -m "integration"
```

## 贡献指南

添加新测试时，请遵循以下规范：

1. 将推理测试放入 `inference_test/` 目录
2. 将训练测试放入 `train_test/` 目录
3. 系统级测试放在根目录
4. 为新路由器添加对应的推理和训练测试
5. 确保新增测试有清晰的文档字符串
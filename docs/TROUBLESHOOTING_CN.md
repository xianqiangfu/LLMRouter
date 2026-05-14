# LLMRouter 故障排查手册

## 目录

- [安装和配置问题](#安装和配置问题)
- [API 调用问题](#api-调用问题)
- [数据加载问题](#数据加载问题)
- [模型训练问题](#模型训练问题)
- [推理问题](#推理问题)
- [聊天界面问题](#聊天界面问题)
- [服务器部署问题](#服务器部署问题)
- [性能问题](#性能问题)
- [调试技巧和工具](#调试技巧和工具)
- [日志分析](#日志分析)

---

## 安装和配置问题

### 错误代码: `ERR-001`

**错误信息**: `ModuleNotFoundError: No module named 'llmrouter'`

**错误类型**: 安装错误

**原因分析**:
- LLMRouter 包未正确安装
- Python 环境配置错误
- 安装路径不在 Python 搜索路径中

**解决方案**:

```bash
# 1. 检查是否已安装
pip list | grep llmrouter

# 2. 如果未安装，从源码安装
cd LLMRouter
pip install -e .

# 3. 或者从 PyPI 安装
pip install llmrouter-lib

# 4. 验证安装
python -c "import llmrouter; print(llmrouter.__version__)"
```

**预防措施**:
- 使用虚拟环境（venv 或 conda）
- 确保使用正确的 Python 版本（推荐 Python 3.10）
- 在安装时使用 `-e` 参数进行可编辑安装

---

### 错误代码: `ERR-002`

**错误信息**: `ImportError: Missing optional dependency 'litellm'`

**错误类型**: 依赖缺失

**原因分析**:
- 可选依赖包未安装
- 使用了需要额外功能的功能但未安装对应依赖

**解决方案**:

```bash
# 安装核心依赖
pip install -e .

# 安装所有可选依赖
pip install -e ".[all]"

# 或单独安装缺失的依赖
pip install litellm

# 安装 RouterR1 支持（需要 GPU）
pip install -e ".[router-r1]"

# 安装聊天界面依赖
pip install gradio

# 安装服务器依赖
pip install fastapi uvicorn httpx pydantic
```

---

### 错误代码: `ERR-003`

**错误信息**: `FileNotFoundError: YAML file not found: <path>`

**错误类型**: 配置文件错误

**原因分析**:
- YAML 配置文件路径错误
- 文件名拼写错误
- 文件未创建

**解决方案**:

```bash
# 1. 检查文件是否存在
ls -la configs/model_config_train/knnrouter.yaml

# 2. 使用绝对路径
llmrouter train --router knnrouter --config /full/path/to/config.yaml

# 3. 从项目根目录运行，使用相对路径
cd /path/to/LLMRouter
llmrouter train --router knnrouter --config configs/model_config_train/knnrouter.yaml

# 4. 验证 YAML 格式
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

**调试技巧**:
- 使用 `pwd` 确认当前工作目录
- 使用 `find` 命令查找配置文件
- 检查文件权限

---

## API 调用问题

### 错误代码: `ERR-010`

**错误信息**: `ValueError: API_KEYS environment variable is not set`

**错误类型**: API 配置错误

**原因分析**:
- 未设置 API_KEYS 环境变量
- API_KEYS 环境变量为空

**解决方案**:

```bash
# 方法 1: 设置单个 API 密钥
export API_KEYS='your-api-key'

# 方法 2: 使用字典格式（推荐，支持多服务提供商）
export API_KEYS='{"NVIDIA": "nvidia-key-1,nvidia-key-2", "OpenAI": ["openai-key-1", "openai-key-2"], "Anthropic": "anthropic-key"}'

# 方法 3: 使用列表格式
export API_KEYS='["key1", "key2", "key3"]'

# 方法 4: 使用逗号分隔
export API_KEYS='key1,key2,key3'

# 验证设置
echo $API_KEYS
```

**持久化配置**:

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export API_KEYS='"'"'your-api-key'"'"'' >> ~/.bashrc
source ~/.bashrc
```

---

### 错误代码: `ERR-011`

**错误信息**: `ValueError: Service 'NVIDIA' not found in API_KEYS dict. Available services: [...]`

**错误类型**: 服务配置不匹配

**原因分析**:
- API_KEYS 使用字典格式，但 LLM 候选配置中的 service 字段不匹配
- 服务名称大小写不匹配

**解决方案**:

```bash
# 确保 service 字段与 API_KEYS 的键匹配
export API_KEYS='{"NVIDIA": "nvidia-key", "OpenAI": "openai-key"}'

# 在 LLM 候选配置文件（default_llm.json）中确保 service 字段正确
{
  "qwen2.5-7b-instruct": {
    "service": "NVIDIA",  # 必须与 API_KEYS 的键完全匹配（区分大小写）
    "model": "qwen/qwen2.5-7b-instruct",
    "api_endpoint": "https://integrate.api.nvidia.com/v1"
  }
}
```

**调试技巧**:
```bash
# 检查 API_KEYS 服务列表
echo $API_KEYS | python3 -c "import sys, json; print(json.load(sys.stdin).keys())"

# 检查 LLM 候选配置中的 service 字段
cat data/example_data/llm_candidates/default_llm.json | python3 -c "import sys, json; data = json.load(sys.stdin); print({k: v.get('service') for k, v in data.items()})"
```

---

### 错误代码: `ERR-012`

**错误信息**: `API Error: Authentication failed`

**错误类型**: API 认证错误

**原因分析**:
- API 密钥无效或已过期
- API 密钥格式错误
- API 密钥权限不足

**解决方案**:

```bash
# 1. 验证 API 密钥格式
echo $API_KEYS | python3 -m json.tool

# 2. 测试 API 密钥
API_ENDPOINT="https://integrate.api.nvidia.com/v1/chat/completions"
API_KEY="your-api-key"

curl "$API_ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "meta/llama-3.1-8b-instruct",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'

# 3. 重新生成或更新 API 密钥
```

---

### 错误代码: `ERR-013`

**错误信息**: `ValueError: api_endpoint not specified`

**错误类型**: API 端点配置错误

**原因分析**:
- 未配置 API 端点
- LLM 候选配置和路由器配置都缺少 api_endpoint

**解决方案**:

```yaml
# 方法 1: 在 LLM 候选配置中指定（推荐，优先级更高）
# data/example_data/llm_candidates/default_llm.json
{
  "qwen2.5-7b-instruct": {
    "service": "NVIDIA",
    "model": "qwen/qwen2.5-7b-instruct",
    "api_endpoint": "https://integrate.api.nvidia.com/v1",  # 必须配置
    ...
  }
}

# 方法 2: 在路由器配置中指定默认端点（fallback）
# configs/model_config_train/knnrouter.yaml
api_endpoint: 'https://integrate.api.nvidia.com/v1'
```

**优先级**: LLM 候选配置 > 路由器配置

---

### 错误代码: `ERR-014`

**错误信息**: `TimeoutError: Request timeout after 30 seconds`

**错误类型**: API 超时

**原因分析**:
- 网络连接问题
- API 服务响应慢
- 查询太复杂导致生成时间长

**解决方案**:

```bash
# 1. 检查网络连接
ping api.openai.com

# 2. 增加超时时间（在代码或配置中）
# 调用 API 时设置更长的 timeout
call_api(request, timeout=120)  # 从默认 30 增加到 120 秒

# 3. 使用重试机制
call_api(request, max_retries=5)

# 4. 减少查询复杂度或 max_tokens
llmrouter infer --router knnrouter --config config.yaml \
  --query "简单问题" \
  --max-tokens 256
```

---

### 错误代码: `ERR-015`

**错误信息**: `API Error: Rate limit exceeded`

**错误类型**: API 速率限制

**原因分析**:
- API 调用频率超过限制
- 单个 API 密钥的并发请求过多

**解决方案**:

```bash
# 1. 使用多个 API 密钥（负载均衡）
export API_KEYS='{"NVIDIA": "key1,key2,key3,key4,key5"}'

# 2. 减少并发工作进程数
python llmrouter/data/api_calling_evaluation.py --config config.yaml --workers 50  # 从 100 减少到 50

# 3. 添加延迟（在代码中）
import time
time.sleep(0.1)  # 每次调用后等待 100ms

# 4. 批量处理时使用更小的批次
```

---

## 数据加载问题

### 错误代码: `ERR-020`

**错误信息**: `[Warning] Missing query_data_train: <path>`

**错误类型**: 数据文件缺失

**原因分析**:
- 训练数据文件未生成
- 数据路径配置错误
- 数据生成流程未完成

**解决方案**:

```bash
# 1. 检查数据文件是否存在
ls -la data/example_data/query_data/

# 2. 如果数据文件不存在，运行数据生成流程
# Step 1: 生成查询数据
python llmrouter/data/data_generation.py --config llmrouter/data/sample_config.yaml

# Step 2: 生成 LLM 嵌入
python llmrouter/data/generate_llm_embeddings.py --config llmrouter/data/sample_config.yaml

# Step 3: API 调用和评估（需要 API_KEYS）
python llmrouter/data/api_calling_evaluation.py --config llmrouter/data/sample_config.yaml --workers 100

# 3. 使用示例数据（如果不需要重新生成）
# 确保 data/example_data/ 目录下有完整的示例数据
```

---

### 错误代码: `ERR-021`

**错误信息**: `FileNotFoundError: File does not exist: <path>`

**错误类型**: 路径错误

**原因分析**:
- 路径使用了错误的分隔符（Windows vs Linux）
- 相对路径相对于错误的基准目录
- 文件确实不存在

**解决方案**:

```yaml
# 在配置文件中使用正斜杠（推荐，跨平台兼容）
data_path:
  query_data_train: 'data/example_data/query_data/default_query_train.jsonl'
  # 不要使用: 'data\\example_data\\query_data\\...'

# 使用绝对路径（避免相对路径问题）
data_path:
  query_data_train: '/full/path/to/LLMRouter/data/example_data/query_data/default_query_train.jsonl'
```

**调试技巧**:
```python
# 使用 Python 检查路径
import os
path = 'data/example_data/query_data/default_query_train.jsonl'
print(os.path.isabs(path))  # 检查是否为绝对路径
print(os.path.exists(path))  # 检查文件是否存在
print(os.path.abspath(path))  # 获取绝对路径
```

---

### 错误代码: `ERR-022`

**错误信息**: `ValueError: Unsupported file extension: <ext>`

**错误类型**: 文件格式错误

**原因分析**:
- 文件扩展名不是支持的格式
- 模型加载器不支持该文件类型

**解决方案**:

```python
# LLMRouter 支持的文件格式
# PyTorch 模型: .pt, .pth
# Pickle 文件: .pkl
# JSON 文件: .json
# JSONL 文件: .jsonl
# CSV 文件: .csv

# 确保使用正确的扩展名
model_path:
  save_model_path: 'saved_models/knnrouter/knnrouter.pkl'  # 或 .pt

# 如果需要转换格式
import pickle
import torch

# 保存为 PyTorch 格式
torch.save(model, 'model.pt')

# 保存为 Pickle 格式
with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)
```

---

### 错误代码: `ERR-023`

**错误信息**: `json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`

**错误类型**: JSON 解析错误

**原因分析**:
- JSON 文件为空
- JSON 格式不正确
- 文件编码问题

**解决方案**:

```bash
# 1. 检查文件内容
cat data/example_data/llm_candidates/default_llm.json

# 2. 验证 JSON 格式
python -c "import json; print(json.dumps(json.load(open('data/example_data/llm_candidates/default_llm.json')), indent=2))"

# 3. 检查文件编码
file -i data/example_data/llm_candidates/default_llm.json

# 4. 如果编码问题，转换编码
iconv -f GBK -t UTF-8 input.json > output.json

# 5. 检查 JSONL 文件（每行一个 JSON 对象）
while read -r line; do echo "$line" | python -c "import sys, json; json.load(sys.stdin)"; done < data.jsonl
```

---

## 模型训练问题

### 错误代码: `ERR-030`

**错误信息**: `RuntimeError: CUDA out of memory`

**错误类型**: GPU 内存不足

**原因分析**:
- 批次大小太大
- 模型太大
- GPU 上有其他进程占用内存
- 梯度累积导致内存增长

**解决方案**:

```bash
# 1. 检查 GPU 使用情况
nvidia-smi

# 2. 清理 GPU 内存（如果有其他进程）
fuser -v /dev/nvidia*

# 3. 使用更小的批次大小
# 在配置文件中调整 batch_size
hparam:
  batch_size: 16  # 从更大的值减小

# 4. 使用 CPU 训练
llmrouter train --router knnrouter --config config.yaml --device cpu

# 5. 指定特定的 GPU
CUDA_VISIBLE_DEVICES=0 llmrouter train --router knnrouter --config config.yaml

# 6. 混合精度训练（如果模型支持）
# 需要在代码中添加 torch.cuda.amp 支持
```

---

### 错误代码: `ERR-031`

**错误信息**: `RuntimeError: No CUDA devices are available`

**错误类型**: GPU 不可用

**原因分析**:
- 系统没有 GPU
- CUDA 驱动未正确安装
- PyTorch 是 CPU 版本
- GPU 被禁用

**解决方案**:

```bash
# 1. 检查 GPU 是否可用
python -c "import torch; print(torch.cuda.is_available())"

# 2. 检查 CUDA 驱动
nvidia-smi

# 3. 检查 PyTorch CUDA 版本
python -c "import torch; print(torch.version.cuda)"

# 4. 如果没有 GPU 或 CUDA 不可用，使用 CPU
llmrouter train --router knnrouter --config config.yaml --device cpu

# 5. 重新安装带 CUDA 的 PyTorch（如果系统有 GPU）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

### 错误代码: `ERR-032`

**错误信息**: `NotImplementedError: Subclasses must implement route_batch()`

**错误类型**: 抽象方法未实现

**原因分析**:
- 自定义路由器未继承 MetaRouter
- 自定义路由器未实现必需的抽象方法

**解决方案**:

```python
# 确保自定义路由器正确实现
from llmrouter.models.meta_router import MetaRouter
import torch.nn as nn

class MyRouter(MetaRouter):
    def __init__(self, yaml_path: str):
        model = nn.Identity()
        super().__init__(model=model, yaml_path=yaml_path)
        self.llm_names = list(self.llm_data.keys())

    # 必须实现这两个抽象方法
    def route_batch(self, batch):
        """批量路由决策"""
        # 实现批量路由逻辑
        pass

    def route_single(self, batch):
        """单个查询路由决策"""
        query = batch['query']
        # 实现路由逻辑
        return {
            "query": query,
            "model_name": selected_llm,
            "predicted_llm": selected_llm,
        }
```

---

### 错误代码: `ERR-033`

**错误信息**: `KeyError: 'llm_data'`

**错误类型**: 数据加载失败

**原因分析**:
- LLM 候选数据未加载
- 配置文件中缺少 llm_data 路径
- LLM 候选文件格式错误

**解决方案**:

```yaml
# 确保配置文件包含 llm_data 路径
data_path:
  llm_data: 'data/example_data/llm_candidates/default_llm.json'

# 检查文件格式
cat data/example_data/llm_candidates/default_llm.json | python -c "import sys, json; data = json.load(sys.stdin); print(type(data)); print(list(data.keys())[:5])"

# 如果文件不存在或格式错误，从示例数据复制
# 或重新运行数据生成流程
```

---

### 错误代码: `ERR-034`

**错误信息**: `ValueError: Input must be 2D array, got shape <shape>`

**错误类型**: 数据维度错误

**原因分析**:
- 输入数据维度与模型期望不符
- 嵌入向量维度不匹配
- 批次处理时维度问题

**解决方案**:

```python
# 1. 检查输入数据维度
import numpy as np
print(embeddings.shape)  # 应该是 (n_samples, n_features)

# 2. 重塑数据
if len(embeddings.shape) == 1:
    embeddings = embeddings.reshape(1, -1)

# 3. 确保批次维度正确
# 对于批次数据，形状应该是 (batch_size, feature_dim)

# 4. 调试：打印每一步的形状
print(f"Query embedding shape: {query_embedding.shape}")
print(f"LLM embedding shape: {llm_embedding.shape}")
print(f"Input shape to model: {input_tensor.shape}")
```

---

## 推理问题

### 错误代码: `ERR-040`

**错误信息**: `FileNotFoundError: Model file not found: <path>`

**错误类型**: 模型文件缺失

**原因分析**:
- 训练的模型未保存
- 模型路径配置错误
- 模型文件被移动或删除

**解决方案**:

```bash
# 1. 检查模型文件是否存在
ls -la saved_models/knnrouter/

# 2. 使用 --load_model_path 参数指定正确的模型路径
llmrouter infer --router knnrouter --config config.yaml \
  --load_model_path /correct/path/to/model.pt \
  --query "Hello"

# 3. 更新配置文件中的模型路径
# configs/model_config_test/knnrouter.yaml
model_path:
  load_model_path: 'saved_models/knnrouter/knnrouter.pkl'

# 4. 重新训练模型
llmrouter train --router knnrouter --config configs/model_config_train/knnrouter.yaml
```

---

### 错误代码: `ERR-041`

**错误信息**: `ValueError: Unknown router: <router_name>`

**错误类型**: 路由器名称错误

**原因分析**:
- 路由器名称拼写错误
- 路由器未正确注册
- 自定义路由器未被发现

**解决方案**:

```bash
# 1. 列出所有可用的路由器
llmrouter list-routers

# 2. 检查路由器名称拼写
# 注意大小写，通常是小写
llmrouter train --router knnrouter --config config.yaml  # 正确
# 不是 KNNRouter 或 Knnrouter

# 3. 检查自定义路由器是否在正确位置
ls -la custom_routers/
ls -la ~/.llmrouter/plugins/

# 4. 设置插件路径环境变量
export LLMROUTER_PLUGINS="/path/to/custom_routers"

# 5. 确保自定义路由器有 __init__.py 文件
```

---

### 错误代码: `ERR-042`

**错误信息**: `AttributeError: 'NoneType' object has no attribute 'route_single'`

**错误类型**: 路由器实例化失败

**原因分析**:
- 路由器加载失败
- 配置文件错误导致路由器初始化失败

**解决方案**:

```bash
# 1. 启用详细输出
llmrouter infer --router knnrouter --config config.yaml --verbose --query "Hello"

# 2. 检查路由器加载过程
# 在代码中添加调试信息
import traceback
try:
    router = load_router(args.router, args.config, args.load_model_path)
except Exception as e:
    print(f"Error loading router: {e}")
    traceback.print_exc()

# 3. 验证配置文件
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# 4. 检查依赖的文件是否存在
# 确保 data_path 中的所有文件都存在
```

---

### 错误代码: `ERR-043`

**错误信息**: `Error: Input file not found: <path>`

**错误类型**: 输入文件错误

**原因分析**:
- 批量推理时输入文件不存在
- 文件路径错误

**解决方案**:

```bash
# 1. 检查输入文件
ls -la queries.txt

# 2. 使用绝对路径
llmrouter infer --router knnrouter --config config.yaml \
  --input /full/path/to/queries.txt \
  --output results.json

# 3. 验证文件格式
# 支持的格式: .txt, .json, .jsonl
# .txt: 每行一个查询
# .json: JSON 数组或包含 "query" 字段的对象
# .jsonl: 每行一个 JSON 对象

# 4. 检查文件内容
head -n 5 queries.txt
```

---

## 聊天界面问题

### 错误代码: `ERR-050`

**错误信息**: `Error: gradio is required for chat interface`

**错误类型**: 依赖缺失

**原因分析**:
- 未安装 gradio 包
- Gradio 版本不兼容

**解决方案**:

```bash
# 1. 安装 gradio
pip install gradio

# 2. 验证安装
python -c "import gradio; print(gradio.__version__)"

# 3. 如果版本问题，重新安装
pip uninstall gradio
pip install gradio>=4.0.0

# 4. 启动聊天界面
llmrouter chat --router knnrouter --config config.yaml
```

---

### 错误代码: `ERR-051`

**错误信息**: `OSError: [Errno 48] Address already in use`

**错误类型**: 端口占用

**原因分析**:
- 默认端口 8001 已被其他进程占用
- 之前的 Gradio 会话未正确关闭

**解决方案**:

```bash
# 1. 查找占用端口的进程
lsof -i :8001  # Linux/Mac
netstat -ano | findstr :8001  # Windows

# 2. 杀死占用端口的进程
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows

# 3. 使用不同的端口
llmrouter chat --router knnrouter --config config.yaml --port 8002

# 4. 指定 host 和端口
llmrouter chat --router knnrouter --config config.yaml \
  --host 127.0.0.1 \
  --port 7860
```

---

### 错误代码: `ERR-052`

**错误信息**: `Error: API_KEYS not set`

**错误类型**: API 配置错误

**原因分析**:
- 聊天界面调用 LLM 需要 API_KEYS
- 环境变量未设置

**解决方案**:

```bash
# 设置 API_KEYS
export API_KEYS='your-api-key'

# 然后启动聊天界面
llmrouter chat --router knnrouter --config config.yaml
```

---

## 服务器部署问题

### 错误代码: `ERR-060`

**错误信息**: `Error: FastAPI dependencies required`

**错误类型**: 依赖缺失

**原因分析**:
- 未安装 FastAPI 及相关依赖
- 服务模式需要额外的包

**解决方案**:

```bash
# 1. 安装 FastAPI 依赖
pip install fastapi uvicorn httpx pydantic

# 2. 验证安装
python -c "import fastapi, uvicorn, httpx, pydantic; print('OK')"

# 3. 启动服务器
llmrouter serve --config configs/openclaw_example.yaml
```

---

### 错误代码: `ERR-061`

**错误信息**: `OSError: [Errno 98] Address already in use`

**错误类型**: 端口占用

**原因分析**:
- 默认端口 8000 已被占用
- 之前的服务器实例未关闭

**解决方案**:

```bash
# 1. 查找占用端口的进程
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# 2. 杀死进程或使用不同端口
kill -9 <PID>

# 3. 使用不同端口启动
llmrouter serve --config configs/openclaw_example.yaml --port 8001

# 4. 或在配置文件中指定端口
# 修改 configs/openclaw_example.yaml
serve:
  host: "0.0.0.0"
  port: 8001
```

---

### 错误代码: `ERR-062`

**错误信息**: `HTTPException: 404 Not Found`

**错误类型**: API 端点错误

**原因分析**:
- 请求了不存在的端点
- LLM 模型配置错误

**解决方案**:

```bash
# 1. 检查服务器健康状态
curl http://localhost:8000/health

# 2. 检查可用模型列表
curl http://localhost:8000/v1/models

# 3. 检查配置文件中的模型配置
cat configs/openclaw_example.yaml | grep -A 10 "llms:"

# 4. 使用正确的端点
# /v1/chat/completions - 聊天补全
# /v1/models - 模型列表
# /health - 健康检查
# /v1/chat/ws - WebSocket 端点
```

---

## 性能问题

### 错误代码: `ERR-070`

**问题**: 路由推理速度慢

**原因分析**:
- KNN 路由器使用大量邻居
- 嵌入向量维度太高
- 未使用 GPU 加速
- 模型在冷启动时需要加载

**解决方案**:

```yaml
# 1. 减少邻居数量（对于 KNN）
hparam:
  n_neighbors: 3  # 从默认的 5 减少到 3

# 2. 使用更快的距离计算算法
hparam:
  algorithm: "brute"  # 对于小数据集更快
  metric: "cosine"    # 余弦距离通常更快

# 3. 使用 GPU（如果可用）
llmrouter infer --router mlprouter --config config.yaml --device cuda

# 4. 使用更小的嵌入向量
# 在数据生成阶段使用更小的嵌入维度

# 5. 预加载模型
# 在服务启动时预加载模型，避免首次请求延迟

# 6. 批量处理而非逐个处理
llmrouter infer --router knnrouter --config config.yaml \
  --input queries.txt \
  --output results.json
```

---

### 错误代码: `ERR-071`

**问题**: API 调用延迟高

**原因分析**:
- 网络延迟
- API 服务响应慢
- 查询太复杂

**解决方案**:

```bash
# 1. 测试网络延迟
ping api.openai.com

# 2. 使用更快的 API 端点
# 选择地理位置更近的 API 端点

# 3. 减少 max_tokens
llmrouter infer --router knnrouter --config config.yaml \
  --query "简单问题" \
  --max-tokens 256

# 4. 使用本地模型（Ollama, vLLM）
# 配置本地 API 端点
export API_KEYS='{"Ollama": ""}'
# 在配置中使用本地端点
api_endpoint: 'http://localhost:11434/v1'

# 5. 并行调用（对于批量推理）
# 使用 --workers 参数
python llmrouter/data/api_calling_evaluation.py --config config.yaml --workers 50
```

---

### 错误代码: `ERR-072`

**问题**: 内存使用过高

**原因分析**:
- 加载了太多模型
- 嵌入向量占用大量内存
- 批次太大

**解决方案**:

```python
# 1. 监控内存使用
import psutil
import os
process = psutil.Process(os.getpid())
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")

# 2. 使用更小的数据类型
# 将 float64 转换为 float32
embeddings = embeddings.astype(np.float32)

# 3. 使用生成器而非列表
# 处理大数据集时使用生成器逐批处理

# 4. 及时释放内存
import gc
del large_object
gc.collect()

# 5. 使用流式处理
# 对于聊天和推理，使用流式响应而非等待完整响应
```

---

## 调试技巧和工具

### 1. Python 调试器

```bash
# 使用 pdb 调试
python -m pdb llmrouter/cli/router_main.py train --router knnrouter --config config.yaml

# 在代码中插入断点
import pdb; pdb.set_trace()

# 使用 IPython 调试器（更友好）
import ipdb; ipdb.set_trace()
```

---

### 2. 日志配置

```python
# 设置日志级别
import logging
logging.basicConfig(level=logging.DEBUG)

# 或在环境变量中设置
export LOG_LEVEL=DEBUG

# 保存日志到文件
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('llmrouter.log'),
        logging.StreamHandler()
    ]
)
```

---

### 3. 性能分析

```python
# 使用 cProfile 分析性能
python -m cProfile -o profile.stats llmrouter/cli/router_main.py train --router knnrouter --config config.yaml

# 使用 pstats 查看结果
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"

# 使用 line_profiler 分析函数级别性能
pip install line_profiler
kernprof -l -v my_script.py
```

---

### 4. 内存分析

```bash
# 使用 memory_profiler
pip install memory_profiler
python -m memory_profiler my_script.py

# 在代码中添加装饰器
from memory_profiler import profile

@profile
def my_function():
    # 函数代码
    pass
```

---

### 5. 网络调试

```bash
# 使用 curl 测试 API 端点
curl -v http://localhost:8000/health
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"auto","messages":[{"role":"user","content":"Hello"}]}'

# 使用 nc 监听端口
nc -l 8000

# 使用 wireshark 或 tcpdump 分析网络流量
tcpdump -i any port 8000
```

---

### 6. 配置验证

```python
# 验证 YAML 配置
import yaml
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
    print(yaml.dump(config, default_flow_style=False))

# 验证 JSON 配置
import json
with open('llm_candidates.json', 'r') as f:
    data = json.load(f)
    print(json.dumps(data, indent=2))
```

---

### 7. 环境检查脚本

```bash
#!/bin/bash
# env_check.sh - 环境检查脚本

echo "=== Python 环境 ==="
python --version
pip list | grep -E "torch|numpy|yaml|gradio|fastapi"

echo -e "\n=== CUDA 环境 ==="
nvidia-smi
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

echo -e "\n=== 环境变量 ==="
echo "API_KEYS: ${API_KEYS:0:20}..."
echo "LLMROUTER_PLUGINS: $LLMROUTER_PLUGINS"

echo -e "\n=== 文件检查 ==="
ls -la configs/
ls -la data/example_data/

echo -e "\n=== 网络检查 ==="
ping -c 1 api.openai.com > /dev/null 2>&1 && echo "API reachable" || echo "API not reachable"
```

---

### 8. 单元测试

```python
# test_my_router.py
import unittest
from llmrouter.models.meta_router import MetaRouter

class TestMyRouter(unittest.TestCase):
    def setUp(self):
        self.router = MyRouter('config.yaml')

    def test_route_single(self):
        result = self.router.route_single({'query': 'Hello'})
        self.assertIn('model_name', result)
        self.assertIn('predicted_llm', result)

    def test_route_batch(self):
        batch = [{'query': f'Query {i}'} for i in range(10)]
        results = self.router.route_batch(batch)
        self.assertEqual(len(results), 10)

if __name__ == '__main__':
    unittest.main()
```

---

## 日志分析

### 1. 常见日志模式

```bash
# 查找错误日志
grep -i "error" llmrouter.log

# 查找警告日志
grep -i "warning" llmrouter.log

# 查找 API 调用错误
grep "API Error" llmrouter.log

# 查找超时错误
grep -i "timeout" llmrouter.log
```

---

### 2. 日志聚合和分析

```bash
# 统计错误类型
grep "Error:" llmrouter.log | awk '{print $NF}' | sort | uniq -c

# 查找高频错误
grep -i error llmrouter.log | cut -d: -f3 | sort | uniq -c | sort -rn | head -10

# 分析时间范围内的错误
grep "2025-05-15" llmrouter.log | grep -i error
```

---

### 3. 实时日志监控

```bash
# 实时查看日志
tail -f llmrouter.log

# 实时过滤错误
tail -f llmrouter.log | grep -i error

# 高亮错误和警告
tail -f llmrouter.log | grep --color -E "error|warning|ERROR|WARNING"
```

---

### 4. 日志格式化

```python
# 结构化日志
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

# 使用结构化日志
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.getLogger().addHandler(handler)
```

---

## 快速诊断检查清单

当遇到问题时，按以下顺序检查：

- [ ] Python 版本是否正确（推荐 3.10）
- [ ] LLMRouter 是否正确安装
- [ ] 所有依赖是否已安装
- [ ] API_KEYS 环境变量是否设置
- [ ] 配置文件是否存在且格式正确
- [ ] 数据文件是否存在
- [ ] 模型文件是否存在
- [ ] GPU（如果使用）是否可用
- [ ] 端口是否被占用（服务器模式）
- [ ] 网络连接是否正常

---

## 获取帮助

如果以上解决方案无法解决问题：

1. **查看文档**: [LLMRouter GitHub](https://github.com/ulab-uiuc/LLMRouter)
2. **搜索 Issues**: 在 GitHub Issues 中搜索类似问题
3. **提交 Issue**: 创建新的 Issue，包含：
   - 错误信息完整堆栈
   - 操作系统和 Python 版本
   - 最小复现代码
   - 相关配置文件
4. **Slack 社区**: 加入 [Slack 社区](https://join.slack.com/t/llmrouteropen-ri04588/shared_invite/zt-3mkx82cut-A25v5yR52xVKi7_jm_YK_w)
5. **微信群**: 查看主页获取微信二维码

---

## 更新日志

- **2025-05-15**: 创建初始版本
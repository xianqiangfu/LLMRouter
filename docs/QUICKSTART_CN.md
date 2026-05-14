# LLMRouter 快速入门指南

欢迎使用 LLMRouter！本指南将帮助您快速搭建环境并开始使用 LLMRouter 进行智能路由。

## 目录

- [环境搭建](#环境搭建)
- [安装 LLMRouter](#安装-llmrouter)
- [配置 API 密钥](#配置-api-密钥)
- [快速开始](#快速开始)
- [常用命令](#常用命令)
- [故障排除](#故障排除)

---

## 环境搭建

### 系统要求

- **操作系统**: Linux, macOS, Windows
- **Python 版本**: 3.10 或更高版本
- **CUDA** (可选): 如需 GPU 加速，请安装 CUDA 11.8 或更高版本

### 安装 Python

**Linux/macOS:**
```bash
# 使用 pyenv (推荐)
pyenv install 3.10.12
pyenv global 3.10.12

# 或使用 conda
conda create -n llmrouter python=3.10
conda activate llmrouter
```

**Windows:**
```bash
# 下载并安装 Python 3.10
# https://www.python.org/downloads/

# 或使用 Anaconda
conda create -n llmrouter python=3.10
conda activate llmrouter
```

### 安装 CUDA (GPU 加速)

**检查 CUDA 是否已安装:**
```bash
nvidia-smi
```

**安装 CUDA Toolkit (如未安装):**

**Linux:**
```bash
# Ubuntu/Debian
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda-repo-ubuntu2204-12-1-local_12.1.0-530.30.02-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2204-12-1-local_12.1.0-530.30.02-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2204-12-1-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda
```

**Windows:**
- 下载并安装 CUDA Toolkit: https://developer.nvidia.com/cuda-downloads

---

## 安装 LLMRouter

### 方法一：从源码安装

```bash
# 克隆仓库
git clone https://github.com/ulab-uiuc/LLMRouter.git
cd LLMRouter

# 创建并激活虚拟环境
conda create -n llmrouter python=3.10
conda activate llmrouter

# 基础安装
pip install -e .

# 可选：安装 RouterR1 支持 (需要 GPU)
# RouterR1 需要 vllm==0.6.3 (torch==2.4.0)
pip install -e ".[router-r1]"

# 可选：安装所有可选依赖
pip install -e ".[all]"
```

### 方法二：从 PyPI 安装

```bash
pip install llmrouter-lib
```

### 验证安装

```bash
# 检查是否安装成功
llmrouter --help

# 查看可用的路由器
llmrouter list-routers
```

---

## 配置 API 密钥

LLMRouter 需要 API 密钥来调用 LLM API 进行推理、聊天和数据生成。

### 获取免费 NVIDIA API 密钥

NVIDIA 提供免费的 API 密钥，您可以访问 [https://build.nvidia.com/](https://build.nvidia.com/) 创建账户并生成 API 密钥。

### 配置方式

#### 方式一：服务提供商字典格式 (推荐)

适用于使用多个服务提供商的场景：

```bash
export API_KEYS='{"NVIDIA": "nvidia-key-1,nvidia-key-2", "OpenAI": ["openai-key-1", "openai-key-2"], "Anthropic": "anthropic-key-1"}'
```

**格式说明：**
- **键 (Keys)**: 服务提供商名称 (必须与 LLM 候选 JSON 中的 `service` 字段匹配)
- **值 (Values)**: 可以是：
  - 逗号分隔字符串: `"key1,key2,key3"`
  - JSON 数组: `["key1", "key2", "key3"]`
  - 单个字符串: `"key1"`
- **负载均衡**: 每个服务维护自己的轮询计数器
- **服务匹配**: 系统自动匹配 LLM 候选 JSON 中的 `service` 字段

**LLM 候选 JSON 示例:**
```json
{
  "qwen2.5-7b-instruct": {
    "service": "NVIDIA",
    "model": "qwen/qwen2.5-7b-instruct",
    "api_endpoint": "https://integrate.api.nvidia.com/v1"
  },
  "gpt-4": {
    "service": "OpenAI",
    "model": "gpt-4",
    "api_endpoint": "https://api.openai.com/v1"
  }
}
```

#### 方式二：JSON 数组格式

```bash
export API_KEYS='["your-key-1", "your-key-2", "your-key-3"]'
```

#### 方式三：逗号分隔格式

```bash
export API_KEYS='key1,key2,key3'
```

#### 方式四：单个密钥

```bash
export API_KEYS='your-api-key'
```

### 持久化配置

将导出命令添加到 shell 配置文件中：

**Linux/macOS:**
```bash
echo "export API_KEYS='your-api-key'" >> ~/.bashrc
source ~/.bashrc
```

**Windows (PowerShell):**
```powershell
$env:API_KEYS='your-api-key'
# 或添加到 $PROFILE
```

### 本地模型配置

使用本地 LLM (如 Ollama, vLLM, SGLang) 时，可以使用空字符串作为 API 密钥：

```bash
export API_KEYS='{"Ollama": ""}'
```

**Ollama 配置示例:**
```json
{
  "gemma3": {
    "size": "3B",
    "feature": "Gemma 3B model hosted locally via Ollama",
    "input_price": 0.0,
    "output_price": 0.0,
    "model": "gemma3",
    "service": "Ollama",
    "api_endpoint": "http://localhost:11434/v1"
  }
}
```

---

## 快速开始

### 1. 数据生成

LLMRouter 包含完整的数据生成流水线，将基准数据集转换为路由数据。

**使用示例数据:**

```bash
# 步骤 1: 生成查询数据
python llmrouter/data/data_generation.py --config llmrouter/data/sample_config.yaml

# 步骤 2: 生成 LLM 嵌入
python llmrouter/data/generate_llm_embeddings.py --config llmrouter/data/sample_config.yaml

# 步骤 3: API 调用与评估 (需要 API_KEYS)
python llmrouter/data/api_calling_evaluation.py --config llmrouter/data/sample_config.yaml --workers 100
```

**输出文件:**
- `query_data_train.jsonl` / `query_data_test.jsonl` - 查询数据 (训练/测试集)
- `default_llm_embeddings.json` - LLM 嵌入
- `query_embeddings_longformer.pt` - 查询嵌入
- `default_routing_train_data.jsonl` / `default_routing_test_data.jsonl` - 路由数据

### 2. 训练路由器

使用准备好的数据训练路由器模型：

```bash
# 训练 KNN 路由器
llmrouter train --router knnrouter --config configs/model_config_train/knnrouter.yaml

# 使用 GPU 训练 MLP 路由器
CUDA_VISIBLE_DEVICES=0 llmrouter train --router mlprouter --config configs/model_config_train/mlprouter.yaml --device cuda

# 静默训练 MF 路由器
CUDA_VISIBLE_DEVICES=1 llmrouter train --router mfrouter --config configs/model_config_train/mfrouter.yaml --device cuda --quiet
```

**训练参数说明:**
- `--router`: 路由器类型 (knnrouter, mlprouter, svmrouter, mfrouter, graphrouter 等)
- `--config`: 配置文件路径
- `--device`: 设备选择 (cuda 或 cpu)
- `--quiet`: 静默模式 (减少输出)

### 3. 推理

使用训练好的路由器执行推理：

```bash
# 单个查询推理
llmrouter infer --router knnrouter --config configs/model_config_test/knnrouter.yaml --query "什么是机器学习？"

# 批量推理
llmrouter infer --router knnrouter --config configs/model_config_test/knnrouter.yaml --input queries.txt --output results.json

# 仅路由 (不调用 LLM API)
llmrouter infer --router knnrouter --config configs/model_config_test/knnrouter.yaml --query "你好" --route-only

# 自定义生成参数
llmrouter infer --router knnrouter --config configs/model_config_test/knnrouter.yaml --query "解释人工智能" --temp 0.7 --max-tokens 2048 --verbose
```

**输入文件格式:**
- `.txt`: 每行一个查询
- `.json`: 字符串列表或包含 `"query"` 字段的对象列表
- `.jsonl`: 每行一个 JSON 对象

### 4. 交互式聊天

启动交互式聊天界面：

```bash
# 基本聊天界面
llmrouter chat --router knnrouter --config configs/model_config_test/knnrouter.yaml

# 自定义主机和端口
llmrouter chat --router knnrouter --config configs/model_config_test/knnrouter.yaml --host 0.0.0.0 --port 7860

# 公共共享链接
llmrouter chat --router knnrouter --config configs/model_config_test/knnrouter.yaml --share

# 指定查询模式
llmrouter chat --router knnrouter --config configs/model_config_test/knnrouter.yaml --mode full_context --top_k 5
```

**查询模式:**
- `current_only`: 仅基于当前查询路由 (默认)
- `full_context`: 结合所有聊天历史与当前查询
- `retrieval`: 检索 top-k 相似历史查询

### 5. 完整示例

从零开始的完整流程示例：

```bash
# 1. 设置环境
conda create -n llmrouter python=3.10
conda activate llmrouter
pip install -e .

# 2. 配置 API 密钥
export API_KEYS='your-nvidia-api-key'

# 3. 生成数据
python llmrouter/data/data_generation.py --config llmrouter/data/sample_config.yaml
python llmrouter/data/generate_llm_embeddings.py --config llmrouter/data/sample_config.yaml
python llmrouter/data/api_calling_evaluation.py --config llmrouter/data/sample_config.yaml --workers 100

# 4. 训练路由器
llmrouter train --router knnrouter --config configs/model_config_train/knnrouter.yaml

# 5. 执行推理
llmrouter infer --router knnrouter --config configs/model_config_test/knnrouter.yaml --query "什么是量子计算？"

# 6. 启动聊天界面
llmrouter chat --router knnrouter --config configs/model_config_test/knnrouter.yaml
```

---

## 常用命令

### 训练命令

```bash
llmrouter train --router <router_name> --config <config_path> [options]
```

**选项:**
- `--device`: 设备选择 (cuda/cpu)
- `--quiet`: 静默模式
- `--verbose`: 详细输出

### 推理命令

```bash
llmrouter infer --router <router_name> --config <config_path> [options]
```

**选项:**
- `--query`: 单个查询文本
- `--input`: 输入文件路径
- `--output`: 输出文件路径
- `--route-only`: 仅路由，不调用 LLM API
- `--temp`: 温度参数
- `--max-tokens`: 最大 token 数
- `--verbose`: 详细输出

### 聊天命令

```bash
llmrouter chat --router <router_name> --config <config_path> [options]
```

**选项:**
- `--host`: 主机地址
- `--port`: 端口号
- `--share`: 创建公共共享链接
- `--mode`: 查询模式 (current_only/full_context/retrieval)
- `--top-k`: 检索的 top-k 数量

### 服务命令

```bash
llmrouter serve --config <config_path> [options]
```

**选项:**
- `--router`: 路由器类型
- `--host`: 主机地址
- `--port`: 端口号

### 列表命令

```bash
# 列出所有可用路由器
llmrouter list-routers
```

### 直接执行脚本

```bash
# 训练
python -m llmrouter.cli.router_train --router knnrouter --config config.yaml

# 推理
python -m llmrouter.cli.router_inference --router knnrouter --config config.yaml --query "你好"

# 聊天
python -m llmrouter.cli.router_chat --router knnrouter --config config.yaml
```

---

## 故障排除

### 安装问题

**问题: pip 安装失败**

解决方案:
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**问题: CUDA 相关错误**

解决方案:
```bash
# 检查 CUDA 版本
nvidia-smi

# 安装兼容的 PyTorch 版本
pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu121

# 或使用 CPU 版本
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### API 密钥问题

**问题: API 密钥未配置错误**

错误信息: `API key not found`

解决方案:
```bash
# 检查环境变量
echo $API_KEYS

# 设置环境变量
export API_KEYS='your-api-key'

# 验证 API 密钥
curl -H "Authorization: Bearer $API_KEYS" https://integrate.api.nvidia.com/v1/models
```

**问题: API 调用失败**

解决方案:
```bash
# 检查 API 端点是否正确
# 查看 LLM 候选 JSON 文件中的 api_endpoint 字段

# 测试 API 连接
curl https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEYS" \
  -d '{
    "model": "meta/llama-3.1-8b-instruct",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### 数据问题

**问题: 数据文件未找到**

错误信息: `FileNotFoundError: [Errno 2] No such file or directory`

解决方案:
```bash
# 检查配置文件中的路径
cat llmrouter/data/sample_config.yaml

# 验证文件是否存在
ls -la data/example_data/

# 使用绝对路径
# 或确保在工作目录中执行命令
```

**问题: 数据格式错误**

解决方案:
```bash
# 检查数据文件格式
head -n 1 data/example_data/routing_data/default_routing_train_data.jsonl

# 验证 JSON 格式
cat data/example_data/routing_data/default_routing_train_data.jsonl | jq
```

### 训练问题

**问题: CUDA out of memory**

解决方案:
```bash
# 减小批次大小
# 编辑配置文件，减小 batch_size

# 使用 CPU 训练
llmrouter train --router knnrouter --config config.yaml --device cpu

# 使用多个 GPU 并行训练
CUDA_VISIBLE_DEVICES=0,1 llmrouter train --router knnrouter --config config.yaml
```

**问题: 模型保存失败**

解决方案:
```bash
# 创建输出目录
mkdir -p saved_models/knnrouter

# 检查磁盘空间
df -h

# 检查写入权限
ls -ld saved_models/
```

### 推理问题

**问题: 路由器模型未找到**

错误信息: `Model file not found`

解决方案:
```bash
# 检查模型文件路径
ls -la saved_models/knnrouter/

# 确保配置文件中的路径正确
cat configs/model_config_test/knnrouter.yaml

# 重新训练模型
llmrouter train --router knnrouter --config configs/model_config_train/knnrouter.yaml
```

**问题: 推理结果不准确**

解决方案:
```bash
# 检查训练数据质量
head -n 5 data/example_data/routing_data/default_routing_train_data.jsonl

# 尝试不同的路由器
llmrouter train --router mlprouter --config configs/model_config_train/mlprouter.yaml

# 调整超参数
# 编辑配置文件中的 hparam 部分
```

### 聊天界面问题

**问题: Gradio 界面无法启动**

解决方案:
```bash
# 检查端口是否被占用
netstat -an | grep 7860

# 使用不同的端口
llmrouter chat --router knnrouter --config config.yaml --port 7861

# 安装 Gradio
pip install gradio
```

**问题: 公共链接无法创建**

解决方案:
```bash
# 确保网络连接正常
ping google.com

# 不使用公共链接
llmrouter chat --router knnrouter --config config.yaml

# 检查 Gradio 版本
pip install --upgrade gradio
```

### 性能问题

**问题: 推理速度慢**

解决方案:
```bash
# 使用 GPU 加速
CUDA_VISIBLE_DEVICES=0 llmrouter infer --router knnrouter --config config.yaml --query "你好"

# 减小 KNN 的 n_neighbors 值
# 编辑配置文件，减小 n_neighbors

# 使用批量推理
llmrouter infer --router knnrouter --config config.yaml --input queries.txt --output results.json
```

### 依赖问题

**问题: 依赖版本冲突**

解决方案:
```bash
# 创建新环境
conda create -n llmrouter python=3.10
conda activate llmrouter

# 清理 pip 缓存
pip cache purge

# 重新安装
pip install -e . --no-cache-dir
```

### 获取帮助

如果以上解决方案无法解决您的问题：

1. 查看 [GitHub Issues](https://github.com/ulab-uiuc/LLMRouter/issues)
2. 查看详细文档:
   - [系统架构文档](docs/architecture/system_architecture.md)
   - [数据生成流程](docs/architecture/data_generation_flow.md)
   - [训练流程](docs/architecture/training_flow.md)
   - [推理流程](docs/architecture/inference_flow.md)
3. 加入社区:
   - [Slack](https://join.slack.com/t/llmrouteropen-ri04588/shared_invite/zt-3mkx82cut-A25v5yR52xVKi7_jm_YK_w)
   - [微信](https://github.com/ulab-uiuc/LLMRouter/issues/136)
4. 提交 Issue: [GitHub Issues](https://github.com/ulab-uiuc/LLMRouter/issues/new)

---

## 下一步

恭喜您完成了快速入门！以下是一些进阶主题：

- **自定义路由器**: [创建自定义路由器](custom_routers/README.md)
- **自定义任务**: [添加自定义任务](custom_tasks/README.md)
- **ComfyUI 界面**: [可视化工作流](ComfyUI/README.md)
- **OpenClaw 集成**: [生产环境部署](openclaw_router/README.md)
- **多模态支持**: [多模态任务](data/multimodal_tasks/README.md)

---

## 参考资源

- **项目主页**: https://github.com/ulab-uiuc/LLMRouter
- **在线文档**: https://ulab-uiuc.github.io/LLMRouter/
- **API 密钥申请**: https://build.nvidia.com/

---

祝您使用愉快！如有任何问题，欢迎随时提问。
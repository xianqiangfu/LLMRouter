# LLMRouter 开发环境搭建指南

本文档详细介绍了 LLMRouter 项目的开发环境配置、IDE 设置、调试技巧、代码规范和开发流程。

---

## 目录

- [1. 开发环境要求](#1-开发环境要求)
- [2. 环境配置](#2-环境配置)
- [3. IDE 配置](#3-ide-配置)
- [4. 调试技巧和工具](#4-调试技巧和工具)
- [5. 代码规范说明](#5-代码规范说明)
- [6. 测试环境配置](#6-测试环境配置)
- [7. 开发流程说明](#7-开发流程说明)
- [8. 常见开发问题](#8-常见开发问题)

---

## 1. 开发环境要求

### 1.1 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4 核 | 8 核及以上 |
| 内存 | 16 GB | 32 GB 及以上 |
| 存储 | 50 GB 可用空间 | 100 GB SSD |
| GPU | 无（仅开发） | NVIDIA GPU（训练/推理） |
| GPU 显存 | - | 8 GB 及以上 |

### 1.2 软件要求

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| 操作系统 | Linux/macOS/Windows | Linux/macOS 体验最佳 |
| Python | 3.10 或 3.11 | 主要开发版本 |
| Git | 2.0+ | 版本控制 |
| CUDA | 11.8+ | GPU 加速（可选） |
| Node.js | 18+ | ComfyUI 界面（可选） |

### 1.3 推荐的开发环境组合

**Linux/macOS 用户：**
- IDE: VS Code 或 PyCharm Professional
- Python 环境: Conda + venv
- 版本控制: Git + GitHub CLI
- 笔记工具: Jupyter Lab

**Windows 用户：**
- IDE: VS Code 或 PyCharm Professional
- Python 环境: Anaconda
- 终端: Windows Terminal (PowerShell 7+)
- WSL: Ubuntu (推荐用于完整开发体验)

---

## 2. 环境配置

### 2.1 克隆仓库

```bash
# 克隆主仓库
git clone https://github.com/ulab-uiuc/LLMRouter.git
cd LLMRouter

# 或者克隆您自己的 fork（用于贡献）
git clone https://github.com/YOUR_USERNAME/LLMRouter.git
cd LLMRouter
```

### 2.2 创建开发环境

#### 使用 Conda（推荐）

```bash
# 创建 Python 3.10 环境
conda create -n llmrouter-dev python=3.10 -y
conda activate llmrouter-dev

# 验证 Python 版本
python --version  # 应显示 Python 3.10.x
```

#### 使用 venv

```bash
# 创建虚拟环境
python3.10 -m venv llmrouter-dev

# 激活环境
# Linux/macOS:
source llmrouter-dev/bin/activate
# Windows:
llmrouter-dev\Scripts\activate
```

### 2.3 安装依赖

#### 基础安装

```bash
# 安装核心依赖（开发模式）
pip install -e .

# 或使用国内镜像加速
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 完整安装

```bash
# 安装所有依赖（包括 RouterR1）
pip install -e ".[all]"
```

#### 开发依赖安装

```bash
# 安装开发工具
pip install pytest pytest-cov black flake8 mypy isort pre-commit
pip install jupyter jupyterlab ipython
```

### 2.4 验证安装

```bash
# 检查 CLI 是否可用
llmrouter --help

# 列出所有路由器
llmrouter list-routers

# 检查 Python 包
python -c "import llmrouter; print(llmrouter.__version__)"
```

### 2.5 配置环境变量

创建 `.env` 文件或直接设置环境变量：

```bash
# API 密钥配置（推荐字典格式）
export API_KEYS='{"NVIDIA": "your-nvidia-key", "OpenAI": "your-openai-key"}'

# 或者创建 .env 文件
echo 'API_KEYS={"NVIDIA": "your-nvidia-key"}' > .env
```

**Windows (PowerShell):**
```powershell
$env:API_KEYS='{"NVIDIA": "your-nvidia-key"}'
```

### 2.6 使用 direnv 自动加载环境变量（推荐）

```bash
# 安装 direnv
# macOS: brew install direnv
# Linux: sudo apt install direnv

# 在项目根目录创建 .envrc 文件
cat > .envrc << 'EOF'
# 自动激活 conda 环境
use_conda llmrouter-dev

# 加载环境变量
export API_KEYS='your-api-key'
export CUDA_VISIBLE_DEVICES=0

# 设置 Python 路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
EOF

# 允许并加载
direnv allow
```

---

## 3. IDE 配置

### 3.1 VS Code 配置

#### 安装推荐扩展

创建 `.vscode/extensions.json`：

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "ms-python.debugpy",
    "donjayamanne.python-extension-pack",
    "eamodio.gitlens",
    "github.vscode-pull-request-github",
    "redhat.vscode-yaml",
    "stkb.rewrap",
    "usernamehw.errorlens",
    "ms-toolsai.jupyter"
  ]
}
```

#### VS Code 设置

创建 `.vscode/settings.json`：

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=100"],
  "python.sortImports.args": ["--profile", "black", "--line-length", "100"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "editor.rulers": [100],
  "editor.wordWrap": "wordWrapColumn",
  "editor.wordWrapColumn": 100,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true,
    "**/.coverage": true
  },
  "files.watcherExclude": {
    "**/__pycache__/**": true,
    "**/node_modules/**": true
  },
  "search.exclude": {
    "**/__pycache__": true,
    "**/node_modules": true,
    "**/*.egg-info": true
  },
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "python.testing.unittestEnabled": false
}
```

#### VS Code 调试配置

创建 `.vscode/launch.json`：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: 当前文件",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Python: 训练 KNN Router",
      "type": "debugpy",
      "request": "launch",
      "module": "llmrouter.cli.router_train",
      "args": [
        "--router", "knnrouter",
        "--config", "configs/model_config_train/knnrouter.yaml"
      ],
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Python: 推理测试",
      "type": "debugpy",
      "request": "launch",
      "module": "llmrouter.cli.router_inference",
      "args": [
        "--router", "knnrouter",
        "--config", "configs/model_config_test/knnrouter.yaml",
        "--query", "Hello"
      ],
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Python: 运行测试",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": [
        "tests/train_test/test_knnrouter.py",
        "-v",
        "-s"
      ],
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Python: 数据生成",
      "type": "debugpy",
      "request": "launch",
      "module": "llmrouter.data.data_generation",
      "args": [
        "--config", "llmrouter/data/sample_config.yaml"
      ],
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ]
}
```

#### VS Code 任务配置

创建 `.vscode/tasks.json`：

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "格式化代码",
      "type": "shell",
      "command": "black",
      "args": ["."],
      "problemMatcher": []
    },
    {
      "label": "排序导入",
      "type": "shell",
      "command": "isort",
      "args": ["."],
      "problemMatcher": []
    },
    {
      "label": "运行 Flake8 检查",
      "type": "shell",
      "command": "flake8",
      "args": ["llmrouter/", "--max-line-length=100"],
      "problemMatcher": []
    },
    {
      "label": "运行测试",
      "type": "shell",
      "command": "pytest",
      "args": ["-v", "tests/"],
      "problemMatcher": []
    },
    {
      "label": "运行测试并生成覆盖率",
      "type": "shell",
      "command": "pytest",
      "args": ["--cov=llmrouter", "--cov-report=html", "--cov-report=term", "tests/"],
      "problemMatcher": []
    },
    {
      "label": "安装开发依赖",
      "type": "shell",
      "command": "pip",
      "args": ["install", "-e", ".[all]", "-q"],
      "problemMatcher": []
    },
    {
      "label": "更新依赖",
      "type": "shell",
      "command": "pip",
      "args": ["install", "--upgrade", "-r", "requirements.txt"],
      "problemMatcher": []
    }
  ]
}
```

### 3.2 PyCharm 配置

#### 项目设置

1. 打开 PyCharm，选择 `File` -> `Open` -> 选择 LLMRouter 目录
2. 配置 Python 解释器：
   - `File` -> `Settings` -> `Project` -> `Python Interpreter`
   - 点击 `Add Interpreter` -> `Conda Environment`
   - 选择 `Existing environment`
   - 浏览到您的 conda 环境：`~/anaconda3/envs/llmrouter-dev/bin/python`

#### 代码风格设置

`File` -> `Settings` -> `Editor` -> `Code Style` -> `Python`：

```
缩进大小: 4
继续缩进大小: 8
Tab 大小: 4
行宽限制: 100
```

#### 启用 Black 格式化

`File` -> `Settings` -> `Tools` -> `External Tools`：

添加 Black 格式化工具：
- Name: `Black`
- Program: `$PyInterpreterDirectory$/black`
- Arguments: `$FilePath$`
- Working directory: `$ProjectFileDir$`

#### 运行配置

创建运行配置：

1. 点击 `Run` -> `Edit Configurations`
2. 点击 `+` 添加 `Python` 配置：

**训练 KNN Router:**
```
Script path: llmrouter/cli/router_train.py
Parameters: --router knnrouter --config configs/model_config_train/knnrouter.yaml
Working directory: $ProjectFileDir$
Environment: PYTHONPATH=$ProjectFileDir$
```

**运行测试:**
```
Target: Module name: pytest
Parameters: tests/train_test/test_knnrouter.py -v
Working directory: $ProjectFileDir$
```

#### 启用 pytest

`File` -> `Settings` -> `Tools` -> `Python Integrated Tools`：

```
Default test runner: pytest
```

### 3.3 Jupyter Notebook 配置

#### 启动 Jupyter Lab

```bash
# 安装 Jupyter Lab
pip install jupyterlab

# 启动 Jupyter Lab
jupyter lab

# 或指定端口
jupyter lab --port 8888 --no-browser
```

#### VS Code Jupyter 配置

在 VS Code 中：
1. 安装 `Jupyter` 扩展
2. 打开任何 `.ipynb` 文件
3. 选择正确的 Python 内核

#### 推荐的 Jupyter 扩展

```bash
pip install ipywidgets
pip install jupyter_contrib_nbextensions
jupyter contrib nbextension install --user
```

---

## 4. 调试技巧和工具

### 4.1 使用 pdb 调试

#### 基本调试命令

```python
import pdb; pdb.set_trace()

# 或者 Python 3.7+
breakpoint()
```

**常用 pdb 命令:**

| 命令 | 说明 |
|------|------|
| `n` (next) | 执行下一行（不进入函数） |
| `s` (step) | 执行下一行（进入函数） |
| `c` (continue) | 继续执行到下一个断点 |
| `l` (list) | 显示当前代码位置 |
| `p variable` | 打印变量值 |
| `pp variable` | 美化打印变量值 |
| `w` (where) | 显示调用栈 |
| `b line_number` | 设置断点 |
| `b function_name` | 在函数处设置断点 |
| `cl` | 清除断点 |
| `q` (quit) | 退出调试器 |

#### 高级 pdb 技巧

```python
# 条件断点
pdb.set_trace()  # 只在特定条件下中断
# 或在 pdb 中
(Pdb) b 50, x > 10  # 在第 50 行，当 x > 10 时中断

# 监视变量
(Pdb) display x  # 每次停止时显示 x

# 临时禁用断点
(Pdb) disable 1  # 禁用断点 1
(Pdb) enable 1   # 启用断点 1
```

### 4.2 使用 IPython 调试

```python
# 在 IPython 中
from IPython import embed
embed()

# 或者使用 ipdb
import ipdb; ipdb.set_trace()
```

### 4.3 VS Code 调试技巧

#### 断点类型

1. **普通断点**：点击行号左侧设置
2. **条件断点**：右键断点 -> 编辑断点 -> 输入条件
3. **日志断点**：右键行号 -> 添加日志点 -> 输入消息

**条件断点示例:**
```
x > 10
len(items) == 0
query.startswith("debug")
```

**日志断点示例:**
```
Processing query: {query}
Items count: {len(items)}
```

#### 调试控制台

在调试过程中使用调试控制台：

```python
# 在调试控制台中执行
>>> locals()  # 查看局部变量
>>> globals()  # 查看全局变量
>>> dir(obj)  # 查看对象属性
```

#### 调试配置优化

```json
{
  "justMyCode": false,  // 调试第三方代码
  "showReturnValue": true,  // 显示返回值
  "redirectOutput": true  // 重定向输出到调试控制台
}
```

### 4.4 PyCharm 调试技巧

#### 设置断点

- 点击行号左侧的灰色区域
- 右键断点设置条件
- 使用 `Ctrl+Shift+F8` 查看所有断点

#### 调试操作

| 快捷键 | 操作 |
|--------|------|
| `F8` | Step Over |
| `F7` | Step Into |
| `Shift+F8` | Step Out |
| `F9` | Resume Program |
| `Alt+F9` | Run to Cursor |

#### 评估表达式

- 在调试时选中表达式
- 按 `Alt+F8` 评估表达式
- 或使用 `Evaluate Expression` 窗口

### 4.5 性能分析

#### 使用 cProfile

```python
import cProfile
import pstats

def profile_function():
    pr = cProfile.Profile()
    pr.enable()

    # 您的代码
    your_function()

    pr.disable()
    stats = pstats.Stats(pr)
    stats.sort_stats('cumtime')
    stats.print_stats(10)
```

#### 使用 line_profiler

```bash
# 安装
pip install line_profiler

# 使用
kernprof -l -v your_script.py
```

#### 使用 memory_profiler

```bash
# 安装
pip install memory_profiler

# 在代码中
from memory_profiler import profile

@profile
def your_function():
    # 您的代码
    pass
```

#### 使用 PyTorch Profiler

```python
import torch
from torch.profiler import profile, record_function, ProfilerActivity

with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
    with record_function("model_inference"):
        model(input)

print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=10))
```

### 4.6 日志调试

#### 配置日志

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 使用日志
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

#### 在路由器中使用日志

```python
import logging

class KNNRouter(MetaRouter):
    def __init__(self, yaml_path: str):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initializing KNNRouter from {yaml_path}")
        super().__init__(yaml_path=yaml_path)

    def route_single(self, query_input: dict) -> dict:
        query = query_input['query']
        self.logger.debug(f"Routing query: {query[:50]}...")
        # 路由逻辑
        result = self._do_routing(query)
        self.logger.info(f"Routed to {result['model_name']}")
        return result
```

### 4.7 单元测试调试

#### 调试单个测试

```bash
# 使用 pytest 调试
pytest tests/train_test/test_knnrouter.py::test_knn_train -v -s

# 使用 pdb 调试
pytest tests/train_test/test_knnrouter.py::test_knn_train --pdb

# 只在失败时进入调试
pytest tests/train_test/test_knnrouter.py --pdb -x
```

#### 使用 IPython 调试测试

```bash
# 安装 pytest-ipdb
pip install pytest-ipdb

# 使用 IPython 调试
pytest tests/train_test/test_knnrouter.py --ipdb
```

---

## 5. 代码规范说明

### 5.1 命名规范

#### 文件命名

| 类型 | 命名风格 | 示例 |
|------|---------|------|
| Python 模块 | snake_case | `knnrouter.py`, `data_generation.py` |
| 包目录 | snake_case | `llmrouter/`, `custom_routers/` |
| 配置文件 | snake_case | `knnrouter.yaml`, `sample_config.yaml` |
| 数据文件 | snake_case | `query_data_train.jsonl` |
| 文档文件 | snake_case | `README.md`, `DEVELOPMENT.md` |

#### Python 代码命名

| 类型 | 命名风格 | 示例 |
|------|---------|------|
| 变量 | snake_case | `query_text`, `model_name`, `embedding_id` |
| 函数 | snake_case | `route_single()`, `get_embedding()`, `train_model()` |
| 类 | PascalCase | `KNNRouter`, `MetaRouter`, `LLMCandidate` |
| 常量 | UPPER_SNAKE_CASE | `MAX_TOKENS`, `DEFAULT_MODEL`, `API_ENDPOINT` |
| 私有成员 | _leading_underscore | `_internal_method()`, `_private_var` |
| 魔术方法 | __double_underscore__ | `__init__`, `__call__`, `__str__` |

**命名示例:**

```python
# 好的命名
def calculate_router_score(query_embedding: np.ndarray, model_embeddings: Dict[str, np.ndarray]) -> float:
    """计算路由器的匹配分数。"""
    pass

class RouterTrainer:
    """路由器训练器基类。"""
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.max_epochs = 100
        self._internal_state = {}

    def _prepare_data(self):
        """内部数据准备方法。"""
        pass

# 不好的命名
def calc_score(emb, mods):
    pass

class rt:
    def __init__(self, cp):
        pass
```

### 5.2 注释规范

#### 文档字符串（Docstrings）

使用 Google 风格的文档字符串：

```python
def route_single(self, query_input: dict) -> dict:
    """路由单个查询到最佳的 LLM 模型。

    Args:
        query_input: 包含查询信息的字典，必须包含 'query' 键。
                    可选包含 'history'、'context' 等额外信息。

    Returns:
        dict: 路由结果字典，包含：
            - query: 原始查询文本
            - model_name: 选择的模型名称
            - predicted_llm: 预测的 LLM 模型
            - confidence: 路由置信度（可选）

    Raises:
        ValueError: 当查询输入格式不正确时抛出
        KeyError: 当查询字典缺少必需键时抛出

    Example:
        >>> router = KNNRouter("config.yaml")
        >>> result = router.route_single({"query": "Hello"})
        >>> print(result['model_name'])
        'llama-3-8b'
    """
    pass
```

#### 行内注释

```python
# 计算查询与所有候选模型的相似度
similarities = self._compute_similarities(query_embedding, model_embeddings)

# 选择相似度最高的模型
best_model = max(similarities.items(), key=lambda x: x[1])

# 返回路由结果
return {
    "model_name": best_model[0],
    "confidence": best_model[1]
}

# TODO: 添加对多模态查询的支持
# FIXME: 处理空查询的情况
# NOTE: 这里的超参数需要根据数据集调整
```

#### 模块级注释

```python
"""KNN 路由器实现。

该模块实现了基于 K 近邻（K-Nearest Neighbors）的路由器，
用于根据查询的嵌入向量选择最合适的 LLM 模型。

主要功能：
- 支持多种距离度量（欧氏距离、余弦相似度等）
- 支持批量路由
- 支持训练数据缓存

参考论文：
    RouteLLM: Learning to Route LLMs with Preference Data
"""

import numpy as np
from sklearn.neighbors import NearestNeighbors
from typing import Dict, List, Optional
```

### 5.3 代码格式化

#### Black 配置

创建 `pyproject.toml`：

```toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
```

使用 Black 格式化：

```bash
# 格式化整个项目
black .

# 只检查不修改
black --check .

# 格式化特定文件
black llmrouter/models/knnrouter/knnrouter.py
```

#### isort 配置

```toml
[tool.isort]
profile = "black"
line_length = 100
known_first_party = ["llmrouter"]
```

使用 isort 排序导入：

```bash
# 排序整个项目的导入
isort .

# 只检查不修改
isort --check-only .
```

#### pre-commit 配置

创建 `.pre-commit-config.yaml`：

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--ignore=E203,W503']
```

安装和使用 pre-commit：

```bash
# 安装 pre-commit
pip install pre-commit

# 安装钩子
pre-commit install

# 手动运行所有钩子
pre-commit run --all-files

# 跳过某些钩子
pre-commit run --all-files --skip=flake8
```

### 5.4 Git 提交规范

#### 提交信息格式

使用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型（Type）:**

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加 GraphRouter 支持` |
| `fix` | Bug 修复 | `fix: 修复 KNN 路由器的内存泄漏` |
| `docs` | 文档更新 | `docs: 更新开发环境搭建指南` |
| `style` | 代码格式（不影响功能） | `style: 使用 Black 格式化代码` |
| `refactor` | 重构 | `refactor: 简化路由器基类` |
| `test` | 测试相关 | `test: 添加 MLP 路由器测试` |
| `chore` | 构建/工具 | `chore: 更新依赖版本` |
| `perf` | 性能优化 | `perf: 优化嵌入计算性能` |

**示例提交:**

```
feat(router): 添加自定义路由器插件系统

- 实现插件发现机制
- 支持从 ./custom_routers/ 和 ~/.llmrouter/plugins/ 加载路由器
- 添加示例路由器（RandomRouter 和 ThresholdRouter）

Closes #45
```

```
fix(knnrouter): 修复批量推理时的索引错误

当批量推理输入为空列表时，会引发 IndexError。
现在添加了输入验证和优雅的错误处理。

Fixes #78
```

#### .gitignore 配置

确保项目包含完整的 `.gitignore`：

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# 虚拟环境
venv/
env/
ENV/
env.bak/
venv.bak/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# 数据和模型
data/example_data/routing_data/*.jsonl
data/example_data/embeddings/*.pt
saved_models/
*.pkl
*.pth
*.bin

# 日志
*.log
logs/

# Jupyter Notebook
.ipynb_checkpoints
*.ipynb

# 测试
.pytest_cache/
.coverage
htmlcov/
.tox/
.mypy_cache/

# 环境变量
.env
.env.local

# OS
Thumbs.db
```

---

## 6. 测试环境配置

### 6.1 测试框架

LLMRouter 使用 pytest 作为测试框架。

#### 安装测试依赖

```bash
# 安装 pytest 和相关工具
pip install pytest pytest-cov pytest-mock pytest-timeout

# 安装覆盖率工具
pip install coverage[toml]
```

### 6.2 测试配置

#### pytest 配置

创建 `pytest.ini`：

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=llmrouter
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    gpu: marks tests that require GPU
    api: marks tests that require API keys
```

#### pytest-cov 配置

在 `pyproject.toml` 中添加：

```toml
[tool.coverage.run]
source = ["llmrouter"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__init__.py",
    "*/cli/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

### 6.3 测试组织

#### 测试目录结构

```
tests/
├── conftest.py              # pytest 配置和 fixtures
├── train_test/              # 训练测试
│   ├── test_knnrouter.py
│   ├── test_mlprouter.py
│   └── ...
├── inference_test/          # 推理测试
│   ├── test_knnrouter.py
│   ├── test_mlprouter.py
│   └── ...
├── data_test/               # 数据处理测试
│   ├── test_data_generation.py
│   └── test_embeddings.py
├── utils_test/              # 工具函数测试
│   └── test_api_calling.py
└── integration_test/        # 集成测试
    ├── test_full_pipeline.py
    └── test_openclaw_integration.py
```

#### conftest.py 配置

```python
import os
import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture(scope="session")
def project_root():
    """返回项目根目录。"""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """返回测试数据目录。"""
    return project_root / "data" / "example_data"

@pytest.fixture
def temp_dir():
    """创建临时目录，测试后自动清理。"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def mock_api_key():
    """模拟 API 密钥。"""
    old_key = os.environ.get("API_KEYS")
    os.environ["API_KEYS"] = "test-api-key-123"
    yield
    if old_key is None:
        os.environ.pop("API_KEYS", None)
    else:
        os.environ["API_KEYS"] = old_key

@pytest.fixture
def sample_query():
    """示例查询 fixture。"""
    return {"query": "What is machine learning?"}

@pytest.fixture
def sample_llm_data(test_data_dir):
    """示例 LLM 数据 fixture。"""
    import json
    llm_file = test_data_dir / "llm_candidates" / "default_llm.json"
    if llm_file.exists():
        with open(llm_file, 'r') as f:
            return json.load(f)
    return {}
```

### 6.4 编写测试

#### 单元测试示例

```python
import pytest
import numpy as np
from llmrouter.models import KNNRouter, KNNRouterTrainer

class TestKNNRouter:
    """KNN 路由器测试类。"""

    @pytest.fixture
    def router(self, test_data_dir):
        """创建 KNN 路由器实例。"""
        config_path = test_data_dir / "configs" / "knnrouter.yaml"
        return KNNRouter(str(config_path))

    def test_router_initialization(self, router):
        """测试路由器初始化。"""
        assert router is not None
        assert hasattr(router, 'model')
        assert hasattr(router, 'llm_names')

    def test_route_single(self, router, sample_query):
        """测试单个查询路由。"""
        result = router.route_single(sample_query)
        assert 'model_name' in result
        assert 'query' in result
        assert result['query'] == sample_query['query']

    def test_route_batch(self, router):
        """测试批量查询路由。"""
        queries = [
            {"query": f"Query {i}"} for i in range(5)
        ]
        results = router.route_batch(queries)
        assert len(results) == len(queries)
        for result in results:
            assert 'model_name' in result

    @pytest.mark.parametrize("k", [1, 3, 5, 10])
    def test_different_k_values(self, router, k):
        """测试不同的 k 值。"""
        # 修改 k 值并测试
        old_k = router.model.n_neighbors
        router.model.n_neighbors = k
        result = router.route_single({"query": "Test"})
        assert result is not None
        router.model.n_neighbors = old_k  # 恢复原值

    def test_empty_query(self, router):
        """测试空查询处理。"""
        with pytest.raises(ValueError):
            router.route_single({"query": ""})

    @pytest.mark.slow
    def test_large_batch_routing(self, router):
        """测试大批量路由（标记为慢速测试）。"""
        queries = [{"query": f"Query {i}"} for i in range(1000)]
        results = router.route_batch(queries)
        assert len(results) == 1000
```

#### 训练测试示例

```python
import pytest
from llmrouter.models import KNNRouter, KNNRouterTrainer

class TestKNNRouterTrainer:
    """KNN 路由器训练器测试类。"""

    @pytest.fixture
    def trainer(self, router):
        """创建训练器实例。"""
        return KNNRouterTrainer(router=router, device="cpu")

    def test_trainer_initialization(self, trainer):
        """测试训练器初始化。"""
        assert trainer is not None
        assert trainer.device == "cpu"

    def test_train(self, trainer, temp_dir):
        """测试训练过程。"""
        # 修改保存路径到临时目录
        trainer.save_model_path = str(temp_dir / "model.pkl")

        # 运行训练
        trainer.train()

        # 验证模型已保存
        assert (temp_dir / "model.pkl").exists()

    @pytest.mark.gpu
    def test_train_with_gpu(self, router):
        """测试 GPU 训练（需要 GPU）。"""
        trainer = KNNRouterTrainer(router=router, device="cuda")
        trainer.train()

    @pytest.mark.integration
    def test_full_training_pipeline(self, router, temp_dir):
        """测试完整训练流水线（集成测试）。"""
        trainer = KNNRouterTrainer(router=router, device="cpu")
        trainer.save_model_path = str(temp_dir / "model.pkl")
        trainer.train()

        # 加载模型并进行推理
        trained_router = KNNRouter(router.yaml_path)
        trained_router.load_model(trainer.save_model_path)
        result = trained_router.route_single({"query": "Test"})
        assert result is not None
```

### 6.5 运行测试

#### 基本测试命令

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/train_test/test_knnrouter.py

# 运行特定测试函数
pytest tests/train_test/test_knnrouter.py::TestKNNRouter::test_route_single

# 运行标记为慢速的测试
pytest -m slow

# 并行运行测试
pytest -n auto

# 显示详细输出
pytest -v -s

# 只运行失败的测试
pytest --lf

# 第一次失败后停止
pytest -x

# 显示测试覆盖率
pytest --cov=llmrouter --cov-report=term
```

#### 生成覆盖率报告

```bash
# 生成 HTML 覆盖率报告
pytest --cov=llmrouter --cov-report=html

# 查看报告
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux

# 生成 XML 报告（用于 CI/CD）
pytest --cov=llmrouter --cov-report=xml
```

### 6.6 测试最佳实践

1. **保持测试独立性**：每个测试应该独立运行，不依赖其他测试
2. **使用 fixtures**：复用测试数据和配置
3. **描述性命名**：测试名称应该清晰描述测试内容
4. **测试边界情况**：包括空输入、极端值等
5. **使用 mock**：模拟外部依赖（API 调用、文件 I/O）
6. **保持测试快速**：将慢速测试标记为 `@pytest.mark.slow`

---

## 7. 开发流程说明

### 7.1 分支策略

#### 主要分支

| 分支 | 用途 | 说明 |
|------|------|------|
| `main` | 主分支 | 稳定的发布版本 |
| `develop` | 开发分支 | 最新开发功能 |
| `feature/*` | 功能分支 | 开发新功能 |
| `fix/*` | 修复分支 | 修复 bug |
| `release/*` | 发布分支 | 准备发布 |
| `hotfix/*` | 热修复分支 | 紧急修复 |

#### 分支工作流

```
1. 从 main 分支创建功能分支
   git checkout main
   git pull origin main
   git checkout -b feature/add-new-router

2. 开发和提交
   git add .
   git commit -m "feat: 添加新的路由器实现"

3. 推送到远程
   git push origin feature/add-new-router

4. 创建 Pull Request
   在 GitHub 上创建 PR，请求合并到 main

5. 代码审查
   团队成员审查代码，提出修改建议

6. 修改和完善
   根据反馈修改代码

7. 合并
   审查通过后合并到 main

8. 删除功能分支
   git branch -d feature/add-new-router
   git push origin --delete feature/add-new-router
```

### 7.2 开发工作流

#### 开发新功能

```bash
# 1. 更新主分支
git checkout main
git pull origin main

# 2. 创建功能分支
git checkout -b feature/your-feature-name

# 3. 进行开发
# - 编写代码
# - 添加测试
# - 更新文档

# 4. 运行测试
pytest tests/
pytest --cov=llmrouter

# 5. 代码格式化
black .
isort .
flake8 llmrouter/

# 6. 提交代码
git add .
git commit -m "feat: 添加新功能描述

详细说明功能实现的内容和目的。
"

# 7. 推送并创建 PR
git push origin feature/your-feature-name
# 在 GitHub 上创建 PR
```

#### 修复 Bug

```bash
# 1. 更新主分支
git checkout main
git pull origin main

# 2. 创建修复分支
git checkout -b fix/bug-description

# 3. 修复问题
# - 定位问题
# - 编写测试用例（确保测试失败）
# - 修复代码
# - 验证测试通过

# 4. 运行相关测试
pytest tests/related_tests/
pytest --cov=llmrouter

# 5. 提交修复
git add .
git commit -m "fix: 修复具体 bug 描述

修复了 [问题 A] 和 [问题 B]。
添加了测试用例确保不再出现此问题。

Fixes #123
"

# 6. 推送并创建 PR
git push origin fix/bug-description
```

### 7.3 代码审查清单

在提交 PR 之前，确保：

- [ ] 代码符合项目规范（PEP 8）
- [ ] 通过所有现有测试
- [ ] 添加了新功能的测试
- [ ] 测试覆盖率没有显著下降
- [ ] 更新了相关文档
- [ ] 提交信息清晰且符合规范
- [ ] 没有调试代码或 TODO 注释
- [ ] 没有敏感信息（API 密钥、密码等）
- [ ] 代码易于理解和维护

### 7.4 发布流程

#### 准备发布

```bash
# 1. 更新版本号
# 编辑 pyproject.toml 中的 version 字段
# 例如: version = "0.3.1" -> version = "0.3.2"

# 2. 更新 CHANGELOG.md
# 添加新版本的变更内容

# 3. 创建发布分支
git checkout main
git pull origin main
git checkout -b release/v0.3.2

# 4. 运行完整测试
pytest --cov=llmrouter
pytest -m integration
pytest -m slow

# 5. 构建包
python -m build

# 6. 提交发布
git add .
git commit -m "chore: 准备 v0.3.2 发布"
git push origin release/v0.3.2
```

#### 发布到 PyPI

```bash
# 1. 安装发布工具
pip install build twine

# 2. 构建包
python -m build

# 3. 检查包
twine check dist/*

# 4. 上传到测试 PyPI（可选）
twine upload --repository testpypi dist/*

# 5. 上传到 PyPI
twine upload dist/*

# 6. 在 GitHub 上创建 Release
# - 前往 GitHub Releases 页面
# - 创建新标签 v0.3.2
# - 添加发布说明
# - 上传构建的包
```

### 7.5 持续集成

#### GitHub Actions 配置

项目已配置 GitHub Actions，自动运行测试和检查。

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[all]"
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest --cov=llmrouter --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## 8. 常见开发问题

### 8.1 导入错误

**问题**: `ModuleNotFoundError: No module named 'llmrouter'`

**解决方案**:
```bash
# 确保以可编辑模式安装
pip install -e .

# 或设置 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 8.2 CUDA 相关问题

**问题**: `CUDA out of memory`

**解决方案**:
```bash
# 使用 CPU
CUDA_VISIBLE_DEVICES="" llmrouter train --router knnrouter --config config.yaml

# 或减小批次大小
# 编辑配置文件，减小 batch_size
```

**问题**: `RuntimeError: CUDA error: no kernel image is available`

**解决方案**:
```bash
# 检查 CUDA 版本
nvidia-smi

# 安装兼容的 PyTorch 版本
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### 8.3 依赖冲突

**问题**: 依赖版本冲突

**解决方案**:
```bash
# 创建新的虚拟环境
conda create -n llmrouter-dev python=3.10
conda activate llmrouter-dev

# 清理 pip 缓存
pip cache purge

# 重新安装
pip install -e ".[all]" --no-cache-dir
```

### 8.4 测试失败

**问题**: 测试失败但本地通过

**解决方案**:
```bash
# 清理测试缓存
pytest --cache-clear

# 使用隔离环境
pytest --create-db

# 检查环境变量
echo $API_KEYS
echo $PYTHONPATH
```

### 8.5 Git 相关问题

**问题**: 合并冲突

**解决方案**:
```bash
# 拉取最新代码
git fetch origin
git rebase origin/main

# 解决冲突
# 编辑冲突文件
git add .
git rebase --continue
```

---

## 附录

### A. 有用的开发工具

| 工具 | 用途 | 安装 |
|------|------|------|
| `black` | 代码格式化 | `pip install black` |
| `isort` | 导入排序 | `pip install isort` |
| `flake8` | 代码检查 | `pip install flake8` |
| `mypy` | 类型检查 | `pip install mypy` |
| `pytest` | 测试框架 | `pip install pytest` |
| `pytest-cov` | 测试覆盖率 | `pip install pytest-cov` |
| `pre-commit` | Git 钩子 | `pip install pre-commit` |
| `ipython` | 增强交互式 Python | `pip install ipython` |
| `jupyterlab` | 交互式笔记本 | `pip install jupyterlab` |
| `tox` | 多环境测试 | `pip install tox` |

### B. 快捷键参考

#### VS Code 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+P` | 快速打开文件 |
| `Ctrl+Shift+F` | 全局搜索 |
| `Ctrl+`` | 打开终端 |
| `F5` | 开始调试 |
| `Ctrl+Shift+D` | 打开调试视图 |
| `Ctrl+Shift+X` | 打开扩展视图 |

#### PyCharm 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+N` | 查找类 |
| `Ctrl+Shift+N` | 查找文件 |
| `Ctrl+Shift+F` | 全局搜索 |
| `Alt+F12` | 打开终端 |
| `Shift+F9` | 开始调试 |
| `Shift+F10` | 运行当前文件 |

---

**文档版本**: 1.0.0
**最后更新**: 2026-05-15
**维护者**: LLMRouter 开发团队

如有问题或建议，请通过 [GitHub Issues](https://github.com/ulab-uiuc/LLMRouter/issues) 反馈。
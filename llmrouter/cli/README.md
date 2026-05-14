# LLMRouter CLI 命令行工具

LLMRouter 提供了统一的命令行界面(CLI)，用于训练路由器、执行推理、启动聊天界面和管理可用路由器。

## 目录

- [命令结构](#命令结构)
- [命令列表](#命令列表)
- [命令执行流程](#命令执行流程)
- [详细用法](#详细用法)

---

## 命令结构

LLMRouter CLI 采用子命令结构：

```bash
llmrouter <子命令> [参数]
```

### 可用子命令

| 子命令 | 功能 |
|--------|------|
| `train` | 训练路由器模型 |
| `infer` | 使用训练好的路由器进行推理 |
| `chat` | 启动交互式聊天界面 |
| `serve` | 启动OpenAI兼容的API服务器 |
| `list-routers` | 列出所有可用的路由器 |
| `version` | 显示版本信息 |

### 获取帮助

```bash
# 查看主帮助
llmrouter --help

# 查看特定子命令帮助
llmrouter <子命令> --help
```

---

## 命令列表

### 1. train - 训练路由器

训练指定的路由器模型。

#### 参数

| 参数 | 必需 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--router` | 是 | string | - | 路由器方法名称（如 knnrouter、mlprouter） |
| `--config` | 是 | string | - | 训练配置文件的路径（YAML格式） |
| `--device` | 否 | string | auto | 训练设备（cuda/cpu/auto） |
| `--quiet` | 否 | flag | False | 静默模式，不输出详细日志 |

#### 支持的路由器

- `knnrouter` - K近邻路由器
- `svmrouter` - 支持向量机路由器
- `mlprouter` - 多层感知机路由器
- `mfrouter` - 矩阵分解路由器
- `elorouter` - Elo评分路由器
- `dcrouter` - 分治路由器
- `automix` - Automix路由器
- `hybrid_llm` - 混合LLM路由器
- `graphrouter` - 图路由器
- `causallm_router` - 因果语言模型路由器
- `knnmultiroundrouter` - KNN多轮路由器
- `gmtrouter` - GMT路由器
- `personalizedrouter` - 个性化路由器

#### 示例

```bash
# 训练KNN路由器
llmrouter train --router knnrouter --config configs/model_config_train/knnrouter.yaml

# 使用GPU训练MLP路由器
llmrouter train --router mlprouter --config configs/model_config_train/mlprouter.yaml --device cuda

# 静默模式训练
llmrouter train --router mfrouter --config configs/model_config_train/mfrouter.yaml --quiet
```

---

### 2. infer - 推理

使用训练好的路由器进行推理，支持单条查询和批量查询。

#### 参数

| 参数 | 必需 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--router` | 是 | string | - | 路由器方法名称 |
| `--config` | 是 | string | - | 配置文件路径（YAML格式） |
| `--query` | 否* | string | - | 单条查询字符串 |
| `--input` | 否* | string | - | 输入文件路径（支持.txt、.json、.jsonl） |
| `--load_model_path` | 否 | string | - | 覆盖配置文件中的模型加载路径 |
| `--route-only` | 否 | flag | False | 仅执行路由，不调用API |
| `--output` | 否 | string | - | 输出文件路径（默认输出到stdout） |
| `--output-format` | 否 | string | json | 输出格式（json/jsonl） |
| `--temp` | 否 | float | 0.8 | 文本生成温度 |
| `--max-tokens` | 否 | int | 1024 | 最大生成token数 |
| `--verbose` | 否 | flag | False | 输出详细日志 |

*注：`--query` 和 `--input` 必须二选一

#### 输入文件格式

支持以下格式：

1. **纯文本文件**（.txt）：每行一个查询
2. **JSON文件**（.json）：
   - 字符串列表：`["query1", "query2", ...]`
   - 字典列表：`[{"query": "query1"}, {"query": "query2"}, ...]`
3. **JSONL文件**（.jsonl）：每行一个JSON对象
   - `{"query": "query1"}`
   - `"query1"`（字符串）

#### 示例

```bash
# 单条查询推理
llmrouter infer --router knnrouter --config config.yaml --query "什么是人工智能？"

# 从文件批量推理
llmrouter infer --router knnrouter --config config.yaml --input queries.txt --output results.json

# 仅路由（不调用API）
llmrouter infer --router knnrouter --config config.yaml --query "Hello" --route-only

# 自定义生成参数
llmrouter infer --router knnrouter --config config.yaml --query "解释机器学习" --temp 0.5 --max-tokens 2048

# JSONL格式输出
llmrouter infer --router knnrouter --config config.yaml --input queries.jsonl --output results.jsonl --output-format jsonl
```

---

### 3. chat - 聊天界面

启动基于Gradio的交互式聊天界面。

#### 参数

| 参数 | 必需 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--router` | 是 | string | - | 路由器方法名称 |
| `--config` | 是 | string | - | 配置文件路径（YAML格式） |
| `--load_model_path` | 否 | string | - | 覆盖配置文件中的模型加载路径 |
| `--temp` | 否 | float | 0.8 | 默认文本生成温度 |
| `--host` | 否 | string | - | 服务器绑定的主机（默认所有接口） |
| `--port` | 否 | int | 8001 | 服务器绑定的端口 |
| `--mode` | 否 | string | current_only | 查询模式（full_context/current_only/retrieval） |
| `--top_k` | 否 | int | 3 | 检索模式下检索的相似查询数 |
| `--share` | 否 | flag | False | 创建公共可分享链接 |

#### 查询模式说明

- **full_context**：包含所有历史对话上下文 + 当前查询
- **current_only**：仅使用当前查询（默认）
- **retrieval**：从历史对话中检索top-k条相似查询 + 当前查询

#### 示例

```bash
# 启动基本聊天界面
llmrouter chat --router knnrouter --config config.yaml

# 使用完整上下文模式
llmrouter chat --router knnrouter --config config.yaml --mode full_context

# 使用检索模式
llmrouter chat --router knnrouter --config config.yaml --mode retrieval --top_k 5

# 创建公共分享链接
llmrouter chat --router knnrouter --config config.yaml --share

# 自定义端口和主机
llmrouter chat --router knnrouter --config config.yaml --host 0.0.0.0 --port 9000
```

---

### 4. serve - API服务

启动OpenAI兼容的API服务器，支持内置路由策略和LLMRouter ML路由器。

#### 参数

| 参数 | 必需 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--config` | 否 | string | - | OpenClaw配置文件路径（YAML格式） |
| `--host` | 否 | string | 0.0.0.0 | 服务器绑定的主机 |
| `--port` | 否 | int | 8000 | 服务器绑定的端口 |
| `--router` | 否 | string | - | 使用的路由器（如knnrouter、mlprouter） |
| `--router-config` | 否 | string | - | 路由器特定配置文件路径 |
| `--no-prefix` | 否 | flag | False | 在响应中禁用模型名称前缀 |

#### 路由策略

**内置策略**（在配置文件中设置）：
- `random`：随机模型选择（可选权重）
- `round_robin`：轮询模型
- `rules`：基于关键词的路由
- `llm`：使用LLM进行路由决策

**LLMRouter ML路由器**（使用 `--router` 参数或设置 `strategy: llmrouter`）：
- `knnrouter`、`mlprouter`、`svmrouter`、`mfrouter`
- `thresholdrouter`、`randomrouter`（来自custom_routers/）
- 以及更多...

#### OpenClaw集成

在 `~/.openclaw/openclaw.json` 中添加：

```json
{
  "models": {
    "providers": {
      "openclaw": {
        "api": "openai-completions",
        "baseUrl": "http://localhost:8000/v1",
        "apiKey": "not-needed",
        "models": [{"id": "auto", "name": "OpenClaw Router"}]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {"primary": "openclaw/auto"}
    }
  }
}
```

#### 示例

```bash
# 使用配置文件启动
llmrouter serve --config configs/openclaw_example.yaml

# 使用特定的LLMRouter ML路由器
llmrouter serve --config config.yaml --router knnrouter --router-config configs/knnrouter.yaml

# 自定义端口
llmrouter serve --config config.yaml --port 9000

# 禁用模型名称前缀
llmrouter serve --config config.yaml --no-prefix
```

---

### 5. list-routers - 列出路由器

列出所有可用的路由器及其训练能力。

#### 参数

无参数。

#### 输出说明

输出分为三部分：
1. **推理可用的路由器**：所有可用于推理的路由器
2. **训练可用的路由器**：支持训练的路由器及其训练器
3. **不支持训练的路由器**：无法训练的路由器及原因

#### 示例

```bash
# 列出所有路由器
llmrouter list-routers
```

---

### 6. version - 版本信息

显示LLMRouter的版本信息。

#### 参数

无参数。

#### 示例

```bash
# 显示版本
llmrouter version
```

---

## 命令执行流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        LLMRouter CLI                            │
│                   (llmrouter <命令> <参数>)                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │   参数解析与验证      │
                └───────────┬───────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    train    │    │    infer    │    │    chat     │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 加载配置    │    │ 加载配置    │    │ 加载配置    │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 初始化路由器│    │ 初始化路由器│    │ 初始化路由器│
│ 和训练器    │    │              │    │              │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 执行训练    │    │ 加载查询    │    │ 启动Gradio  │
│              │    │              │    │ 界面        │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 保存模型    │    │ 路由查询    │    │ 等待用户输入 │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
                          ▼                  │
                 ┌─────────────┐              │
                 │ 调用模型API │              │
                 └──────┬──────┘              │
                        │                     │
                        ▼                     │
                 ┌─────────────┐              │
                 │ 输出结果    │              │
                 └──────┬──────┘              │
                        │                     │
        ┌───────────────┼───────────────┐    │
        │               │               │    │
        ▼               ▼               ▼    ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  serve      │ │ list-routers│ │  version    │ │  (持续交互) │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │              │
       ▼               ▼               ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ 加载OpenClaw│ │ 遍历注册表  │ │ 读取版本    │ │ 准备查询    │
│ 配置        │ │              │ │              │ │              │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │              │
       ▼               ▼               ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ 创建FastAPI │ │ 输出推理路由│ │ 显示版本号  │ │ 路由查询    │
│ 应用        │ │              │ │              │ │              │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │              │
       ▼               ▼               │              ▼
┌─────────────┐ ┌─────────────┐         │    ┌─────────────┐
│ 启动服务器  │ │ 输出训练路由│         │    │ 调用模型API │
│              │ │              │         │    │              │
└──────┬──────┘ └─────────────┘         │    └──────┬──────┘
       │                                 │           │
       ▼                                 │           ▼
┌─────────────┐                          │    ┌─────────────┐
│ 等待API请求 │                          │    │ 返回响应    │
│              │                          │    │              │
└─────────────┘                          │    └─────────────┘
                                        │           │
                                        └───────────┘
                                            │
                                            ▼
                                    ┌─────────────┐
                                    │  (循环等待)  │
                                    └─────────────┘
```

---

## 详细用法

### 常见工作流程

#### 1. 训练新路由器

```bash
# 1. 准备配置文件
# 2. 训练路由器
llmrouter train --router knnrouter --config configs/model_config_train/knnrouter.yaml --device cuda

# 3. 验证训练结果
llmrouter list-routers
```

#### 2. 单次推理

```bash
# 使用训练好的路由器进行推理
llmrouter infer --router knnrouter --config config.yaml --query "解释深度学习"
```

#### 3. 批量处理

```bash
# 准备输入文件 queries.txt
# 每行一个查询

# 批量推理
llmrouter infer --router knnrouter --config config.yaml \
  --input queries.txt \
  --output results.json \
  --output-format jsonl \
  --verbose
```

#### 4. 交互式对话

```bash
# 启动聊天界面
llmrouter chat --router knnrouter --config config.yaml --port 8001

# 访问 http://localhost:8001 开始对话
```

#### 5. 部署API服务

```bash
# 启动OpenAI兼容的API服务
llmrouter serve --config configs/openclaw_example.yaml --port 8000

# 使用OpenAI SDK调用
# API endpoint: http://localhost:8000/v1
```

### 配置文件说明

所有命令都需要YAML格式的配置文件。配置文件通常包含：

- **模型路径**：训练好的路由器模型位置
- **API端点**：底层LLM模型的API地址
- **模型数据**：可用模型列表及其配置
- **超参数**：路由器特定的训练/推理参数

### 插件系统

LLMRouter支持插件系统，可以自动发现和注册自定义路由器：

- 插件目录：`custom_routers/`
- 自定义路由器会自动注册到可用路由器列表中
- 使用 `list-routers` 命令查看所有可用路由器（包括插件）

---

## 故障排查

### 常见问题

1. **导入错误**：确保所有依赖已正确安装
   ```bash
   pip install -r requirements.txt
   ```

2. **配置文件未找到**：检查配置文件路径是否正确
   ```bash
   llmrouter train --router knnrouter --config /full/path/to/config.yaml
   ```

3. **路由器不支持训练**：某些路由器（如SmallestLLM、LargestLLM）不支持训练，仅可用于推理

4. **API调用失败**：检查配置文件中的API端点是否正确配置

### 调试模式

使用 `--verbose` 参数获取详细日志：

```bash
llmrouter infer --router knnrouter --config config.yaml --query "test" --verbose
```

---

## 相关链接

- [主README](../../README.md)
- [模型文档](../models/)
- [配置示例](../../configs/)
- [自定义路由器](../../custom_routers/)
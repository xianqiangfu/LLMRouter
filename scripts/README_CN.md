# Scripts 目录说明文档

本目录包含用于 LLMRouter 项目的实用脚本，主要涵盖部署、测试和工具类功能。

## 目录作用

`scripts/` 目录存放了项目的 Shell 脚本工具，主要用于：

- 启动和停止 OpenClaw Router 及 OpenClaw Gateway 服务
- 分析 OpenCode 会话的 token 使用情况
- 简化项目的部署和管理流程

## 脚本文件列表及功能

### 1. start-openclaw.sh

启动 OpenClaw Router 和 OpenClaw Gateway 服务的部署脚本。支持 26+ 种路由策略，可灵活配置端口、路由器类型等参数。

**功能特性**：
- 自动检查端口占用并处理冲突
- 支持多种 ML 路由器和高级路由策略
- 彩色输出和状态提示
- 日志记录和实时监控
- 优雅的进程管理（支持 Ctrl+C 停止）

**可用选项**：
| 选项 | 说明 |
|------|------|
| `-c, --config FILE` | 指定配置文件路径（默认：`openclaw_router/config.yaml`）|
| `-p, --port PORT` | 指定 Router 端口（默认：`8000`）|
| `-r, --router NAME` | 使用指定的路由器 |
| `--router-config FILE` | 路由器配置文件路径 |
| `--no-gateway` | 不启动 OpenClaw Gateway |
| `--no-prefix` | 不在响应中添加模型名称前缀 |
| `--list-routers` | 列出所有可用的路由器 |
| `-h, --help` | 显示帮助信息 |

**支持的路由器（26+）**：
- **内置策略**：`random`、`round_robin`、`rules`、`llm`
- **ML 路由器**：`knrouter`、`mlprouter`、`svmrouter`、`mfrouter`、`elorouter`、`dcrouter`
- **高级路由器**：`graphrouter`、`gmtrouter`、`causallmrouter`、`personalizedrouter`
- **多轮路由器**：`knnmultiroundrouter`、`llmmultiroundrouter`
- **混合路由器**：`hybridllm`、`automixrouter`、`routerdc`、`router_r1`
- **简单选择**：`randomrouter`、`thresholdrouter`、`largest_llm`、`smallest_llm`

### 2. stop-openclaw.sh

停止 OpenClaw Router 和 OpenClaw Gateway 服务的脚本。

**功能特性**：
- 安全终止相关进程
- 彩色状态输出
- 优雅的服务关闭

### 3. print_session_tokens.sh

用于导出 OpenCode 会话并解析 token 使用情况的工具脚本。该脚本将会话导出为 JSON 文件，然后解析其中的 token 使用统计信息并以表格形式展示。

**功能特性**：
- 支持按代理（Agent）分组统计
- 支持按消息（Message）明细统计
- 支持缓存 token 统计（cache_read、cache_write）
- 自动清理 ANSI 转义序列
- JSON 数据验证和处理

**可用选项**：
| 选项 | 说明 |
|------|------|
| `--show-cache` | 在输出表格中包含缓存 token 列 |
| `--show-messages` | 在代理摘要之前显示每条消息的 token 表格 |
| `-h, --help` | 显示帮助信息 |

## 依赖和执行环境

### 系统要求

- **操作系统**：Linux、macOS 或 Windows（使用 Git Bash / WSL）
- **Shell**：Bash（脚本使用 Bash 语法）

### 软件依赖

#### 所有脚本通用依赖

| 依赖 | 说明 | 安装命令 |
|------|------|----------|
| Python 3.8+ | 运行 LLMRouter 服务 | [官网下载](https://www.python.org/) |
| pip | Python 包管理器 | 随 Python 安装 |

#### start-openclaw.sh / stop-openclaw.sh 额外依赖

| 依赖 | 说明 | 安装命令 |
|------|------|----------|
| curl | HTTP 请求测试 | `sudo apt install curl` (Linux) / `brew install curl` (macOS) |
| lsof / ss / netstat | 端口检查工具 | 系统自带 |
| OpenClaw CLI | Gateway 服务（可选）| `npm install -g openclaw` |

#### print_session_tokens.sh 额外依赖

| 依赖 | 说明 | 安装命令 |
|------|------|----------|
| jq | JSON 处理工具 | `sudo apt install jq` (Linux) / `brew install jq` (macOS) |
| column | 表格格式化工具 | 系统自带（util-linux 包）|
| OpenCode CLI | OpenCode 会话导出 | 见 [OpenCode 文档](https://docs.opencode.com/) |

### Python 依赖

启动 Router 服务需要安装 LLMRouter 的 Python 依赖：

```bash
pip install -r requirements.txt
```

## 使用示例

### 启动服务

```bash
# 使用默认配置启动
./scripts/start-openclaw.sh

# 使用 LLM 路由策略
./scripts/start-openclaw.sh -r llm

# 使用 KNN Router
./scripts/start-openclaw.sh -r knnrouter

# 在端口 9000 上使用 Random Router
./scripts/start-openclaw.sh -r randomrouter -p 9000

# 仅启动 Router，不启动 Gateway
./scripts/start-openclaw.sh --no-gateway

# 使用自定义配置
./scripts/start-openclaw.sh -c my_config.yaml -r mlprouter

# 列出所有可用路由器
./scripts/start-openclaw.sh --list-routers
```

### 停止服务

```bash
# 停止所有 OpenClaw 服务
./scripts/stop-openclaw.sh
```

输出示例：
```
============================================================
  Stopping OpenClaw Router + OpenClaw Gateway
============================================================

Stopping OpenClaw Router... OK
Stopping OpenClaw Gateway... OK

All services stopped
```

### 分析 Token 使用

```bash
# 显示会话的 token 使用摘要（按代理分组）
./scripts/print_session_tokens.sh session-abc123

# 显示包含缓存 token 的详细统计
./scripts/print_session_tokens.sh --show-cache session-abc123

# 显示每条消息的 token 使用详情
./scripts/print_session_tokens.sh --show-messages session-abc123

# 同时显示消息详情和缓存统计
./scripts/print_session_tokens.sh --show-cache --show-messages session-abc123
```

输出示例：
```
Agent Summary
agent      count  total   input   output  reasoning  cache_read  cache_write
claude     25     150000  75000   60000   15000      30000       5000
user       12     8000    8000    0       0          0           0
TOTAL      37     158000  83000   60000   15000      30000       5000
```

## 脚本使用注意事项

1. **执行权限**：确保脚本具有执行权限
   ```bash
   chmod +x scripts/*.sh
   ```

2. **Windows 用户**：建议使用 Git Bash 或 WSL 运行脚本

3. **启动前检查**：
   - 已安装 Python 和必要的依赖
   - 配置文件（`config.yaml`）存在且配置正确
   - 如果需要使用 OpenClaw Gateway，需先安装 OpenClaw CLI

4. **日志位置**：
   - OpenClaw Router 日志：`/tmp/openclaw.log`
   - OpenClaw Gateway 日志：`/tmp/openclaw-gateway.log`

5. **端口配置**：
   - Router 默认端口：`8000`
   - Gateway 默认端口：`18789`
   - 确保端口未被其他进程占用

## 故障排除

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 端口占用 | 旧服务未正常停止 | 使用 `stop-openclaw.sh` 或手动终止进程 |
| 配置文件未找到 | 路径错误 | 检查 `-c` 参数指定的配置文件路径 |
| Python 命令失败 | 依赖未安装 | 运行 `pip install -r requirements.txt` |
| OpenClaw Gateway 启动失败 | CLI 未安装或配置错误 | 运行 `npm install -g openclaw` 并检查配置 |
| jq 命令未找到 | print_session_tokens 依赖缺失 | 安装 jq 工具 |

## 相关文档

- [OpenClaw Router README](../openclaw_router/README_CN.md) - OpenClaw Router 详细文档
- [项目主 README](../README.md) - 项目总览文档
- [GitHub Issues](https://github.com/your-repo/llmrouter/issues) - 问题追踪
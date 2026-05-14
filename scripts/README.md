# Scripts 目录说明

本目录包含用于 LLMRouter 项目的实用脚本，主要涵盖部署、测试和工具类功能。

## 脚本列表

### 1. start-openclaw.sh

**功能说明**：
用于启动 OpenClaw Router 和 OpenClaw Gateway 服务的部署脚本。支持多种路由策略，可以配置端口、路由器类型等参数。

**用法**：
```bash
./scripts/start-openclaw.sh [选项]
```

**可用选项**：
- `-c, --config FILE` - 指定配置文件路径（默认：openclaw_router/config.yaml）
- `-p, --port PORT` - 指定 Router 端口（默认：8000）
- `-r, --router NAME` - 使用指定的路由器（如 knnrouter, mlprouter, randomrouter）
- `--router-config FILE` - 路由器配置文件路径
- `--no-gateway` - 不启动 OpenClaw Gateway
- `--no-prefix` - 不在响应中添加模型名称前缀
- `--list-routers` - 列出所有可用的路由器
- `-h, --help` - 显示帮助信息

**支持的路由器（26+）**：
- **内置策略**：random, round_robin, rules, llm
- **ML 路由器**：knrouter, mlprouter, svmrouter, mfrouter, elorouter, dcrouter
- **高级路由器**：graphrouter, gmtrouter, causallmrouter, personalizedrouter
- **多轮路由器**：knnmultiroundrouter, llmmultiroundrouter
- **混合路由器**：hybridllm, automixrouter, routerdc, router_r1
- **简单选择**：randomrouter, thresholdrouter, largest_llm, smallest_llm

**使用示例**：
```bash
# 使用默认配置启动
./scripts/start-openclaw.sh

# 使用 LLM 路由策略
./scripts/start-openclaw.sh -r llm

# 使用随机路由
./scripts/start-openclaw.sh -r random

# 使用 KNN Router
./scripts/start-openclaw.sh -r knnrouter

# 在端口 9000 上使用 Random Router
./scripts/start-openclaw.sh -r randomrouter -p 9000

# 仅启动 Router，不启动 Gateway
./scripts/start-openclaw.sh --no-gateway

# 使用自定义配置和 ML Router
./scripts/start-openclaw.sh -c my_config.yaml -r mlprouter

# 列出所有可用路由器
./scripts/start-openclaw.sh --list-routers
```

### 2. stop-openclaw.sh

**功能说明**：
用于停止 OpenClaw Router 和 OpenClaw Gateway 服务的脚本。

**用法**：
```bash
./scripts/stop-openclaw.sh
```

**使用示例**：
```bash
# 停止所有 OpenClaw 服务
./scripts/stop-openclaw.sh
```

**输出示例**：
```
============================================================
  Stopping OpenClaw Router + OpenClaw Gateway
============================================================

Stopping OpenClaw Router... OK
Stopping OpenClaw Gateway... OK

All services stopped
```

### 3. print_session_tokens.sh

**功能说明**：
用于导出 OpenCode 会话并解析其 token 使用情况的工具脚本。该脚本会将会话导出为 JSON 文件，然后解析其中的 token 使用统计信息并以表格形式展示。

**用法**：
```bash
./scripts/print_session_tokens.sh [选项] <session-id>
```

**可用选项**：
- `--show-cache` - 在输出表格中包含缓存 token 列
- `--show-messages` - 在代理摘要之前显示每条消息的 token 表格
- `-h, --help` - 显示帮助信息

**使用示例**：
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

**依赖工具**：
- `jq` - 用于 JSON 处理
- `column` - 用于表格格式化
- `opencode` - 用于导出 OpenCode 会话

**输出示例**：
```
Agent Summary
agent      count  total   input   output  reasoning
claude     25     150000  75000   60000   15000
user       12     8000    8000    0       0
TOTAL      37     158000  83000   60000   15000
```

## 部署相关脚本

以下脚本用于部署和运行 LLMRouter 服务：

1. **start-openclaw.sh** - 启动 Router 和 Gateway 服务
2. **stop-openclaw.sh** - 停止 Router 和 Gateway 服务

## 测试相关脚本

以下脚本用于测试和调试：

1. **print_session_tokens.sh** - 用于分析 OpenCode 会话的 token 使用情况，帮助优化成本和性能

## 注意事项

1. 所有脚本都需要具有执行权限，如需添加权限：
   ```bash
   chmod +x scripts/*.sh
   ```

2. 在 Windows 系统上，建议使用 Git Bash 或 WSL 运行这些脚本。

3. 启动脚本前，请确保：
   - 已安装 Python 和必要的依赖
   - 配置文件（config.yaml）存在且配置正确
   - 如果需要使用 OpenClaw Gateway，需先安装 OpenClaw CLI：`npm install -g openclaw`

4. 服务日志位置：
   - OpenClaw Router 日志：`/tmp/openclaw.log`
   - OpenClaw Gateway 日志：`/tmp/openclaw-gateway.log`

## 故障排除

如果脚本运行出现问题：

1. 检查配置文件路径是否正确
2. 查看服务日志文件了解详细错误信息
3. 确认端口未被其他进程占用
4. 验证所有依赖工具是否已安装

## 相关文档

- [OpenClaw Router README](../openclaw_router/README.md)
- [项目主 README](../README.md)
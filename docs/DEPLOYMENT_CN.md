# LLMRouter 部署运维文档

本文档提供 LLMRouter 的完整部署和运维指南，包括本地部署、Docker 容器化部署、云端部署以及监控和性能优化等内容。

---

## 目录

- [本地部署指南](#本地部署指南)
  - [系统要求](#系统要求)
  - [环境准备](#环境准备)
  - [安装步骤](#安装步骤)
  - [配置说明](#配置说明)
  - [启动服务](#启动服务)
  - [验证部署](#验证部署)
- [Docker 部署指南](#docker-部署指南)
  - [Dockerfile 编写](#dockerfile-编写)
  - [Docker Compose 配置](#docker-compose-配置)
  - [构建与运行](#构建与运行)
  - [生产环境建议](#生产环境建议)
- [云端部署指南](#云端部署指南)
  - [AWS 部署](#aws-部署)
  - [Azure 部署](#azure-部署)
  - [Google Cloud 部署](#google-cloud-部署)
- [监控配置说明](#监控配置说明)
  - [Prometheus + Grafana](#prometheus--grafana)
  - [健康检查](#健康检查)
  - [告警配置](#告警配置)
- [日志管理说明](#日志管理说明)
  - [日志配置](#日志配置)
  - [日志轮转](#日志轮转)
  - [集中式日志收集](#集中式日志收集)
- [性能调优指南](#性能调优指南)
  - [并发控制](#并发控制)
  - [缓存优化](#缓存优化)
  - [路由策略优化](#路由策略优化)
  - [网络优化](#网络优化)

---

## 本地部署指南

### 系统要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Linux / macOS / Windows (WSL2) | Linux (Ubuntu 20.04+) |
| CPU | 4 核 | 8+ 核 |
| 内存 | 8GB | 16GB+ |
| 存储 | 20GB | 50GB+ SSD |
| Python | 3.10+ | 3.10 或 3.11 |
| GPU | 可选 | NVIDIA GPU (用于 RouterR1) |

### 环境准备

#### 1. 安装 Python 和虚拟环境

**Linux/macOS:**
```bash
# 创建 Python 虚拟环境
python3.10 -m venv llmrouter-env

# 激活环境
source llmrouter-env/bin/activate
```

**Windows (PowerShell):**
```powershell
# 创建 Python 虚拟环境
python -m venv llmrouter-env

# 激活环境
.\llmrouter-env\Scripts\Activate.ps1
```

#### 2. 安装 CUDA（可选，用于 GPU 加速）

```bash
# 检查 CUDA 版本
nvidia-smi

# 安装 PyTorch (GPU 版本)
pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu118
```

### 安装步骤

#### 方式一：从源码安装

```bash
# 克隆代码仓库
git clone https://github.com/ulab-uiuc/LLMRouter.git
cd LLMRouter

# 基础安装
pip install -e .

# 可选：安装 RouterR1 支持（需要 GPU）
pip install -e ".[router-r1]"

# 可选：安装所有依赖
pip install -e ".[all]"
```

#### 方式二：从 PyPI 安装

```bash
pip install llmrouter-lib
```

### 配置说明

#### 1. 设置 API 密钥

LLMRouter 支持多种格式的 API 密钥配置：

**推荐格式（多服务提供商）：**
```bash
export API_KEYS='{
  "NVIDIA": "nvapi-key1,nvapi-key2",
  "OpenAI": ["sk-...", "sk-..."],
  "Anthropic": "sk-ant-..."
}'
```

**单密钥格式：**
```bash
export API_KEYS='your-api-key'
```

**JSON 数组格式：**
```bash
export API_KEYS='["key1", "key2", "key3"]'
```

#### 2. 配置 LLM 候选模型

创建或编辑 `llm_candidates.json` 文件：

```json
{
  "qwen2.5-7b-instruct": {
    "size": "7B",
    "feature": "通用对话模型",
    "input_price": 0.2,
    "output_price": 0.2,
    "model": "qwen/qwen2.5-7b-instruct",
    "service": "NVIDIA",
    "api_endpoint": "https://integrate.api.nvidia.com/v1"
  },
  "llama3-70b-instruct": {
    "size": "70B",
    "feature": "复杂推理模型",
    "input_price": 0.9,
    "output_price": 0.9,
    "model": "meta/llama3-70b-instruct",
    "service": "NVIDIA",
    "api_endpoint": "https://integrate.api.nvidia.com/v1"
  }
}
```

#### 3. 本地 LLM 配置

如需使用本地部署的 LLM（如 Ollama、vLLM）：

```bash
export API_KEYS='{"Ollama": ""}'
```

```json
{
  "gemma3": {
    "model": "gemma3",
    "service": "Ollama",
    "api_endpoint": "http://localhost:11434/v1"
  }
}
```

### 启动服务

#### 1. 启动 OpenAI 兼容 API 服务器

```bash
# 基础启动
llmrouter serve --config configs/openclaw_example.yaml

# 自定义端口和主机
llmrouter serve --config configs/openclaw_example.yaml \
  --host 0.0.0.0 \
  --port 9000

# 使用 ML 路由器
llmrouter serve --config configs/openclaw_example.yaml \
  --router knnrouter \
  --router-config configs/model_config_test/knnrouter.yaml
```

#### 2. 启动交互式聊天界面

```bash
llmrouter chat --router knnrouter --config config.yaml
```

#### 3. 启动推理服务

```bash
# 单查询推理
llmrouter infer --router knnrouter --config config.yaml --query "What is machine learning?"

# 批量推理
llmrouter infer --router knnrouter --config config.yaml \
  --input queries.txt --output results.json
```

### 验证部署

#### 1. 健康检查

```bash
curl http://localhost:8000/health
```

预期响应：
```json
{
  "status": "ok",
  "router": "randomrouter",
  "llms": ["llama-3.1-8b", "llama3-70b", "mistral-7b"]
}
```

#### 2. 列出可用模型

```bash
curl http://localhost:8000/v1/models
```

#### 3. 测试聊天接口

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Hello, LLMRouter!"}]
  }'
```

---

## Docker 部署指南

### Dockerfile 编写

在项目根目录创建 `Dockerfile`：

```dockerfile
# 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app

# 安装 Python 依赖
RUN pip install --no-cache-dir -e .

# 可选：安装 RouterR1 支持（需要 CUDA）
# RUN pip install --no-cache-dir -e ".[router-r1]"

# 创建数据目录
RUN mkdir -p /app/data /app/saved_models /app/logs

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV API_KEYS='{}'

# 启动命令
CMD ["llmrouter", "serve", "--config", "configs/openclaw_example.yaml", "--host", "0.0.0.0"]
```

### Docker Compose 配置

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  llmrouter:
    build: .
    container_name: llmrouter
    ports:
      - "8000:8000"
    environment:
      - API_KEYS=${API_KEYS}
      - PYTHONUNBUFFERED=1
    volumes:
      - ./data:/app/data
      - ./saved_models:/app/saved_models
      - ./logs:/app/logs
      - ./configs:/app/configs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - llmrouter-network

  # 可选：Prometheus 监控
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped
    networks:
      - llmrouter-network

  # 可选：Grafana 可视化
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    restart: unless-stopped
    networks:
      - llmrouter-network

  # 可选：Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - llmrouter-network

volumes:
  prometheus-data:
  grafana-data:
  redis-data:

networks:
  llmrouter-network:
    driver: bridge
```

创建 `.env` 文件用于环境变量：

```env
API_KEYS='{"NVIDIA": "nvapi-key", "OpenAI": "sk-..."}'
```

### 构建与运行

#### 1. 构建镜像

```bash
docker build -t llmrouter:latest .
```

#### 2. 使用 Docker Compose 启动

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f llmrouter

# 停止服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

#### 3. 单独运行容器

```bash
docker run -d \
  --name llmrouter \
  -p 8000:8000 \
  -e API_KEYS='{"NVIDIA": "nvapi-key"}' \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/saved_models:/app/saved_models \
  --restart unless-stopped \
  llmrouter:latest
```

### 生产环境建议

#### 1. 使用多阶段构建优化镜像大小

```dockerfile
# 构建阶段
FROM python:3.10-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 运行阶段
FROM python:3.10-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . /app

ENV PATH=/root/.local/bin:$PATH

RUN pip install --no-cache-dir -e .

CMD ["llmrouter", "serve", "--config", "configs/openclaw_example.yaml"]
```

#### 2. 资源限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
services:
  llmrouter:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

#### 3. 安全配置

```yaml
services:
  llmrouter:
    user: 1000:1000  # 非 root 用户运行
    read_only: true
    tmpfs:
      - /tmp
```

---

## 云端部署指南

### AWS 部署

#### 方式一：EC2 实例部署

**1. 创建 EC2 实例**

```bash
# 使用 AWS CLI 创建实例
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-0123456789 \
  --user-data file://user-data.sh
```

**2. 用户脚本 (user-data.sh)**

```bash
#!/bin/bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# 拉取并运行容器
docker pull llmrouter:latest
docker run -d --name llmrouter -p 8000:8000 --restart unless-stopped \
  -e API_KEYS='{"NVIDIA": "nvapi-key"}' \
  llmrouter:latest
```

**3. 配置安全组**

允许以下入站规则：

| 类型 | 协议 | 端口范围 | 源 |
|------|------|----------|-----|
| HTTP | TCP | 80 | 0.0.0.0/0 |
| HTTPS | TCP | 443 | 0.0.0.0/0 |
| 自定义 TCP | TCP | 8000 | 0.0.0.0/0 |

**4. 配置 Nginx 反向代理**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### 方式二：ECS 部署

**1. 创建任务定义 (task-definition.json)**

```json
{
  "family": "llmrouter",
  "containerDefinitions": [
    {
      "name": "llmrouter",
      "image": "your-docker-repo/llmrouter:latest",
      "cpu": 2048,
      "memory": 4096,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "API_KEYS",
          "value": "{\"NVIDIA\": \"nvapi-key\"}"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/llmrouter",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "networkMode": "awsvpc",
  "cpu": "2048",
  "memory": "4096"
}
```

**2. 注册任务定义**

```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

**3. 创建服务**

```bash
aws ecs create-service \
  --cluster llmrouter-cluster \
  --service-name llmrouter-service \
  --task-definition llmrouter \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-123,subnet-456],securityGroups=[sg-789],assignPublicIp=ENABLED}"
```

#### 方式三：使用 Lambda + API Gateway（轻量级）

适合低流量场景，无服务器架构。

---

### Azure 部署

#### 方式一：Azure Container Instances (ACI)

**1. 创建容器实例**

```bash
az container create \
  --resource-group llmrouter-rg \
  --name llmrouter \
  --image your-docker-repo/llmrouter:latest \
  --dns-name-label llmrouter-unique \
  --ports 8000 \
  --environment-variables API_KEYS='{"NVIDIA":"nvapi-key"}' \
  --cpu 2 \
  --memory 4
```

#### 方式二：Azure Kubernetes Service (AKS)

**1. 创建 AKS 集群**

```bash
az aks create \
  --resource-group llmrouter-rg \
  --name llmrouter-aks \
  --node-count 2 \
  --node-vm-size Standard_DS2_v2 \
  --enable-addons monitoring \
  --generate-ssh-keys
```

**2. 部署应用 (deployment.yaml)**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llmrouter
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llmrouter
  template:
    metadata:
      labels:
        app: llmrouter
    spec:
      containers:
      - name: llmrouter
        image: your-docker-repo/llmrouter:latest
        ports:
        - containerPort: 8000
        env:
        - name: API_KEYS
          valueFrom:
            secretKeyRef:
              name: llmrouter-secrets
              key: api-keys
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: llmrouter-service
spec:
  selector:
    app: llmrouter
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**3. 应用部署**

```bash
kubectl apply -f deployment.yaml
```

---

### Google Cloud 部署

#### 方式一：Cloud Run

```bash
# 构建并推送镜像
gcloud builds submit --tag gcr.io/PROJECT_ID/llmrouter

# 部署到 Cloud Run
gcloud run deploy llmrouter \
  --image gcr.io/PROJECT_ID/llmrouter \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars API_KEYS='{"NVIDIA":"nvapi-key"}' \
  --memory 4Gi \
  --cpu 2
```

#### 方式二：Google Kubernetes Engine (GKE)

```bash
# 创建 GKE 集群
gcloud container clusters create llmrouter-cluster \
  --num-nodes=3 \
  --machine-type=n1-standard-2 \
  --region=us-central1

# 获取凭证
gcloud container clusters get-credentials llmrouter-cluster \
  --region=us-central1

# 部署应用
kubectl apply -f k8s-deployment.yaml
```

---

## 监控配置说明

### Prometheus + Grafana

#### 1. Prometheus 配置

创建 `monitoring/prometheus.yml`：

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'llmrouter'
    static_configs:
      - targets: ['llmrouter:8000']
    metrics_path: '/metrics'

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

#### 2. 自定义指标扩展

在 `llmrouter/serve/server.py` 中添加 Prometheus 指标：

```python
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
request_count = Counter('llmrouter_requests_total', 'Total requests', ['router', 'model'])
request_latency = Histogram('llmrouter_request_duration_seconds', 'Request latency')
active_connections = Gauge('llmrouter_active_connections', 'Active connections')

# 在路由中使用
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    with request_latency.time():
        request_count.labels(router=config.router_name, model=selected_model).inc()
        # ... 处理请求
```

#### 3. Grafana 仪表盘配置

创建 `monitoring/grafana/dashboards/llmrouter.json`：

```json
{
  "dashboard": {
    "title": "LLMRouter 监控",
    "panels": [
      {
        "title": "请求数量",
        "targets": [
          {
            "expr": "rate(llmrouter_requests_total[5m])",
            "legendFormat": "{{router}} → {{model}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "请求延迟",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, llmrouter_request_duration_seconds)",
            "legendFormat": "P95 延迟"
          }
        ],
        "type": "graph"
      },
      {
        "title": "活跃连接数",
        "targets": [
          {
            "expr": "llmrouter_active_connections"
          }
        ],
        "type": "stat"
      }
    ]
  }
}
```

### 健康检查

#### 1. 基础健康检查端点

```python
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "router": config.router_name,
        "llms": list(config.llms.keys()),
        "timestamp": time.time()
    }
```

#### 2. 深度健康检查

```python
@app.get("/health/deep")
async def health_deep():
    checks = {}

    # 检查各个 LLM 服务
    for llm_name, llm_config in config.llms.items():
        try:
            start = time.time()
            # 简单的健康检查请求
            response = await llm_backend.call(
                llm_name,
                [{"role": "user", "content": "ping"}],
                max_tokens=10
            )
            checks[llm_name] = {
                "status": "ok",
                "latency": time.time() - start
            }
        except Exception as e:
            checks[llm_name] = {
                "status": "error",
                "error": str(e)
            }

    return {
        "status": "ok" if all(c["status"] == "ok" for c in checks.values()) else "degraded",
        "checks": checks
    }
```

### 告警配置

#### Prometheus 告警规则

创建 `monitoring/alerts.yml`：

```yaml
groups:
  - name: llmrouter
    rules:
      - alert: HighErrorRate
        expr: rate(llmrouter_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "高错误率检测"
          description: "错误率超过 5%: {{ $value }}"

      - alert: HighLatency
        expr: histogram_quantile(0.95, llmrouter_request_duration_seconds) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "高延迟检测"
          description: "P95 延迟超过 10s: {{ $value }}s"

      - alert: ServiceDown
        expr: up{job="llmrouter"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "服务不可用"
          description: "LLMRouter 服务已停止"
```

---

## 日志管理说明

### 日志配置

#### 1. 结构化日志配置

创建 `llmrouter/utils/logging_config.py`：

```python
import logging
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger

class LogFormatter(jsonlogger.JsonFormatter):
    """自定义日志格式化器"""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['service'] = 'llmrouter'

def setup_logging(level=logging.INFO):
    """配置日志"""
    handler = logging.StreamHandler()
    formatter = LogFormatter(
        '%(timestamp)s %(level)s %(service)s %(message)s %(pathname)s %(lineno)d'
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
```

#### 2. 请求日志中间件

```python
import time
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # 记录请求
    logger.info({
        "event": "request_start",
        "method": request.method,
        "path": request.url.path,
        "client": request.client.host
    })

    response = await call_next(request)

    # 记录响应
    process_time = time.time() - start_time
    logger.info({
        "event": "request_end",
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration": process_time
    })

    return response
```

### 日志轮转

#### 1. 使用 logrotate

创建 `/etc/logrotate.d/llmrouter`：

```conf
/app/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
    sharedscripts
    postrotate
        docker exec llmrouter kill -USR1 $(cat /app/logs/nginx.pid)
    endscript
}
```

#### 2. 应用内日志轮转

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

### 集中式日志收集

#### 1. 使用 Loki + Promtail

**Loki 配置 (loki-config.yml):**

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
  filesystem:
    directory: /loki/chunks
```

**Promtail 配置 (promtail-config.yml):**

```yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: llmrouter
    docker:
      host: unix:///var/run/docker.sock
      refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
```

#### 2. 使用 ELK Stack

**Filebeat 配置 (filebeat.yml):**

```yaml
filebeat.inputs:
  - type: docker
    containers.ids: '*'
    processors:
      - add_docker_metadata:

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  indices:
    - index: "llmrouter-%{+yyyy.MM.dd}"

setup.kibana:
  host: "kibana:5601"
```

---

## 性能调优指南

### 并发控制

#### 1. Uvicorn 并发配置

```bash
# 使用多 Worker
uvicorn llmrouter.serve.server:create_app \
  --factory \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker
```

#### 2. 请求限流

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/v1/chat/completions")
@limiter.limit("10/minute")
async def chat_completions(request: Request, chat_request: ChatRequest):
    # ... 处理请求
```

### 缓存优化

#### 1. 使用 Redis 缓存

```python
import redis
from functools import wraps

redis_client = redis.Redis(host='redis', port=6379, db=0)

def cache_result(ttl=300):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # 尝试从缓存获取
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result, default=str)
            )

            return result
        return wrapper
    return decorator
```

#### 2. 查询嵌入缓存

```python
@cache_result(ttl=3600)
async def get_query_embedding(query: str):
    """获取查询嵌入（带缓存）"""
    return get_longformer_embedding(query)
```

### 路由策略优化

#### 1. 负载均衡配置

```yaml
router:
  strategy: random
  weights:
    fast-model: 5     # 50% 流量
    balanced-model: 3  # 30% 流量
    powerful-model: 2  # 20% 流量
```

#### 2. 路由缓存

```python
from functools import lru_cache

class CachedRouter:
    def __init__(self, router):
        self.router = router
        self.cache = {}

    @lru_cache(maxsize=1000)
    def route_single_cached(self, query: str):
        return self.router.route_single({"query": query})
```

### 网络优化

#### 1. 启用 HTTP/2

```python
app = FastAPI()

# 配置 HTTP/2
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
app.add_middleware(HTTPSRedirectMiddleware)
```

#### 2. 连接池配置

```python
import httpx

# 配置连接池
client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100,
        keepalive_expiry=30
    ),
    timeout=httpx.Timeout(120.0)
)
```

#### 3. Gzip 压缩

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 性能测试

#### 使用 Locust 进行压测

创建 `locustfile.py`：

```python
from locust import HttpUser, task, between

class LLMRouterUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def chat_completion(self):
        self.client.post("/v1/chat/completions", json={
            "model": "auto",
            "messages": [{"role": "user", "content": "What is machine learning?"}]
        })

    @task(3)
    def health_check(self):
        self.client.get("/health")
```

运行压测：

```bash
locust -f locustfile.py --host http://localhost:8000
```

---

## 总结

本文档涵盖了 LLMRouter 的完整部署和运维指南，包括：

1. **本地部署**：从源码或 PyPI 安装，配置 API 密钥和 LLM 候选模型
2. **Docker 部署**：使用 Dockerfile 和 Docker Compose 进行容器化部署
3. **云端部署**：在 AWS、Azure 和 Google Cloud 上部署的多种方式
4. **监控配置**：使用 Prometheus 和 Grafana 进行监控和告警
5. **日志管理**：结构化日志、日志轮转和集中式日志收集
6. **性能调优**：并发控制、缓存优化、路由策略和网络优化

根据您的需求选择合适的部署方式，并根据实际负载进行性能调优。如有问题，请参考项目文档或提交 Issue。
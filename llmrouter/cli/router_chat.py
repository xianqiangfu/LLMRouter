"""
Chatbot Interface for LLMRouter

This script provides a Gradio-based chat interface that uses LLMRouter
to route queries to appropriate models and generate responses.
"""

import atexit
import argparse
import os
import yaml
from typing import Dict, Any, Optional

import gradio as gr

# Import router classes
from llmrouter.models import (
    KNNRouter,
    SVMRouter,
    MLPRouter,
    MFRouter,
    EloRouter,
    DCRouter,
    HybridLLMRouter,
    GraphRouter,
    CausalLMRouter,
    SmallestLLM,
    LargestLLM,
    AutomixRouter,
    GMTRouter,
    PersonalizedRouter,
)
from llmrouter.models.llmmultiroundrouter import LLMMultiRoundRouter
from llmrouter.models.knnmultiroundrouter import KNNMultiRoundRouter
try:
    from llmrouter.models import RouterR1
except ImportError:
    RouterR1 = None
from llmrouter.utils import call_api, get_longformer_embedding
import torch
import numpy as np


# -----------------------------------------------------------------------------
# CSS STYLING (UPDATED FOR FORCED LIGHT THEME)
# -----------------------------------------------------------------------------
CUSTOM_CSS = """
/* FORCE LIGHT THEME VARIABLES */
:root, .gradio-container {
    --body-background-fill: #f3f4f6; /* Slightly darker grey for better contrast with white cards */
    --body-text-color: #0f172a;
    --background-fill-primary: #ffffff;
    --background-fill-secondary: #f8fafc;
    --border-color-primary: #e2e8f0;
    --block-background-fill: #ffffff;
    --block-border-color: #e2e8f0;
    --block-label-text-color: #64748b;
    --block-title-text-color: #1e293b;
    --input-background-fill: #ffffff;
    --input-border-color: #cbd5e1;
    --font: 'Inter', system-ui, -apple-system, sans-serif;
}

.gradio-container {
    max-width: 100% !important;
    width: 100% !important;
    padding: 0 24px !important;
    background: var(--body-background-fill) !important;
}

/* --- SHARED CARD STYLE --- */
/* This unifies the look of the Info Panel and the Controls Section */
.side-panel, .controls-section {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 16px !important; /* Modern rounded corners */
    padding: 24px !important;       /* Consistent padding */
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
    margin-bottom: 16px;
}

/* --- HEADER BAR --- */
.top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 0;
    margin-bottom: 24px;
    border-bottom: 1px solid #e5e7eb;
}

.top-bar h1 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #111827;
    margin: 0;
    letter-spacing: -0.025em;
}

.status-pill {
    background: #dbeafe;
    color: #1e40af;
    padding: 6px 16px;
    border-radius: 9999px;
    font-size: 0.875rem;
    font-weight: 600;
    border: 1px solid #bfdbfe;
    display: flex;
    align-items: center;
    gap: 8px;
}
.status-pill::before {
    content: "";
    display: block;
    width: 8px;
    height: 8px;
    background: #2563eb;
    border-radius: 50%;
}

/* --- CHAT AREA --- */
.main-chat {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
.main-chat .bubble-wrap {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
}
.main-chat .message.user {
    background-color: #eff6ff !important;
    border-color: #bfdbfe !important;
    color: #1e3a8a !important;
}

/* --- CODE BLOCKS IN CHAT --- */
/* Style code blocks in chat messages for readability */
.main-chat pre,
.main-chat code,
.message pre,
.message code {
    background-color: #f8fafc !important;
    color: #1e293b !important;
    border: 1px solid #e2e8f0 !important;
}

/* Inline code */
.main-chat code:not(pre code),
.message code:not(pre code) {
    background-color: #f1f5f9 !important;
    color: #0f172a !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-size: 0.9em !important;
    border: 1px solid #e2e8f0 !important;
}

/* Code blocks (pre) */
.main-chat pre,
.message pre {
    background-color: #f8fafc !important;
    color: #1e293b !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    overflow-x: auto !important;
    margin: 8px 0 !important;
}

/* Code inside pre blocks */
.main-chat pre code,
.message pre code {
    background-color: transparent !important;
    border: none !important;
    padding: 0 !important;
    color: #1e293b !important;
}

/* Ensure text in code blocks is always readable */
.main-chat pre *,
.message pre *,
.main-chat code *,
.message code * {
    color: #1e293b !important;
}

/* --- INPUT AREA --- */
.input-row textarea {
    border-radius: 12px !important;
    padding: 14px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    transition: all 0.2s;
}
.input-row textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
}
button.primary {
    background: #2563eb !important;
    border-radius: 10px !important;
    transition: background 0.2s;
}
button.primary:hover {
    background: #1d4ed8 !important;
}

/* --- SIDE PANEL SPECIFICS (TOP BOX) --- */
.side-panel h3 {
    margin: 0 0 16px 0;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
    font-weight: 700;
}

.side-panel .info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px dashed #f1f5f9;
}
.side-panel .info-row:last-child {
    border-bottom: none;
    padding-bottom: 0;
}

.side-panel .info-label {
    font-size: 0.9rem;
    color: #64748b;
    font-weight: 500;
}

.side-panel .info-value {
    font-family: 'Monaco', monospace;
    font-size: 0.85rem;
    color: #0f172a;
    background: #f1f5f9;
    padding: 4px 10px;
    border-radius: 6px;
    font-weight: 600;
}

/* --- CONTROLS SPECIFICS (BOTTOM BOX) --- */
.controls-section {
    margin-top: 0 !important;
}

/* Clean up Gradio's default label styling to match our custom header */
.controls-section span.label-wrap, 
.controls-section label span {
    color: #64748b !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

/* Mode Radio Buttons - Modern Pills */
.mode-radio {
    margin-bottom: 16px !important;
}
.mode-radio .gradio-radio-group {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}
.mode-radio label {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    font-size: 0.9rem !important;
    color: #475569 !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
    transition: all 0.2s ease;
    flex-grow: 1;
    justify-content: center;
    text-align: center;
}
.mode-radio label:hover {
    border-color: #cbd5e1 !important;
    background: #ffffff !important;
}
.mode-radio label.selected,
.mode-radio input[type="radio"]:checked + label {
    background: #eff6ff !important;
    border-color: #3b82f6 !important;
    color: #1d4ed8 !important;
    box-shadow: 0 0 0 1px #3b82f6 !important;
}
.mode-radio .circle { display: none !important; } /* Hide the actual radio circle */

/* Sliders */
input[type=range] {
    accent-color: #2563eb;
}

footer { display: none !important; }
"""

def _safe_unlink(path: str) -> None:
    """安全删除文件，如果文件不存在则忽略错误"""
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def _normalize_chat_history(history: Any) -> list[tuple[str, str]]:
    """
    将聊天历史规范化为标准格式

    支持输入格式：
    - [(user, assistant), ...] 元组列表
    - [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...] 字典列表

    Returns:
        标准化的聊天历史列表 [(user, assistant), ...]
    """
    if not history:
        return []

    if isinstance(history, (list, tuple)) and history:
        first = history[0]
        if isinstance(first, (list, tuple)) and len(first) == 2:
            # 输入格式为元组列表
            normalized: list[tuple[str, str]] = []
            for human, assistant in history:
                human_text = "" if human is None else str(human)
                assistant_text = "" if assistant is None else str(assistant)
                normalized.append((human_text, assistant_text))
            return normalized

        if isinstance(first, dict) and "role" in first:
            # 输入格式为字典列表（OpenAI 风格）
            normalized: list[tuple[str, str]] = []
            current_user: Optional[str] = None
            for msg in history:
                if not isinstance(msg, dict):
                    continue
                role = msg.get("role")
                content = msg.get("content")
                content_text = "" if content is None else str(content)
                if role == "user":
                    current_user = content_text
                elif role == "assistant":
                    if current_user is None:
                        normalized.append(("", content_text))
                    else:
                        normalized.append((current_user, content_text))
                        current_user = None
            # 处理最后一条未配对的用户消息
            if current_user is not None:
                normalized.append((current_user, ""))
            return normalized

    return []


# Router registry: maps router method names to their classes
ROUTER_REGISTRY = {
    "knnrouter": KNNRouter,
    "svmrouter": SVMRouter,
    "mlprouter": MLPRouter,
    "mfrouter": MFRouter,
    "elorouter": EloRouter,
    "dcrouter": DCRouter,
    "routerdc": DCRouter,
    "smallest_llm": SmallestLLM,
    "largest_llm": LargestLLM,
    "llmmultiroundrouter": LLMMultiRoundRouter,
    "knnmultiroundrouter": KNNMultiRoundRouter,
    "automixrouter": AutomixRouter,
}

# Add optional routers if available
if HybridLLMRouter is not None:
    ROUTER_REGISTRY["hybrid_llm"] = HybridLLMRouter
    ROUTER_REGISTRY["hybridllm"] = HybridLLMRouter

if GraphRouter is not None:
    ROUTER_REGISTRY["graphrouter"] = GraphRouter
    ROUTER_REGISTRY["graph_router"] = GraphRouter

if CausalLMRouter is not None:
    ROUTER_REGISTRY["causallm_router"] = CausalLMRouter
    ROUTER_REGISTRY["causallmrouter"] = CausalLMRouter

# Add RouterR1 if available
if RouterR1 is not None:
    ROUTER_REGISTRY["router_r1"] = RouterR1
    ROUTER_REGISTRY["router-r1"] = RouterR1

# Add GMTRouter if available
if GMTRouter is not None:
    ROUTER_REGISTRY["gmtrouter"] = GMTRouter
    ROUTER_REGISTRY["gmt_router"] = GMTRouter

if PersonalizedRouter is not None:
    ROUTER_REGISTRY["personalizedrouter"] = PersonalizedRouter
    ROUTER_REGISTRY["personalized_router"] = PersonalizedRouter

# Multi-round routers that have full pipeline in route_single
# These routers return response directly from route_single
MULTI_ROUND_ROUTERS = {
    "llmmultiroundrouter",
    "knnmultiroundrouter",
}

# Routers that require special handling
# RouterR1 needs model_id, api_base, api_key for route_single
ROUTERS_REQUIRING_SPECIAL_ARGS = {
    "router_r1",
    "router-r1",
}

# Routers that benefit from conversation history (multi-turn context)
# These routers receive conversation_history in route_single for personalization
ROUTERS_WITH_CONVERSATION_HISTORY = {
    "gmtrouter",
    "gmt_router",
}

# Routers that are not supported for chat interface
UNSUPPORTED_ROUTERS = {}


def prepare_query_full_context(message: str, history: list) -> str:
    """
    为完整上下文模式准备查询：将所有历史记录与当前查询合并

    Args:
        message: 当前用户消息
        history: 聊天历史，(user, assistant) 元组列表

    Returns:
        合并后的查询字符串
    """
    # 从历史记录构建完整上下文
    context_parts = []
    for human, assistant in _normalize_chat_history(history):
        context_parts.append(f"Previous Query: {human}")
        context_parts.append(f"Previous Response: {assistant}")

    # 添加当前查询
    context_parts.append(f"Current Query: {message}")

    # 合并为单个查询
    combined_query = "\n\n".join(context_parts)
    return combined_query


def prepare_query_current_only(message: str, history: list) -> str:
    """
    为仅当前查询模式准备查询：只使用当前查询

    Args:
        message: 当前用户消息
        history: 聊天历史（在此模式下不使用）

    Returns:
        当前查询字符串
    """
    return message


def prepare_query_retrieval(message: str, history: list, top_k: int = 3) -> str:
    """
    为检索模式准备查询：查找 top-k 个相似的历史查询

    Args:
        message: 当前用户消息
        history: 聊天历史，(user, assistant) 元组列表
        top_k: 要检索的相似查询数量

    Returns:
        包含检索上下文的合并查询字符串
    """
    history_pairs = _normalize_chat_history(history)
    if not history_pairs:
        # 没有历史记录，只返回当前查询
        return message

    try:
        # 获取当前查询的嵌入向量
        current_embedding = get_longformer_embedding(message)
        if isinstance(current_embedding, torch.Tensor):
            current_embedding = current_embedding.numpy()

        # 确保 current_embedding 是一维的
        if len(current_embedding.shape) > 1:
            current_embedding = current_embedding.flatten()

        # 获取所有历史查询的嵌入向量
        historical_queries = [human for human, _ in history_pairs]
        historical_responses = [assistant for _, assistant in history_pairs]

        if not historical_queries:
            return message

        # 计算历史查询的嵌入向量
        historical_embeddings = get_longformer_embedding(historical_queries)
        if isinstance(historical_embeddings, torch.Tensor):
            historical_embeddings = historical_embeddings.numpy()

        # 处理 historical_embeddings 可能是一维的情况（单个查询）
        if len(historical_embeddings.shape) == 1:
            historical_embeddings = historical_embeddings.reshape(1, -1)

        # 计算余弦相似度
        # 归一化嵌入向量
        current_norm = current_embedding / (np.linalg.norm(current_embedding) + 1e-8)
        historical_norms = historical_embeddings / (np.linalg.norm(historical_embeddings, axis=1, keepdims=True) + 1e-8)

        # 计算相似度: (num_queries, embedding_dim) @ (embedding_dim,) -> (num_queries,)
        similarities = np.dot(historical_norms, current_norm)

        # 确保 similarities 是一维数组
        if similarities.ndim == 0:
            similarities = np.array([similarities])
        elif len(similarities.shape) > 1:
            similarities = similarities.flatten()

        # 获取 top-k 索引（限制在可用历史记录数量内）
        actual_top_k = min(top_k, len(historical_queries))
        top_k_indices = np.argsort(similarities)[-actual_top_k:][::-1]

        # 构建检索的上下文
        retrieved_parts = []
        for idx in top_k_indices:
            retrieved_parts.append(f"Similar Query: {historical_queries[idx]}")
            retrieved_parts.append(f"Response: {historical_responses[idx]}")

        # 将检索的上下文与当前查询合并
        retrieved_context = "\n\n".join(retrieved_parts)
        combined_query = f"{retrieved_context}\n\nCurrent Query: {message}"

        return combined_query

    except Exception as e:
        # 如果检索失败，回退到仅使用当前查询
        print(f"Warning: Retrieval mode failed, falling back to current query only: {e}")
        return message


def prepare_query_by_mode(message: str, history: list, mode: str, top_k: int = 3) -> str:
    """
    根据选择的模式准备查询

    Args:
        message: 当前用户消息
        history: 聊天历史，(user, assistant) 元组列表
        mode: 以下之一："full_context"、"current_only"、"retrieval"
        top_k: 检索模式中相似查询的数量

    Returns:
        准备好的查询字符串
    """
    mode_lower = mode.lower()

    if mode_lower == "full_context" or mode_lower == "full":
        return prepare_query_full_context(message, history)
    elif mode_lower == "current_only" or mode_lower == "current":
        return prepare_query_current_only(message, history)
    elif mode_lower == "retrieval" or mode_lower == "retrieve":
        return prepare_query_retrieval(message, history, top_k)
    else:
        # 如果模式未知，默认使用 current_only
        print(f"Warning: Unknown mode '{mode}', defaulting to 'current_only'")
        return prepare_query_current_only(message, history)


def load_router(router_name: str, config_path: str, load_model_path: Optional[str] = None):
    """
    根据路由器名称和配置加载路由器实例

    Args:
        router_name: 路由器方法名称（如 "knnrouter"、"llmmultiroundrouter"）
        config_path: YAML 配置文件路径
        load_model_path: 可选路径，用于覆盖配置文件中的 model_path.load_model_path

    Returns:
        路由器实例
    """
    router_name_lower = router_name.lower()

    # 检查路由器是否不支持聊天界面
    if router_name_lower in UNSUPPORTED_ROUTERS:
        raise ValueError(
            f"Router '{router_name}' is not supported for chat interface. "
            f"Supported routers: {list(ROUTER_REGISTRY.keys())}"
        )

    if router_name_lower not in ROUTER_REGISTRY:
        raise ValueError(
            f"Unknown router: {router_name}. Available routers: {list(ROUTER_REGISTRY.keys())}"
        )

    router_class = ROUTER_REGISTRY[router_name_lower]

    # 如果提供了自定义模型路径，覆盖配置文件中的模型路径
    if load_model_path:
        # 读取配置、修改、写入临时文件
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        if "model_path" not in config:
            config["model_path"] = {}
        config["model_path"]["load_model_path"] = load_model_path

        # 写入临时配置文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as temp_config:
            yaml.safe_dump(config, temp_config)
            config_path = temp_config.name
        atexit.register(_safe_unlink, config_path)

    # 初始化路由器
    # 注意：RouterR1 可能需要特殊处理，但测试表明它可以仅使用 yaml_path 进行初始化
    try:
        router = router_class(yaml_path=config_path)
    except TypeError as e:
        # 如果初始化失败，可能需要额外的初始化参数
        if "required positional argument" in str(e) or "missing" in str(e).lower():
            raise ValueError(
                f"Router '{router_name}' requires additional initialization parameters. "
                f"Error: {str(e)}"
            ) from e
        raise

    return router


def predict(
    message: str,
    history: list,
    router_instance: Any,
    router_name: str,
    temperature: float = 0.8,
    mode: str = "current_only",
    top_k: int = 3,
):
    """
    使用路由器预测响应

    Args:
        message: 用户消息
        history: 聊天历史，(user, assistant) 元组列表
        router_instance: 已加载的路由器实例
        router_name: 路由器方法名称
        temperature: 生成温度参数（如果适用）
        mode: 查询模式 - "full_context"、"current_only" 或 "retrieval"
        top_k: 检索模式中相似查询的数量

    Returns:
        生成的响应文本（字符串）
    """
    router_name_lower = router_name.lower()
    history_pairs = _normalize_chat_history(history)

    # 根据模式准备查询
    query_for_router = prepare_query_by_mode(message, history_pairs, mode, top_k)

    # 检查路由器是否为多轮路由器（在 route_single 中执行完整流程）
    if router_name_lower in MULTI_ROUND_ROUTERS:
        # 多轮路由器执行完整流程：分解 + 路由 + 执行 + 聚合
        # 对于聊天模式，只需传入查询字符串并获取响应
        try:
            # 使用简单的查询字符串调用 route_single 进行聊天交互
            result = router_instance.route_single(query_for_router)
            # 多轮路由器直接返回响应
            return result
        except Exception as e:
            import traceback
            return f"Error: {str(e)}\n{traceback.format_exc()}"

    # 特殊处理 RouterR1（需要 model_id、api_base、api_key）
    if router_name_lower in ROUTERS_REQUIRING_SPECIAL_ARGS:
        try:
            # 从配置中获取必需参数
            cfg = getattr(router_instance, "cfg", {}) or {}
            hparam = cfg.get("hparam", {}) or {}
            api_base = hparam.get("api_base") or getattr(router_instance, "api_base", None)
            api_key = hparam.get("api_key") or getattr(router_instance, "api_key", None)

            if not api_key or not api_base:
                return "Error: RouterR1 requires api_key and api_base in yaml config"

            result = router_instance.route_single({"query": query_for_router})
            return result

        except Exception as e:
            return f"Error with RouterR1: {str(e)}"

    # 否则，使用 route_single 获取路由决策，然后调用模型
    try:
        # 执行查询路由 - 使用基于模式准备的查询
        query_input = {"query": query_for_router}

        # 对于 GMTRouter，添加对话历史以进行多轮个性化
        if router_name_lower in ROUTERS_WITH_CONVERSATION_HISTORY:
            # 将历史记录转换为 conversation_history 格式
            conversation_history = []
            for user_msg, assistant_msg in history_pairs:
                conversation_history.append({
                    "role": "user",
                    "content": user_msg
                })
                if assistant_msg:  # 最后一轮可能为 None
                    conversation_history.append({
                        "role": "assistant",
                        "content": assistant_msg
                    })

            query_input.update({
                "query_text": message,  # 原始消息
                "user_id": "chat_user",  # 默认聊天用户（可自定义）
                "session_id": "chat_session",
                "turn": len(history_pairs) + 1,
                "conversation_history": conversation_history
            })

        routing_result = router_instance.route_single(query_input)

        # 从路由结果中提取模型名称
        # DCRouter 返回 "predicted_llm"，其他路由器返回 "model_name"
        model_name = (
            routing_result.get("model_name")
            or routing_result.get("predicted_llm")
            or routing_result.get("predicted_llm_name")
        )

        if not model_name:
            return f"Error: Router did not return a model name. Routing result: {routing_result}"

        # 从 llm_data 获取 API 端点和模型名称（如果可用）
        # 路由器返回模型键，但我们需要完整的模型路径用于 API
        api_model_name = model_name  # 默认使用 model_name
        api_endpoint = None
        service = None

        if hasattr(router_instance, 'llm_data') and router_instance.llm_data:
            if model_name in router_instance.llm_data:
                # 使用 llm_data 中的 "model" 字段，它包含完整的 API 路径
                api_model_name = router_instance.llm_data[model_name].get("model", model_name)
                # 从 llm_data 获取 API 端点，如果不存在则回退到路由器配置
                api_endpoint = router_instance.llm_data[model_name].get(
                    "api_endpoint",
                    router_instance.cfg.get("api_endpoint")
                )
                # 获取 service 字段用于服务特定的 API 密钥选择
                service = router_instance.llm_data[model_name].get("service")
            else:
                # 如果未找到 model_name，尝试通过匹配 model 字段来查找
                for key, value in router_instance.llm_data.items():
                    if value.get("model") == model_name or key == model_name:
                        api_model_name = value.get("model", model_name)
                        # 从 llm_data 获取 API 端点，如果不存在则回退到路由器配置
                        api_endpoint = value.get(
                            "api_endpoint",
                            router_instance.cfg.get("api_endpoint")
                        )
                        # 获取 service 字段用于服务特定的 API 密钥选择
                        service = value.get("service")
                        break

        # 如果仍然没有找到端点，尝试从路由器配置获取
        if api_endpoint is None:
            api_endpoint = router_instance.cfg.get("api_endpoint")

        # 验证我们有端点
        if not api_endpoint:
            return f"Error: API endpoint not found for model '{model_name}'. Please specify 'api_endpoint' in llm_data JSON for this model or in router YAML config."

        # 构建包含聊天历史的提示词
        prompt = "You are a helpful AI assistant.\n\n"
        for human, assistant in history_pairs:
            prompt += f"User: {human}\nAssistant: {assistant}\n\n"
        prompt += f"User: {message}\nAssistant:"

        # 通过 API 调用路由到的模型
        request = {
            "api_endpoint": api_endpoint,
            "query": prompt,
            "model_name": model_name,  # 保留原始名称用于路由器识别
            "api_name": api_model_name,  # 使用完整的 API 模型路径
        }
        # 如果可用则添加 service 字段（用于服务特定的 API 密钥选择）
        if service:
            request["service"] = service

        result = call_api(request, max_tokens=1024, temperature=temperature)

        response = result.get("response", "No response generated")

        # 添加模型名称前缀
        model_prefix = f"[{model_name}]\n"
        return model_prefix + response

    except Exception as e:
        import traceback
        return f"Error: {str(e)}\n{traceback.format_exc()}"


def create_interface(router_instance, router_name: str, args):
    """创建简洁的聊天界面"""

    # 获取 LLM 数量用于显示
    llm_count = 0
    if hasattr(router_instance, 'llm_data') and router_instance.llm_data:
        llm_count = len(router_instance.llm_data)

    def predict_with_router(message, history, temperature, mode, top_k):
        return predict(message, history, router_instance, router_name, temperature, mode, top_k)

    # 使用 gr.themes.Base() 最小化默认样式干扰，但 Default 配合我们的自定义样式也可以
    with gr.Blocks(css=CUSTOM_CSS, theme=gr.themes.Default(), title="LLMRouter") as demo:

        # 简洁的顶部栏
        gr.HTML(f"""
            <div class="top-bar">
                <h1>LLMRouter</h1>
                <span class="status-pill">{router_name}</span>
            </div>
        """)

        with gr.Row():
            # 主聊天区域 - 占据大部分空间
            with gr.Column(scale=4, elem_classes=["main-chat"]):
                chatbot = gr.Chatbot(
                    height=560,
                    show_label=False,
                    type="messages",
                    elem_classes=["main-chat"]
                )

                with gr.Row(elem_classes=["input-row"]):
                    msg = gr.Textbox(
                        placeholder="Type a message...",
                        show_label=False,
                        container=False,
                        scale=5,
                    )
                    submit_btn = gr.Button("Send", variant="primary", scale=1)

                with gr.Row(elem_classes=["action-btns"]):
                    clear_btn = gr.Button("Clear", size="sm")
                    retry_btn = gr.Button("Retry", size="sm")
                    undo_btn = gr.Button("Undo", size="sm")

            # 紧凑的侧边栏
            with gr.Column(scale=1, min_width=200, elem_classes=["side-column"]):
                gr.HTML(f"""
                    <div class="side-panel">
                        <h3>System Info</h3>
                        <div class="info-row">
                            <span class="info-label">Active Router</span>
                            <span class="info-value">{router_name}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Loaded Models</span>
                            <span class="info-value">{llm_count}</span>
                        </div>
                    </div>
                """)

                with gr.Column(elem_classes=["controls-section"]):
                    mode = gr.Radio(
                        label="Routing Context", # 更改标签以获得更好的美观度
                        choices=["current_only", "full_context", "retrieval"],
                        value=args.mode,
                        container=True,
                        elem_classes=["mode-radio"],
                    )
                    temperature = gr.Slider(
                        label="Temperature",
                        minimum=0,
                        maximum=2,
                        value=args.temp,
                        step=0.1,
                    )
                    top_k = gr.Slider(
                        label="Top-K",
                        minimum=1,
                        maximum=10,
                        value=args.top_k,
                        step=1,
                        visible=(args.mode == "retrieval"),
                    )

        # 事件处理器 - 立即显示用户消息，然后流式传输响应
        def user_message(message, chat_history):
            """立即添加用户消息并清空输入框"""
            if not message.strip():
                return "", chat_history
            # Gradio 消息对象需要字符串内容；使用空字符串作为占位符
            updated_history = chat_history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": ""},
            ]
            return "", updated_history

        def bot_response(chat_history, temperature, mode, top_k):
            """逐字符流式传输机器人响应"""
            if (
                len(chat_history) < 2
                or chat_history[-1].get("role") != "assistant"
                or chat_history[-1].get("content") not in (None, "")
                or chat_history[-2].get("role") != "user"
            ):
                yield chat_history
                return

            user_msg = chat_history[-2].get("content", "")
            history_for_router = chat_history[:-1]

            full_response = predict_with_router(user_msg, history_for_router, temperature, mode, top_k)

            partial = ""
            for char in full_response:
                partial += char
                chat_history[-1]["content"] = partial
                yield chat_history

        def retry_last(chat_history, temperature, mode, top_k):
            """使用流式传输重试最后一条消息"""
            if not chat_history:
                yield chat_history
                return

            trimmed_history = list(chat_history)
            if trimmed_history and trimmed_history[-1].get("role") == "assistant":
                trimmed_history = trimmed_history[:-1]

            if not trimmed_history or trimmed_history[-1].get("role") != "user":
                yield chat_history
                return

            last_user_msg = trimmed_history[-1].get("content", "")
            trimmed_history.append({"role": "assistant", "content": ""})
            yield trimmed_history

            history_for_router = trimmed_history[:-1]
            full_response = predict_with_router(last_user_msg, history_for_router, temperature, mode, top_k)
            partial = ""
            for char in full_response:
                partial += char
                trimmed_history[-1]["content"] = partial
                yield trimmed_history

        # 连接事件 - 两步：显示用户消息，然后流式传输响应
        msg.submit(user_message, [msg, chatbot], [msg, chatbot], queue=False).then(
            bot_response, [chatbot, temperature, mode, top_k], chatbot
        )
        submit_btn.click(user_message, [msg, chatbot], [msg, chatbot], queue=False).then(
            bot_response, [chatbot, temperature, mode, top_k], chatbot
        )
        clear_btn.click(lambda: [], None, chatbot, queue=False)
        retry_btn.click(retry_last, [chatbot, temperature, mode, top_k], chatbot)
        undo_btn.click(
            lambda h: h[:-2] if len(h) >= 2 and h[-1].get("role") == "assistant" else (h[:-1] if h else h),
            chatbot,
            chatbot,
            queue=False,
        )
        mode.change(lambda m: gr.update(visible=(m == "retrieval")), mode, top_k)

    return demo


def main():
    """聊天界面的主入口函数"""
    parser = argparse.ArgumentParser(
        description="Chatbot Interface for LLMRouter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --router knnrouter --config configs/model_config_test/knnrouter.yaml
  %(prog)s --router mfrouter --config configs/model_config_test/mfrouter.yaml --mode full_context
  %(prog)s --router dcrouter --config configs/model_config_test/dcrouter.yaml --share
        """,
    )
    parser.add_argument(
        "--router",
        type=str,
        required=True,
        help="Router method name (e.g., knnrouter, llmmultiroundrouter, mfrouter)",
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "--load_model_path",
        type=str,
        default=None,
        help="Optional path to override model_path.load_model_path in config",
    )
    parser.add_argument(
        "--temp",
        type=float,
        default=0.8,
        help="Temperature for text generation (default: 0.8)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host to bind the server to (default: None, all interfaces)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port to bind the server to (default: 8001)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="current_only",
        choices=["full_context", "current_only", "retrieval"],
        help="Query mode: 'full_context' (all history), 'current_only' (single query), 'retrieval' (top-k similar) (default: current_only)",
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=3,
        help="Number of similar queries to retrieve in retrieval mode (default: 3)",
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public shareable link",
    )

    args = parser.parse_args()

    # 验证配置文件是否存在
    if not os.path.exists(args.config):
        raise FileNotFoundError(f"Config file not found: {args.config}")

    # 打印启动横幅
    print("\n" + "=" * 60)
    print("🚀 LLMRouter Chat Interface")
    print("=" * 60)
    print(f"  Router:  {args.router}")
    print(f"  Config:  {args.config}")
    print(f"  Mode:    {args.mode}")
    print(f"  Port:    {args.port}")
    if args.load_model_path:
        print(f"  Model:   {args.load_model_path}")
    print("=" * 60 + "\n")

    # 加载路由器
    print("📦 Loading router...")
    router_instance = load_router(args.router, args.config, args.load_model_path)
    print("✅ Router loaded successfully!\n")

    # 创建并启动界面
    print("🌐 Starting web interface...")
    demo = create_interface(router_instance, args.router, args)
    demo.queue().launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        show_error=True,
    )


if __name__ == "__main__":
    main()

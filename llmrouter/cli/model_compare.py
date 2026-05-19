"""
Model Comparison Interface for LLMRouter

This script provides a Gradio-based interface that compares outputs from
two different LLM models side by side.
"""

import argparse
import os
import yaml
from typing import Dict, Any, Optional, List

import gradio as gr

from llmrouter.utils import call_api


# -----------------------------------------------------------------------------
# CSS STYLING
# -----------------------------------------------------------------------------
CUSTOM_CSS = """
/* FORCE LIGHT THEME VARIABLES */
:root, .gradio-container {
    --body-background-fill: #f3f4f6;
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

/* --- HEADER BAR --- */
.top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 0;
    margin-bottom: 16px;
    border-bottom: 1px solid #e5e7eb;
}

.top-bar h1 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #111827;
    margin: 0;
    letter-spacing: -0.025em;
}

.status-badge {
    background: #dbeafe;
    color: #1e40af;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 500;
    border: 1px solid #bfdbfe;
}

/* --- MODEL CARDS --- */
.model-card {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 14px !important;
    box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.03) !important;
    height: 100%;
    display: flex;
    flex-direction: column;
}

.model-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #f1f5f9;
}

.model-card-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #1e293b;
    margin: 0;
}

.model-card-select {
    width: 100%;
}

.model-card-select .label-wrap {
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    color: #64748b !important;
    margin-bottom: 4px !important;
}

/* --- CHAT AREA --- */
.chat-area {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    flex: 1;
    min-height: 320px;
}

.chat-area .bubble-wrap {
    background-color: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
}

.chat-area .message.user {
    background-color: #eff6ff !important;
    border-color: #bfdbfe !important;
    color: #1e3a8a !important;
}

.chat-area .message.assistant {
    background-color: #ffffff !important;
    border-color: #e2e8f0 !important;
    color: #0f172a !important;
}

/* --- CODE BLOCKS IN CHAT --- */
.chat-area pre,
.chat-area code,
.message pre,
.message code {
    background-color: #f8fafc !important;
    color: #1e293b !important;
    border: 1px solid #e2e8f0 !important;
}

.chat-area code:not(pre code),
.message code:not(pre code) {
    background-color: #f1f5f9 !important;
    color: #0f172a !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-size: 0.9em !important;
    border: 1px solid #e2e8f0 !important;
}

.chat-area pre,
.message pre {
    background-color: #f8fafc !important;
    color: #1e293b !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    overflow-x: auto !important;
    margin: 8px 0 !important;
}

.chat-area pre code,
.message pre code {
    background-color: transparent !important;
    border: none !important;
    padding: 0 !important;
    color: #1e293b !important;
}

/* --- INPUT AREA --- */
.input-section {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.03) !important;
    margin-top: 16px;
}

.input-row {
    display: flex;
    gap: 10px;
    align-items: flex-end;
}

.input-row textarea {
    border-radius: 10px !important;
    padding: 12px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    transition: all 0.2s;
    resize: none;
}

.input-row textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
}

/* --- ACTION BUTTONS --- */
.action-btns {
    display: flex;
    gap: 6px;
    margin-top: 8px;
}


/* --- MODE 1 COLOR SCHEME --- */
.model-1 .model-card-header {
    border-bottom-color: #bfdbfe;
}

.model-1 .status-badge {
    background: #dbeafe;
    color: #1e40af;
    border-color: #bfdbfe;
}

/* --- MODE 2 COLOR SCHEME --- */
.model-2 .model-card-header {
    border-bottom-color: #d1fae5;
}

.model-2 .status-badge {
    background: #d1fae5;
    color: #065f46;
    border-color: #d1fae5;
}

input[type=range] {
    accent-color: #2563eb;
}

/* --- DROPDOWN --- */
.wrap {
    min-height: 36px !important;
}

button.primary {
    background: #2563eb !important;
    border-radius: 8px !important;
    transition: background 0.2s;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
}

button.primary:hover {
    background: #1d4ed8 !important;
}

button.secondary {
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}

footer { display: none !important; }
"""


def load_models_config(config_path: str) -> Dict[str, Any]:
    """
    从配置文件加载模型信息

    支持两种配置格式：
    1. llm_data 格式：包含 name, model, api_endpoint, service 等字段
    2. llms 格式：包含 provider, model, base_url 等字段

    Args:
        config_path: YAML 配置文件路径

    Returns:
        包含模型信息的字典
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    models_info = {}

    # 尝试 llm_data 格式
    if "llm_data" in config:
        for model_key, model_data in config["llm_data"].items():
            models_info[model_key] = {
                "name": model_data.get("name", model_key),
                "model": model_data.get("model", model_key),
                "api_endpoint": model_data.get("api_endpoint", config.get("api_endpoint")),
                "service": model_data.get("service"),
                "key": model_key,
            }
        return models_info

    # 尝试 llms 格式 (openclaw_router 格式)
    if "llms" in config:
        for model_key, model_data in config["llms"].items():
            models_info[model_key] = {
                "name": model_data.get("description", model_key),
                "model": model_data.get("model", model_key),
                "api_endpoint": model_data.get("base_url"),
                "service": model_data.get("provider"),
                "key": model_key,
            }
        return models_info

    raise ValueError(f"Config file must contain 'llm_data' or 'llms' section")


def predict_model(
    message: str,
    model_info: Dict[str, Any],
    temperature: float = 0.8,
    max_tokens: int = 1024,
) -> str:
    """
    调用指定模型生成响应

    Args:
        message: 用户消息
        model_info: 模型信息字典
        temperature: 生成温度
        max_tokens: 最大生成 token 数

    Returns:
        模型响应文本
    """
    try:
        api_model_name = model_info.get("model", model_info["key"])
        api_endpoint = model_info.get("api_endpoint")
        service = model_info.get("service")

        request = {
            "api_endpoint": api_endpoint,
            "query": message,
            "model_name": model_info["key"],
            "api_name": api_model_name,
        }

        if service:
            request["service"] = service

        result = call_api(request, max_tokens=max_tokens, temperature=temperature)
        response = result.get("response", "No response generated")

        return response

    except Exception as e:
        import traceback
        return f"Error: {str(e)}\n{traceback.format_exc()}"


def predict_both(
    message: str,
    model1_info: Dict[str, Any],
    model2_info: Dict[str, Any],
    temperature: float = 0.8,
    max_tokens: int = 1024,
) -> tuple[str, str]:
    """
    同时调用两个模型并返回响应

    Args:
        message: 用户消息
        model1_info: 模型1的信息
        model2_info: 模型2的信息
        temperature: 生成温度
        max_tokens: 最大生成 token 数

    Returns:
        (模型1响应, 模型2响应)
    """
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(
            predict_model, message, model1_info, temperature, max_tokens
        )
        future2 = executor.submit(
            predict_model, message, model2_info, temperature, max_tokens
        )

        response1 = future1.result()
        response2 = future2.result()

    return response1, response2


def stream_response(full_response: str):
    """流式生成响应字符"""
    partial = ""
    for char in full_response:
        partial += char
        yield partial


def create_interface(models_info: Dict[str, Any], args):
    """创建模型对比界面"""

    model_keys = list(models_info.keys())

    # 获取默认选中的模型
    default_model1 = model_keys[0] if len(model_keys) > 0 else None
    default_model2 = model_keys[1] if len(model_keys) > 1 else (model_keys[0] if model_keys else None)

    with gr.Blocks(title="Model Comparison") as demo:

        # 顶部栏
        gr.HTML("""
            <div class="top-bar">
                <h1>Model Comparison</h1>
                <span class="status-badge">LLMRouter</span>
            </div>
        """)

        # 模型对比区域
        with gr.Row():
            # 模型 1
            with gr.Column(scale=1, elem_classes=["model-1"]):
                with gr.Column(elem_classes=["model-card"]):
                    gr.HTML("""
                        <div class="model-card-header">
                            <h3 class="model-card-title">Model A</h3>
                            <span class="status-badge">Model 1</span>
                        </div>
                    """)
                    model1_select = gr.Dropdown(
                        choices=model_keys,
                        value=default_model1,
                        label="Select Model",
                        interactive=True,
                    )
                    chatbot1 = gr.Chatbot(
                        height=320,
                        show_label=False,
                        elem_classes=["chat-area"],
                    )
                    clear1_btn = gr.Button("Clear", size="sm", variant="secondary")

            # 模型 2
            with gr.Column(scale=1, elem_classes=["model-2"]):
                with gr.Column(elem_classes=["model-card"]):
                    gr.HTML("""
                        <div class="model-card-header">
                            <h3 class="model-card-title">Model B</h3>
                            <span class="status-badge">Model 2</span>
                        </div>
                    """)
                    model2_select = gr.Dropdown(
                        choices=model_keys,
                        value=default_model2,
                        label="Select Model",
                        interactive=True,
                    )
                    chatbot2 = gr.Chatbot(
                        height=320,
                        show_label=False,
                        elem_classes=["chat-area"],
                    )
                    clear2_btn = gr.Button("Clear", size="sm", variant="secondary")

        # 输入区域
        with gr.Row():
            with gr.Column():
                with gr.Column(elem_classes=["input-section"]):
                    msg = gr.Textbox(
                        placeholder="Type a message to compare model responses...",
                        label="Input",
                        lines=3,
                        max_lines=10,
                    )
                    with gr.Row(elem_classes=["input-row"]):
                        submit_btn = gr.Button("Compare", variant="primary", scale=2)
                        submit_alt_btn = gr.Button("Send Separately", scale=1)

                    with gr.Row(elem_classes=["action-btns"]):
                        clear_all_btn = gr.Button("Clear All", size="sm")
                        swap_models_btn = gr.Button("Swap Models", size="sm")

        # 获取当前选中的模型信息
        def get_model_info(model_key: str) -> Dict[str, Any]:
            return models_info.get(model_key, {})

        # 流式响应生成器
        def stream_chatbot_response(chatbot: List[Dict], full_response: str):
            if not chatbot or chatbot[-1].get("role") != "assistant":
                return chatbot

            partial = ""
            for char in full_response:
                partial += char
                chatbot[-1]["content"] = partial
                yield chatbot

        # 提交查询 - 并行模式
        def submit_parallel(message: str, chat1: List[Dict], chat2: List[Dict], model1: str, model2: str):
            if not message.strip():
                return "", chat1, chat2

            # 添加用户消息到两个聊天框
            new_chat1 = chat1 + [{"role": "user", "content": message}, {"role": "assistant", "content": ""}]
            new_chat2 = chat2 + [{"role": "user", "content": message}, {"role": "assistant", "content": ""}]

            # 获取模型信息
            info1 = get_model_info(model1)
            info2 = get_model_info(model2)

            # 调用两个模型
            response1, response2 = predict_both(message, info1, info2, args.temperature, args.max_tokens)

            # 流式输出
            partial = ""
            for char in response1:
                partial += char
                new_chat1[-1]["content"] = partial
                yield "", new_chat1, new_chat2

            partial = ""
            for char in response2:
                partial += char
                new_chat2[-1]["content"] = partial
                yield "", new_chat1, new_chat2

        # 提交查询 - 分别模式
        def submit_sequential(message: str, chat1: List[Dict], chat2: List[Dict], model1: str, model2: str):
            if not message.strip():
                return "", chat1, chat2

            # 获取模型信息
            info1 = get_model_info(model1)
            info2 = get_model_info(model2)

            # 调用两个模型（并行但分别流式输出）
            response1, response2 = predict_both(message, info1, info2, args.temperature, args.max_tokens)

            # 先显示模型1
            new_chat1 = chat1 + [{"role": "user", "content": message}, {"role": "assistant", "content": ""}]
            partial = ""
            for char in response1:
                partial += char
                new_chat1[-1]["content"] = partial
                yield "", new_chat1, chat2

            # 再显示模型2
            new_chat2 = chat2 + [{"role": "user", "content": message}, {"role": "assistant", "content": ""}]
            partial = ""
            for char in response2:
                partial += char
                new_chat2[-1]["content"] = partial
                yield "", new_chat1, new_chat2

        # 交换模型选择
        def swap_models(model1: str, model2: str):
            return model2, model1

        # 清除聊天框
        def clear_chat():
            return []

        # 事件绑定
        submit_btn.click(
            submit_parallel,
            [msg, chatbot1, chatbot2, model1_select, model2_select],
            [msg, chatbot1, chatbot2],
        )

        submit_alt_btn.click(
            submit_sequential,
            [msg, chatbot1, chatbot2, model1_select, model2_select],
            [msg, chatbot1, chatbot2],
        )

        clear1_btn.click(clear_chat, None, chatbot1)
        clear2_btn.click(clear_chat, None, chatbot2)
        clear_all_btn.click(lambda: ([], []), None, [chatbot1, chatbot2])

        swap_models_btn.click(swap_models, [model1_select, model2_select], [model1_select, model2_select])

    return demo


def main():
    """模型对比界面的主入口函数"""
    # 获取脚本所在目录的父目录（项目根目录）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    default_config = os.path.join(project_root, "openclaw_router", "config.yaml")

    parser = argparse.ArgumentParser(
        description="Model Comparison Interface for LLMRouter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Use default config (openclaw_router/config.yaml)
  %(prog)s --config your_config.yaml
  %(prog)s --temperature 0.7 --max_tokens 2048
  %(prog)s --port 8080 --share
        """,
    )
    parser.add_argument(
        "--config",
        type=str,
        default=default_config,
        help=f"Path to YAML configuration file (default: {default_config})",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.8,
        help="Temperature for text generation (default: 0.8)",
    )
    parser.add_argument(
        "--max_tokens",
        type=int,
        default=1024,
        help="Maximum tokens for generation (default: 1024)",
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
        default=8021,
        help="Port to bind the server to (default: 8002)",
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public shareable link",
    )

    args = parser.parse_args()

    # 打印启动横幅
    print("\n" + "=" * 60)
    print("Model Comparison Interface")
    print("=" * 60)
    print(f"  Config:     {args.config}")
    print(f"  Port:       {args.port}")
    print(f"  Temperature: {args.temperature}")
    print(f"  Max Tokens: {args.max_tokens}")
    print("=" * 60 + "\n")

    # 加载模型配置
    print("Loading model configurations...")
    models_info = load_models_config(args.config)

    if not models_info:
        print("No models found in config file!")
        print("Please ensure the config file contains 'llm_data' or 'llms' section.")
        return

    print(f"Loaded {len(models_info)} models:")
    for model_key, model_info in models_info.items():
        model_name = model_info.get("name", model_key)
        print(f"   - {model_key}: {model_name}")
    print()

    # 创建并启动界面
    print("Starting web interface...")
    demo = create_interface(models_info, args)
    demo.queue().launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        show_error=True,
        css=CUSTOM_CSS,
        theme=gr.themes.Default(),
    )


if __name__ == "__main__":
    main()

"""
LLMRouter Main CLI Entry Point

This script provides a unified command-line interface for LLMRouter.
It integrates training, inference, and chat functionalities through subcommands.

LLMRouter 主命令行入口点

本脚本提供 LLMRouter 的统一命令行界面。
通过子命令集成训练、推理和聊天功能。
"""

import argparse
import sys
from typing import List, Optional


def print_banner():
    """Print LLMRouter banner."""
    # 打印 LLMRouter 启动横幅
    banner = """
    TPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPW
    Q                        LLMRouter                          Q
    Q          Intelligent Model Routing for LLMs               Q
    ZPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP]
    """
    print(banner)


def train_command(args):
    """Execute the train subcommand."""
    from llmrouter.cli.router_train import train_router, get_device

    # Determine device
    # 确定训练设备
    device = get_device(args.device if args.device != "auto" else None)

    # Train router
    # 训练路由器模型
    verbose = not args.quiet
    try:
        train_router(
            router_name=args.router,
            config_path=args.config,
            device=device,
            verbose=verbose,
        )
    except Exception as e:
        # 错误处理：捕获并显示训练异常
        print(f"\nError: {str(e)}", file=sys.stderr)
        if verbose:
            import traceback
            print("\nTraceback:", file=sys.stderr)
            traceback.print_exc()
        sys.exit(1)


def infer_command(args):
    """Execute the infer subcommand."""
    import os
    from llmrouter.cli.router_inference import (
        load_router,
        route_query,
        infer_query,
        load_queries_from_file,
        save_results_to_file,
    )

    # Validate config file
    # 验证配置文件是否存在
    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    # Load router
    # 加载路由器模型
    if args.verbose:
        print(f"Loading router: {args.router}", file=sys.stderr)
        print(f"Using config: {args.config}", file=sys.stderr)

    try:
        router_instance = load_router(args.router, args.config, args.load_model_path)
        if args.verbose:
            print("Router loaded successfully!", file=sys.stderr)
    except Exception as e:
        # 错误处理：捕获并显示路由器加载异常
        print(f"Error loading router: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine queries
    # 确定查询来源：命令行参数或输入文件
    if args.query:
        queries = [args.query]
    else:
        if not os.path.exists(args.input):
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        try:
            queries = load_queries_from_file(args.input)
            if args.verbose:
                print(f"Loaded {len(queries)} queries from {args.input}", file=sys.stderr)
        except Exception as e:
            # 错误处理：捕获并显示查询加载异常
            print(f"Error loading queries from file: {e}", file=sys.stderr)
            sys.exit(1)

    # Process queries
    # 处理所有查询
    results = []
    for i, query in enumerate(queries):
        if args.verbose:
            print(f"\nProcessing query {i+1}/{len(queries)}: {query[:50]}...", file=sys.stderr)

        # 根据参数选择仅路由或完整推理
        if args.route_only:
            result = route_query(query, router_instance, args.router)
        else:
            result = infer_query(
                query,
                router_instance,
                args.router,
                temperature=args.temp,
                max_tokens=args.max_tokens,
            )

        results.append(result)

        if args.verbose:
            if result["success"]:
                if args.route_only:
                    print(f"Routed to: {result.get('model_name')}", file=sys.stderr)
                else:
                    print(f"Response generated", file=sys.stderr)
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)

    # Output results
    # 输出结果：保存到文件或打印到标准输出
    if args.output:
        try:
            save_results_to_file(results, args.output, args.output_format)
            if args.verbose:
                print(f"\nResults saved to {args.output}", file=sys.stderr)
        except Exception as e:
            # 错误处理：捕获并显示结果保存异常
            print(f"Error saving results: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Print to stdout
        # 打印到标准输出
        import json
        if len(results) == 1:
            print(json.dumps(results[0], indent=2, ensure_ascii=False))
        else:
            print(json.dumps(results, indent=2, ensure_ascii=False))


def chat_command(args):
    """Execute the chat subcommand."""
    import os
    try:
        import gradio as gr
    except ImportError:
        # 错误处理：检查 gradio 依赖是否安装
        print("Error: gradio is required for chat interface. Install it with:", file=sys.stderr)
        print("  pip install gradio", file=sys.stderr)
        sys.exit(1)

    from llmrouter.cli.router_chat import load_router, predict

    # Validate config file
    # 验证配置文件是否存在
    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    # Load router
    # 加载路由器模型
    print(f"Loading router: {args.router}")
    print(f"Using config: {args.config}")
    if args.load_model_path:
        print(f"Overriding model path: {args.load_model_path}")

    try:
        router_instance = load_router(args.router, args.config, args.load_model_path)
        print("Router loaded successfully!")
    except Exception as e:
        # 错误处理：捕获并显示路由器加载异常
        print(f"Error loading router: {e}", file=sys.stderr)
        sys.exit(1)

    # Create predict function with router instance bound
    # 创建绑定路由器实例的预测函数
    def predict_with_router(message, history, temperature, mode, top_k):
        return predict(message, history, router_instance, args.router, temperature, mode, top_k)

    # Create and launch chat interface
    # 创建并启动聊天界面
    interface = gr.ChatInterface(
        predict_with_router,
        additional_inputs=[
            gr.Slider(
                label="Temperature",
                minimum=0,
                maximum=2,
                value=args.temp,
                step=0.1,
            ),
            gr.Radio(
                label="Query Mode",
                choices=["full_context", "current_only", "retrieval"],
                value=args.mode,
                info="Full Context: all history + current query | Current Only: single query | Retrieval: top-k similar queries",
            ),
            gr.Slider(
                label="Top-K (Retrieval Mode)",
                minimum=1,
                maximum=10,
                value=args.top_k,
                step=1,
                info="Number of similar queries to retrieve (only used in retrieval mode)",
            ),
        ],
        title=f"LLMRouter Chat - {args.router}",
        description=f"Chat interface using {args.router} router | Mode: {args.mode}",
    )

    interface.queue().launch(server_name=args.host, server_port=args.port, share=args.share)


def list_routers_command(args):
    """Execute the list-routers subcommand."""
    _ = args  # Unused, kept for API consistency
    from llmrouter.cli.router_train import ROUTER_TRAINER_REGISTRY, UNSUPPORTED_ROUTERS
    from llmrouter.cli.router_inference import ROUTER_REGISTRY

    print("\n" + "=" * 70)
    print("AVAILABLE ROUTERS")
    print("=" * 70)

    # All routers (for inference)
    # 列出所有可用于推理的路由器
    print("\nRouters available for INFERENCE:")
    print("-" * 70)
    for router_name in sorted(ROUTER_REGISTRY.keys()):
        router_class = ROUTER_REGISTRY[router_name]
        print(f"  {router_name:25s} - {router_class.__name__}")

    # Trainable routers
    # 列出所有可用于训练的路由器
    print("\nRouters available for TRAINING:")
    print("-" * 70)
    for router_name in sorted(ROUTER_TRAINER_REGISTRY.keys()):
        router_class, trainer_class = ROUTER_TRAINER_REGISTRY[router_name]
        print(f"  {router_name:25s} - {router_class.__name__} / {trainer_class.__name__}")

    # Non-trainable routers
    # 列出不支持训练的路由器
    if UNSUPPORTED_ROUTERS:
        print("\nRouters NOT available for training:")
        print("-" * 70)
        for router_name, reason in sorted(UNSUPPORTED_ROUTERS.items()):
            print(f"  {router_name:25s} - {reason}")

    print("\n" + "=" * 70)


def version_command(args):
    """Execute the version subcommand."""
    _ = args  # Unused, kept for API consistency
    try:
        import llmrouter
        version = getattr(llmrouter, "__version__", "unknown")
    except Exception:
        # 错误处理：版本号获取失败时使用默认值
        version = "unknown"

    print(f"LLMRouter version: {version}")


def serve_command(args):
    """Execute the serve subcommand."""
    import os

    # Check dependencies
    # 检查依赖是否安装
    try:
        import fastapi
        import uvicorn
        import httpx
    except ImportError:
        print("Error: FastAPI dependencies required. Install with:", file=sys.stderr)
        print("  pip install fastapi uvicorn httpx", file=sys.stderr)
        sys.exit(1)

    from openclaw_router import run_server, create_app, OpenClawConfig

    # Load config
    # 加载配置文件
    config = None
    if args.config:
        if not os.path.exists(args.config):
            print(f"Error: Config file not found: {args.config}", file=sys.stderr)
            sys.exit(1)
        config = OpenClawConfig.from_yaml(args.config)
    else:
        config = OpenClawConfig()

    # Override config with CLI args
    # 使用命令行参数覆盖配置文件
    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port
    if args.router:
        config.router.strategy = "llmrouter"
        config.router.llmrouter_name = args.router
    if args.router_config:
        config.router.llmrouter_config = args.router_config
    if args.no_prefix:
        config.show_model_prefix = False

    # Create and run app
    # 创建并运行 FastAPI 应用
    app = create_app(config=config)
    run_server(app, host=config.host, port=config.port)


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    try:
        import llmrouter
        cli_version = getattr(llmrouter, "__version__", "unknown")
    except Exception:
        cli_version = "unknown"

    # Create main parser
    # 创建主参数解析器
    parser = argparse.ArgumentParser(
        description="LLMRouter - Intelligent Model Routing for Large Language Models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train a router
  llmrouter train --router knnrouter --config configs/model_config_train/knnrouter.yaml

  # Perform inference
  llmrouter infer --router knnrouter --config config.yaml --query "What is AI?"

  # Launch chat interface
  llmrouter chat --router knnrouter --config config.yaml

  # Start OpenAI-compatible API server (OpenClaw Router for OpenClaw integration)
  llmrouter serve --config configs/openclaw_example.yaml

  # List all available routers
  llmrouter list-routers

For more information on each subcommand, use:
  llmrouter <subcommand> --help
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"LLMRouter CLI v{cli_version}",
        help="Show version and exit",
    )

    # Create subcommands parser
    # 创建子命令解析器
    subparsers = parser.add_subparsers(
        title="subcommands",
        description="Available commands",
        dest="command",
        help="Command to execute",
    )

    # ========== TRAIN SUBCOMMAND ==========
    # ========== 训练子命令 ==========
    train_parser = subparsers.add_parser(
        "train",
        help="Train a router model",
        description="Train a router model with the specified configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    train_parser.add_argument(
        "--router",
        type=str,
        required=True,
        help="Router method name (e.g., knnrouter, mlprouter)",
    )
    train_parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to YAML configuration file for training",
    )
    train_parser.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["cuda", "cpu", "auto"],
        help="Device to use for training (default: auto-detect)",
    )
    train_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output",
    )
    train_parser.set_defaults(func=train_command)

    # ========== INFER SUBCOMMAND ==========
    # ========== 推理子命令 ==========
    infer_parser = subparsers.add_parser(
        "infer",
        help="Perform inference with a router",
        description="Perform inference using a trained router model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    infer_parser.add_argument(
        "--router",
        type=str,
        required=True,
        help="Router method name",
    )
    infer_parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to YAML configuration file",
    )

    # Query input (mutually exclusive)
    # 查询输入（互斥参数组）
    query_group = infer_parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument(
        "--query",
        type=str,
        help="Single query string for inference",
    )
    query_group.add_argument(
        "--input",
        type=str,
        help="Path to input file containing queries",
    )

    infer_parser.add_argument(
        "--load_model_path",
        type=str,
        default=None,
        help="Optional path to override model_path.load_model_path in config",
    )
    infer_parser.add_argument(
        "--route-only",
        action="store_true",
        help="Only perform routing without calling API",
    )
    infer_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output file (default: print to stdout)",
    )
    infer_parser.add_argument(
        "--output-format",
        type=str,
        choices=["json", "jsonl"],
        default="json",
        help="Output format for batch inference (default: json)",
    )
    infer_parser.add_argument(
        "--temp",
        type=float,
        default=0.8,
        help="Temperature for text generation (default: 0.8)",
    )
    infer_parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Maximum tokens for generation (default: 1024)",
    )
    infer_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose output",
    )
    infer_parser.set_defaults(func=infer_command)

    # ========== CHAT SUBCOMMAND ==========
    # ========== 聊天子命令 ==========
    chat_parser = subparsers.add_parser(
        "chat",
        help="Launch interactive chat interface",
        description="Launch a Gradio-based chat interface for interactive conversations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    chat_parser.add_argument(
        "--router",
        type=str,
        required=True,
        help="Router method name",
    )
    chat_parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to YAML configuration file",
    )
    chat_parser.add_argument(
        "--load_model_path",
        type=str,
        default=None,
        help="Optional path to override model_path.load_model_path in config",
    )
    chat_parser.add_argument(
        "--temp",
        type=float,
        default=0.8,
        help="Default temperature for text generation (default: 0.8)",
    )
    chat_parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host to bind the server to (default: None, all interfaces)",
    )
    chat_parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port to bind the server to (default: 8001)",
    )
    chat_parser.add_argument(
        "--mode",
        type=str,
        default="current_only",
        choices=["full_context", "current_only", "retrieval"],
        help="Default query mode (default: current_only)",
    )
    chat_parser.add_argument(
        "--top_k",
        type=int,
        default=3,
        help="Number of similar queries to retrieve in retrieval mode (default: 3)",
    )
    chat_parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public shareable link",
    )
    chat_parser.set_defaults(func=chat_command)

    # ========== LIST-ROUTERS SUBCOMMAND ==========
    # ========== 列出路由器子命令 ==========
    list_parser = subparsers.add_parser(
        "list-routers",
        help="List all available routers",
        description="Display all available router models and their capabilities",
    )
    list_parser.set_defaults(func=list_routers_command)

    # ========== VERSION SUBCOMMAND ==========
    # ========== 版本信息子命令 ==========
    version_parser = subparsers.add_parser(
        "version",
        help="Show version information",
        description="Display LLMRouter version information",
    )
    version_parser.set_defaults(func=version_command)

    # ========== SERVE SUBCOMMAND ==========
    # ========== 服务子命令（启动 API 服务器）==========
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start OpenAI-compatible API server (OpenClaw Router)",
        description="Start an OpenAI-compatible API server with intelligent routing. "
                    "Supports built-in strategies (random, rules, round_robin, llm) and "
                    "LLMRouter ML-based routers (knnrouter, mlprouter, thresholdrouter, etc.). "
                    "Can be directly integrated with OpenClaw and other OpenAI-compatible clients.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with a config file
  llmrouter serve --config configs/openclaw_example.yaml

  # Use a specific LLMRouter ML-based router
  llmrouter serve --config config.yaml --router knnrouter --router-config configs/knnrouter.yaml

  # Custom port
  llmrouter serve --config config.yaml --port 9000

Routing Strategies (in config.yaml):
  Built-in:
    - random: Random model selection (with optional weights)
    - round_robin: Rotate through models
    - rules: Keyword-based routing
    - llm: Use an LLM to decide

  LLMRouter ML-based (use --router flag or strategy: llmrouter):
    - knnrouter, mlprouter, svmrouter, mfrouter
    - thresholdrouter, randomrouter (custom_routers/)
    - And more...

OpenClaw Integration:
  In ~/.openclaw/openclaw.json, add:
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
        """
    )
    serve_parser.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="Path to YAML configuration file",
    )
    serve_parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    serve_parser.add_argument(
        "--port", "-p",
        type=int,
        default=None,
        help="Port to bind the server to (default: 8000)",
    )
    serve_parser.add_argument(
        "--router",
        type=str,
        default=None,
        help="Router to use (e.g., randomrouter, thresholdrouter)",
    )
    serve_parser.add_argument(
        "--router-config",
        type=str,
        default=None,
        help="Path to router-specific config file",
    )
    serve_parser.add_argument(
        "--no-prefix",
        action="store_true",
        help="Disable model name prefix in responses",
    )
    serve_parser.set_defaults(func=serve_command)

    return parser


def main(argv: Optional[List[str]] = None):
    """Main entry point for LLMRouter CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # If no subcommand is provided, show help
    # 如果没有提供子命令，显示帮助信息
    if not hasattr(args, "func"):
        print_banner()
        parser.print_help()
        sys.exit(0)

    # Execute the appropriate subcommand
    # 执行对应的子命令
    args.func(args)


if __name__ == "__main__":
    main()

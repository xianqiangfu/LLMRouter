"""
Router Inference Script for LLMRouter

This script provides non-interactive inference functionality for LLMRouter.
It supports single query inference, batch inference from file, and various output modes.
"""

import atexit
import argparse
import json
import os
import multiprocessing as mp
import sys
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path

def _configure_multiprocessing() -> None:
    """确保 vLLM 工作进程使用 CUDA 安全的多进程方式"""
    os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
    try:
        mp.set_start_method("spawn")
    except RuntimeError:
        pass


_configure_multiprocessing()

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
from llmrouter.utils import call_api


def _safe_unlink(path: str) -> None:
    """安全删除文件，如果文件不存在则忽略错误"""
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


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

if GMTRouter is not None:
    ROUTER_REGISTRY["gmtrouter"] = GMTRouter
    ROUTER_REGISTRY["gmt_router"] = GMTRouter

if PersonalizedRouter is not None:
    ROUTER_REGISTRY["personalizedrouter"] = PersonalizedRouter
    ROUTER_REGISTRY["personalized_router"] = PersonalizedRouter

# Add RouterR1 if available
if RouterR1 is not None:
    ROUTER_REGISTRY["router_r1"] = RouterR1
    ROUTER_REGISTRY["router-r1"] = RouterR1

# Routers that have full pipeline in route_single (multi-round/agentic routers)
# These routers return response directly from route_single, no separate API call needed
MULTI_ROUND_ROUTERS = {
    "llmmultiroundrouter",
    "knnmultiroundrouter",
}

# Routers that require special handling
ROUTERS_REQUIRING_SPECIAL_ARGS = {
    "router_r1",
    "router-r1",
}

# Routers that are not supported
UNSUPPORTED_ROUTERS = {}


# ============================================================================
# Plugin System Integration
# ============================================================================
# Automatically discover and register custom routers from plugin directories
try:
    from llmrouter.plugin_system import discover_and_register_plugins

    # Discover plugins (verbose=False by default, set to True for debugging)
    plugin_registry = discover_and_register_plugins(verbose=False)

    # Register custom routers into ROUTER_REGISTRY
    for router_name, router_class in plugin_registry.discovered_routers.items():
        # Handle both (router, trainer) tuple and single router class
        if isinstance(router_class, tuple):
            ROUTER_REGISTRY[router_name] = router_class[0]  # Only router class for inference
        else:
            ROUTER_REGISTRY[router_name] = router_class

except ImportError:
    # Plugin system not available, continue without custom routers
    pass
# ============================================================================


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

    # 检查路由器是否不支持推理
    if router_name_lower in UNSUPPORTED_ROUTERS:
        raise ValueError(
            f"Router '{router_name}' is not supported for inference. "
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


def route_query(
    query: str,
    router_instance: Any,
    router_name: str,
) -> Dict[str, Any]:
    """
    路由单个查询并返回路由决策

    Args:
        query: 输入查询字符串
        router_instance: 已加载的路由器实例
        router_name: 路由器方法名称

    Returns:
        包含路由结果的字典
    """
    router_name_lower = router_name.lower()

    # 多轮路由器和 RouterR1 不支持 --route-only
    # 因为它们在内部执行完整的推理流程
    if router_name_lower in ROUTERS_REQUIRING_SPECIAL_ARGS:
        return {
            "success": False,
            "query": query,
            "error": f"Router '{router_name}' does not support --route-only; run without --route-only.",
        }

    if router_name_lower in MULTI_ROUND_ROUTERS:
        return {
            "success": False,
            "query": query,
            "error": f"Router '{router_name}' is a multi-round router with full pipeline; --route-only is not supported.",
        }

    try:
        # 执行查询路由
        query_input = {"query": query}
        routing_result = router_instance.route_single(query_input)

        # 从路由结果中提取模型名称
        model_name = (
            routing_result.get("model_name")
            or routing_result.get("predicted_llm")
            or routing_result.get("predicted_llm_name")
        )

        if not model_name:
            return {
                "success": False,
                "error": "Router did not return a model name",
                "routing_result": routing_result,
            }

        return {
            "success": True,
            "query": query,
            "model_name": model_name,
            "routing_result": routing_result,
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "query": query,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


def infer_query(
    query: str,
    router_instance: Any,
    router_name: str,
    temperature: float = 0.8,
    max_tokens: int = 1024,
) -> Dict[str, Any]:
    """
    执行完整推理：路由查询 + 调用 API + 返回响应

    Args:
        query: 输入查询字符串
        router_instance: 已加载的路由器实例
        router_name: 路由器方法名称
        temperature: 生成温度参数
        max_tokens: 最大生成令牌数

    Returns:
        包含推理结果的字典
    """
    router_name_lower = router_name.lower()

    # 检查路由器是否为多轮路由器（在 route_single 中执行完整流程）
    if router_name_lower in MULTI_ROUND_ROUTERS:
        # 多轮路由器执行完整流程：分解 + 路由 + 执行 + 聚合
        # 它们的 route_single 直接返回响应（聊天模式下返回字符串，评估模式下返回字典）
        try:
            result = router_instance.route_single(query)
            # route_single 对简单查询返回字符串，对评估模式返回字典
            if isinstance(result, str):
                return {
                    "success": True,
                    "query": query,
                    "response": result,
                    "model_name": "multi-round-pipeline",
                    "method": "multi_round_router",
                }
            else:
                # 包含响应、令牌数等信息的字典结果
                return {
                    "success": result.get("success", True),
                    "query": query,
                    "response": result.get("response", ""),
                    "model_name": "multi-round-pipeline",
                    "prompt_tokens": result.get("prompt_tokens", 0),
                    "completion_tokens": result.get("completion_tokens", 0),
                    "method": "multi_round_router",
                }
        except Exception as e:
            import traceback
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

    # 特殊处理 RouterR1（需要 model_id、api_base、api_key）
    if router_name_lower in ROUTERS_REQUIRING_SPECIAL_ARGS:
        try:
            # 从配置中获取必需参数
            cfg = getattr(router_instance, "cfg", {}) or {}
            hparam = cfg.get("hparam", {}) or {}
            api_base = hparam.get("api_base") or getattr(router_instance, "api_base", None)
            api_key = hparam.get("api_key") or getattr(router_instance, "api_key", None)

            if not api_key or not api_base:
                return {
                    "success": False,
                    "query": query,
                    "error": "RouterR1 requires api_key and api_base in yaml config",
                }

            # RouterR1 的 route_single 返回响应
            result = router_instance.route_single({"query": query})
            return {
                "success": True,
                "query": query,
                "response": result,
                "method": "router_r1",
            }

        except Exception as e:
            import traceback
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

    # 否则，使用 route_single 获取路由决策，然后调用模型
    try:
        # 执行查询路由
        query_input = {"query": query}
        routing_result = router_instance.route_single(query_input)

        # 从路由结果中提取模型名称
        model_name = (
            routing_result.get("model_name")
            or routing_result.get("predicted_llm")
            or routing_result.get("predicted_llm_name")
        )

        if not model_name:
            return {
                "success": False,
                "query": query,
                "error": "Router did not return a model name",
                "routing_result": routing_result,
            }

        # 从 llm_data 获取 API 端点和模型名称（如果可用）
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
            return {
                "success": False,
                "query": query,
                "error": f"API endpoint not found for model '{model_name}'. Please specify 'api_endpoint' in llm_data JSON for this model or in router YAML config.",
                "routing_result": routing_result,
            }

        # 通过 API 调用路由到的模型
        request = {
            "api_endpoint": api_endpoint,
            "query": query,
            "model_name": model_name,  # 保留原始名称用于路由器识别
            "api_name": api_model_name,  # 使用完整的 API 模型路径
        }
        # 如果可用则添加 service 字段（用于服务特定的 API 密钥选择）
        if service:
            request["service"] = service

        result = call_api(request, max_tokens=max_tokens, temperature=temperature)

        response = result.get("response", "No response generated")

        return {
            "success": True,
            "query": query,
            "model_name": model_name,
            "api_model_name": api_model_name,
            "response": response,
            "routing_result": routing_result,
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "query": query,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


def load_queries_from_file(file_path: str) -> List[str]:
    """
    从文件中加载查询

    支持格式：
    - 纯文本文件（每行一个查询）
    - JSON 文件（字符串列表或包含 "query" 字段的字典列表）
    - JSONL 文件（每行一个包含 "query" 字段的 JSON 对象）

    Args:
        file_path: 输入文件路径

    Returns:
        查询字符串列表
    """
    file_ext = Path(file_path).suffix.lower()

    with open(file_path, "r", encoding="utf-8") as f:
        if file_ext == ".json":
            data = json.load(f)
            if isinstance(data, list):
                if all(isinstance(item, str) for item in data):
                    return data
                elif all(isinstance(item, dict) and "query" in item for item in data):
                    return [item["query"] for item in data]
                else:
                    raise ValueError("JSON file must contain list of strings or list of dicts with 'query' field")
            else:
                raise ValueError("JSON file must contain a list")

        elif file_ext == ".jsonl":
            queries = []
            for line in f:
                line = line.strip()
                if line:
                    obj = json.loads(line)
                    if isinstance(obj, dict) and "query" in obj:
                        queries.append(obj["query"])
                    elif isinstance(obj, str):
                        queries.append(obj)
                    else:
                        raise ValueError("JSONL line must be dict with 'query' field or string")
            return queries

        else:
            # 纯文本文件，每行一个查询
            return [line.strip() for line in f if line.strip()]


def save_results_to_file(results: List[Dict[str, Any]], output_path: str, output_format: str = "json"):
    """
    将结果保存到文件

    Args:
        results: 结果字典列表
        output_path: 输出文件路径
        output_format: 输出格式 - "json" 或 "jsonl"
    """
    with open(output_path, "w", encoding="utf-8") as f:
        if output_format == "jsonl":
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        else:  # json
            json.dump(results, f, indent=2, ensure_ascii=False)


def main():
    """路由器推理的主入口函数"""
    parser = argparse.ArgumentParser(
        description="Router Inference Script for LLMRouter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single query inference
  python router_inference.py --router knnrouter --config config.yaml --query "What is machine learning?"

  # Batch inference from file
  python router_inference.py --router knnrouter --config config.yaml --input queries.txt --output results.json

  # Route only (no API call)
  python router_inference.py --router knnrouter --config config.yaml --query "Hello" --route-only
        """
    )

    # 必需参数
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

    # 查询输入参数
    query_group = parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument(
        "--query",
        type=str,
        help="Single query string for inference",
    )
    query_group.add_argument(
        "--input",
        type=str,
        help="Path to input file containing queries (supports .txt, .json, .jsonl)",
    )

    # 可选参数
    parser.add_argument(
        "--load_model_path",
        type=str,
        default=None,
        help="Optional path to override model_path.load_model_path in config",
    )
    parser.add_argument(
        "--route-only",
        action="store_true",
        help="Only perform routing without calling API (faster)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output file (default: print to stdout)",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["json", "jsonl"],
        default="json",
        help="Output format for batch inference (default: json)",
    )
    parser.add_argument(
        "--temp",
        type=float,
        default=0.8,
        help="Temperature for text generation (default: 0.8)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Maximum tokens for generation (default: 1024)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose output",
    )

    args = parser.parse_args()

    # 验证配置文件是否存在
    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    # 加载路由器
    if args.verbose:
        print(f"Loading router: {args.router}", file=sys.stderr)
        print(f"Using config: {args.config}", file=sys.stderr)
        if args.load_model_path:
            print(f"Overriding model path: {args.load_model_path}", file=sys.stderr)

    try:
        router_instance = load_router(args.router, args.config, args.load_model_path)
        if args.verbose:
            print("Router loaded successfully!", file=sys.stderr)
    except Exception as e:
        print(f"Error loading router: {e}", file=sys.stderr)
        sys.exit(1)

    # 确定查询列表
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
            print(f"Error loading queries from file: {e}", file=sys.stderr)
            sys.exit(1)

    # 处理查询
    results = []
    for i, query in enumerate(queries):
        if args.verbose:
            print(f"\nProcessing query {i+1}/{len(queries)}: {query[:50]}...", file=sys.stderr)

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
                print(f"  └ Error: {result.get('error')}", file=sys.stderr)

    # 输出结果
    if args.output:
        try:
            save_results_to_file(results, args.output, args.output_format)
            if args.verbose:
                print(f"\nResults saved to {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"Error saving results: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # 打印到标准输出
        if len(results) == 1:
            # 单个查询：打印格式化结果
            result = results[0]
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # 多个查询：打印为 JSON 数组
            print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

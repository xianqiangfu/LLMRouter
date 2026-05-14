"""
Router Training Script for LLMRouter

This script provides a unified CLI interface for training different router models.
It supports all router types that have corresponding trainer implementations.
"""

import argparse
import os
import sys
from typing import Dict, Any, Optional, Tuple

# Import router and trainer classes
from llmrouter.models import (
    # Routers
    KNNRouter,
    SVMRouter,
    MLPRouter,
    MFRouter,
    EloRouter,
    DCRouter,
    AutomixRouter,
    HybridLLMRouter,
    GraphRouter,
    CausalLMRouter,
    GMTRouter,
    PersonalizedRouter,
    # Trainers
    KNNRouterTrainer,
    SVMRouterTrainer,
    MLPTrainer,
    MFRouterTrainer,
    EloRouterTrainer,
    DCTrainer,
    AutomixRouterTrainer,
    HybridLLMTrainer,
    GraphTrainer,
    CausalLMTrainer,
    GMTRouterTrainer,
    PersonalizedRouterTrainer,
)

# Import multi-round routers
from llmrouter.models.knnmultiroundrouter import KNNMultiRoundRouter
from llmrouter.models.knnmultiroundrouter import KNNMultiRoundRouterTrainer


# Router registry: maps router method names to (router_class, trainer_class) tuples
ROUTER_TRAINER_REGISTRY: Dict[str, Tuple[Any, Any]] = {
    "knnrouter": (KNNRouter, KNNRouterTrainer),
    "svmrouter": (SVMRouter, SVMRouterTrainer),
    "mlprouter": (MLPRouter, MLPTrainer),
    "mfrouter": (MFRouter, MFRouterTrainer),
    "elorouter": (EloRouter, EloRouterTrainer),
    "dcrouter": (DCRouter, DCTrainer),
    "routerdc": (DCRouter, DCTrainer),
    "automix": (AutomixRouter, AutomixRouterTrainer),
    "automixrouter": (AutomixRouter, AutomixRouterTrainer),
    "hybrid_llm": (HybridLLMRouter, HybridLLMTrainer),
    "hybridllm": (HybridLLMRouter, HybridLLMTrainer),
    "graphrouter": (GraphRouter, GraphTrainer),
    "causallm_router": (CausalLMRouter, CausalLMTrainer),
    "causallmrouter": (CausalLMRouter, CausalLMTrainer),
    "knnmultiroundrouter": (KNNMultiRoundRouter, KNNMultiRoundRouterTrainer),
    "gmtrouter": (GMTRouter, GMTRouterTrainer),
    "gmt_router": (GMTRouter, GMTRouterTrainer),
    "personalizedrouter": (PersonalizedRouter, PersonalizedRouterTrainer),
    "personalized_router": (PersonalizedRouter, PersonalizedRouterTrainer),
}   

# Routers that do not support training
UNSUPPORTED_ROUTERS = {
    "smallest_llm": "SmallestLLM is a baseline router that does not require training",
    "largest_llm": "LargestLLM is a baseline router that does not require training",
    "llmmultiroundrouter": "LLMMultiRoundRouter does not have a trainer implementation",
    "router_r1": "RouterR1 is a pre-trained model and does not support training via this CLI",
    "router-r1": "RouterR1 is a pre-trained model and does not support training via this CLI",
}

# Filter out routers whose optional deps are unavailable
_optional_missing = []
for _name, (_router_cls, _trainer_cls) in list(ROUTER_TRAINER_REGISTRY.items()):
    if _router_cls is None or _trainer_cls is None:
        _optional_missing.append(_name)
        ROUTER_TRAINER_REGISTRY.pop(_name, None)

for _name in _optional_missing:
    UNSUPPORTED_ROUTERS[_name] = (
        "Optional dependencies missing for this router/trainer; "
        "install the extra requirements and try again."
    )


# ============================================================================
# Plugin System Integration
# ============================================================================
# Automatically discover and register custom routers from plugin directories
try:
    from llmrouter.plugin_system import discover_and_register_plugins

    # Discover plugins (verbose=False by default, set to True for debugging)
    plugin_registry = discover_and_register_plugins(verbose=False)

    # Register custom routers into ROUTER_TRAINER_REGISTRY
    for router_name, (router_class, trainer_class) in plugin_registry.discovered_routers.items():
        if trainer_class is not None:
            # Router has a trainer, add to training registry
            ROUTER_TRAINER_REGISTRY[router_name] = (router_class, trainer_class)
        else:
            # Router has no trainer, mark as unsupported for training
            UNSUPPORTED_ROUTERS[router_name] = (
                "Custom router does not have a trainer implementation"
            )

except ImportError:
    # Plugin system not available, continue without custom routers
    pass
# ============================================================================


def get_device(device_arg: Optional[str] = None) -> str:
    """
    确定训练使用的设备

    Args:
        device_arg: 命令行传入的设备参数

    Returns:
        设备字符串（"cuda" 或 "cpu"）
    """
    if device_arg:
        return device_arg

    # 自动检测
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass

    return "cpu"


def load_router_and_trainer(
    router_name: str,
    config_path: str,
    device: str = "cpu",
) -> Tuple[Any, Any]:
    """
    根据路由器名称和配置加载路由器和训练器实例

    Args:
        router_name: 路由器方法名称（如 "knnrouter"、"mlprouter"）
        config_path: YAML 配置文件路径
        device: 训练使用的设备（"cuda" 或 "cpu"）

    Returns:
        (路由器实例, 训练器实例) 元组
    """
    router_name_lower = router_name.lower()

    # 检查路由器是否不支持训练
    if router_name_lower in UNSUPPORTED_ROUTERS:
        raise ValueError(
            f"Router '{router_name}' does not support training.\n"
            f"Reason: {UNSUPPORTED_ROUTERS[router_name_lower]}"
        )

    if router_name_lower not in ROUTER_TRAINER_REGISTRY:
        raise ValueError(
            f"Unknown router: {router_name}.\n"
            f"Supported routers for training: {list(ROUTER_TRAINER_REGISTRY.keys())}"
        )

    router_class, trainer_class = ROUTER_TRAINER_REGISTRY[router_name_lower]

    # 初始化路由器
    try:
        router_instance = router_class(yaml_path=config_path)
    except Exception as e:
        raise ValueError(
            f"Failed to initialize router '{router_name}'.\n"
            f"Error: {str(e)}"
        ) from e

    # 初始化训练器
    try:
        trainer_instance = trainer_class(router=router_instance, device=device)
    except Exception as e:
        raise ValueError(
            f"Failed to initialize trainer for '{router_name}'.\n"
            f"Error: {str(e)}"
        ) from e

    return router_instance, trainer_instance


def train_router(
    router_name: str,
    config_path: str,
    device: str = "cpu",
    verbose: bool = True,
) -> None:
    """
    使用给定配置训练路由器

    Args:
        router_name: 路由器方法名称
        config_path: YAML 配置文件路径
        device: 训练使用的设备
        verbose: 是否打印详细输出
    """
    if verbose:
        print(f"=" * 60)
        print(f"Starting Training for Router: {router_name}")
        print(f"=" * 60)
        print(f"Config file: {config_path}")
        print(f"Device: {device}")
        print(f"=" * 60)

    # 加载路由器和训练器
    if verbose:
        print("\nLoading router and trainer...")

    _, trainer_instance = load_router_and_trainer(
        router_name, config_path, device
    )

    if verbose:
        print("Router and trainer loaded successfully!")

    # 开始训练
    if verbose:
        print(f"\nStarting training for {router_name}...\n")

    try:
        trainer_instance.train()
    except Exception as e:
        raise RuntimeError(f"Training failed: {str(e)}") from e

    if verbose:
        print(f"\nTraining completed for {router_name}!")
        print(f"=" * 60)


def main():
    """路由器训练的主入口函数"""
    parser = argparse.ArgumentParser(
        description="Router Training Script for LLMRouter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train KNN router
  python router_train.py --router knnrouter --config configs/model_config_train/knnrouter.yaml

  # Train MLP router with GPU
  python router_train.py --router mlprouter --config configs/model_config_train/mlprouter.yaml --device cuda

  # Train MF router quietly
  python router_train.py --router mfrouter --config configs/model_config_train/mfrouter.yaml --quiet

Supported routers for training:
  - knnrouter: K-Nearest Neighbors Router
  - svmrouter: Support Vector Machine Router
  - mlprouter: Multi-Layer Perceptron Router
  - mfrouter: Matrix Factorization Router
  - elorouter: Elo Rating Router
  - dcrouter: Divide-and-Conquer Router
  - automix: Automix Router
  - hybrid_llm: Hybrid LLM Router
  - graphrouter: Graph Router
  - causallm_router: Causal Language Model Router
  - knnmultiroundrouter: KNN Multi-Round Router
        """
    )

    # 必需参数
    parser.add_argument(
        "--router",
        type=str,
        required=True,
        help="Router method name (e.g., knnrouter, mlprouter, mfrouter)",
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to YAML configuration file for training",
    )

    # 可选参数
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["cuda", "cpu", "auto"],
        help="Device to use for training (default: auto-detect)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output (only show errors)",
    )
    parser.add_argument(
        "--list-routers",
        action="store_true",
        help="List all supported routers for training and exit",
    )

    args = parser.parse_args()

    # 处理 --list-routers 参数：列出所有支持训练的路由器
    if args.list_routers:
        print("Supported routers for training:")
        print("=" * 60)
        for router_name in sorted(ROUTER_TRAINER_REGISTRY.keys()):
            router_class, trainer_class = ROUTER_TRAINER_REGISTRY[router_name]
            print(f"  • {router_name}")
            print(f"    Router: {router_class.__name__}")
            print(f"    Trainer: {trainer_class.__name__}")
            print()
        print("Unsupported routers:")
        print("=" * 60)
        for router_name, reason in sorted(UNSUPPORTED_ROUTERS.items()):
            print(f"  • {router_name}")
            print(f"    Reason: {reason}")
            print()
        sys.exit(0)

    # 验证配置文件是否存在
    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    # 确定训练设备
    device = get_device(args.device if args.device != "auto" else None)

    # 执行路由器训练
    verbose = not args.quiet
    try:
        train_router(
            router_name=args.router,
            config_path=args.config,
            device=device,
            verbose=verbose,
        )
    except Exception as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        if verbose:
            import traceback
            print("\nTraceback:", file=sys.stderr)
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

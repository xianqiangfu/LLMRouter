"""
LLMRouter 插件系统
====================

该模块提供插件发现和注册系统，允许用户在不修改核心代码库的情况下添加自定义路由器实现。

使用方法：
    1. 创建自定义路由器目录（如 custom_routers/）
    2. 按照 MetaRouter 接口实现路由器
    3. 插件系统将自动发现并注册该路由器

示例目录结构：
    custom_routers/
    ├── __init__.py
    └── my_custom_router/
        ├── __init__.py
        ├── router.py       # 包含 MyCustomRouter 类
        └── trainer.py      # (可选) 包含 MyCustomRouterTrainer 类
"""

import os
import sys
import importlib.util
from pathlib import Path
from typing import Dict, Tuple, Any, Optional, List
import inspect


class PluginRegistry:
    """
    用于管理自定义路由器插件的中心注册表。

    该类处理：
    - 从插件目录中发现自定义路由器
    - 验证路由器实现
    - 注册到路由器和训练器注册表
    """

    def __init__(self):
        """初始化插件注册表。"""
        self.discovered_routers: Dict[str, Tuple[Any, Optional[Any]]] = {}
        self.plugin_paths: List[str] = []

    def discover_plugins(self, plugin_dir: str, verbose: bool = False) -> None:
        """
        从目录中发现并加载路由器插件。

        Args:
            plugin_dir: 包含自定义路由器的目录路径
            verbose: 是否打印发现信息

        目录结构应为：
            plugin_dir/
            ├── __init__.py (可选)
            └── router_name/
                ├── __init__.py
                ├── router.py       # 必须包含继承自 MetaRouter 的 Router 类
                └── trainer.py      # 可选：包含 Trainer 类

        每个路由器模块应通过 __init__.py 导出其主类，
        或在 router.py 中包含以 'Router' 结尾的类名
        """
        plugin_path = Path(plugin_dir)

        if not plugin_path.exists():
            if verbose:
                print(f"⚠️  Plugin directory not found: {plugin_dir}")
            return

        if not plugin_path.is_dir():
            if verbose:
                print(f"⚠️  Plugin path is not a directory: {plugin_dir}")
            return

        # 如果插件目录尚未在 Python 路径中，则添加
        plugin_dir_str = str(plugin_path.resolve())
        if plugin_dir_str not in sys.path:
            sys.path.insert(0, plugin_dir_str)
            self.plugin_paths.append(plugin_dir_str)

        if verbose:
            print(f"\n🔍 Discovering plugins in: {plugin_dir}")
            print("=" * 70)

        # 扫描子目录（每个子目录都是潜在的路由器插件）
        for item in plugin_path.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                self._load_router_from_directory(item, verbose=verbose)

        if verbose:
            print(f"\n✅ Discovered {len(self.discovered_routers)} custom router(s)")
            print("=" * 70)

    def _load_router_from_directory(self, router_dir: Path, verbose: bool = False) -> None:
        """
        从目录加载路由器插件。

        Args:
            router_dir: 路由器插件目录的路径
            verbose: 是否打印加载信息
        """
        router_name = router_dir.name.lower()

        try:
            # 尝试导入路由器模块
            router_class = self._import_router_class(router_dir)
            trainer_class = self._import_trainer_class(router_dir)

            if router_class is None:
                if verbose:
                    print(f"⚠️  Skipped {router_name}: No valid Router class found")
                return

            # 验证路由器类
            if not self._validate_router_class(router_class):
                if verbose:
                    print(f"❌ Skipped {router_name}: Router class validation failed")
                return

            # 注册路由器
            self.discovered_routers[router_name] = (router_class, trainer_class)

            if verbose:
                trainer_info = f" + {trainer_class.__name__}" if trainer_class else ""
                print(f"✅ Loaded: {router_name:25s} -> {router_class.__name__}{trainer_info}")

        except Exception as e:
            if verbose:
                print(f"❌ Error loading {router_name}: {str(e)}")

    def _import_router_class(self, router_dir: Path) -> Optional[Any]:
        """
        从插件目录导入 Router 类。

        尝试多种策略：
        1. 从 __init__.py 导入
        2. 查找 router.py 中以 'Router' 结尾的类
        3. 查找 model.py 中以 'Router' 结尾的类

        Args:
            router_dir: 路由器目录的路径

        Returns:
            Router 类，如果未找到则返回 None
        """
        module_name = router_dir.name

        # 策略 1：尝试从 __init__.py 导入
        try:
            spec = importlib.util.spec_from_file_location(
                module_name,
                router_dir / "__init__.py"
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 查找以 'Router' 结尾的类
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if name.endswith('Router') and not name.startswith('Meta'):
                        return obj
        except (FileNotFoundError, AttributeError, ImportError):
            pass

        # 策略 2：尝试 router.py
        router_file = router_dir / "router.py"
        if router_file.exists():
            try:
                spec = importlib.util.spec_from_file_location(
                    f"{module_name}.router",
                    router_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if name.endswith('Router') and not name.startswith('Meta'):
                            return obj
            except (ImportError, AttributeError):
                pass

        # 策略 3：尝试 model.py
        model_file = router_dir / "model.py"
        if model_file.exists():
            try:
                spec = importlib.util.spec_from_file_location(
                    f"{module_name}.model",
                    model_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if name.endswith('Router') and not name.startswith('Meta'):
                            return obj
            except (ImportError, AttributeError):
                pass

        return None

    def _import_trainer_class(self, router_dir: Path) -> Optional[Any]:
        """
        从插件目录导入 Trainer 类（可选）。

        Args:
            router_dir: 路由器目录的路径

        Returns:
            Trainer 类，如果未找到则返回 None
        """
        module_name = router_dir.name
        trainer_file = router_dir / "trainer.py"

        if not trainer_file.exists():
            return None

        try:
            spec = importlib.util.spec_from_file_location(
                f"{module_name}.trainer",
                trainer_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 查找以 'Trainer' 结尾的类
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if name.endswith('Trainer') and not name.startswith('Base'):
                        return obj
        except (ImportError, AttributeError):
            pass

        return None

    def _validate_router_class(self, router_class: Any) -> bool:
        """
        验证路由器类是否实现了所需的接口。

        Args:
            router_class: 要验证的路由器类

        Returns:
            如果有效则返回 True，否则返回 False
        """
        # 检查是否具有必需的方法
        required_methods = ['route_single', 'route_batch']

        for method_name in required_methods:
            if not hasattr(router_class, method_name):
                return False

        return True

    def register_to_dict(self, target_dict: Dict[str, Any]) -> None:
        """
        将发现的路由器注册到目标注册表字典中。

        Args:
            target_dict: 用于注册路由器的字典
        """
        for router_name, (router_class, trainer_class) in self.discovered_routers.items():
            # 用于推理注册表（仅路由器）
            if trainer_class is None:
                target_dict[router_name] = router_class
            else:
                # 用于训练注册表（路由器 + 训练器元组）
                target_dict[router_name] = (router_class, trainer_class)

    def get_router_names(self) -> List[str]:
        """获取已发现的路由器名称列表。"""
        return list(self.discovered_routers.keys())

    def get_router(self, name: str) -> Optional[Tuple[Any, Optional[Any]]]:
        """
        根据名称获取路由器。

        Args:
            name: 路由器名称

        Returns:
            (RouterClass, TrainerClass) 元组，如果未找到则返回 None
        """
        return self.discovered_routers.get(name.lower())

# 全局插件注册表实例
_global_registry = PluginRegistry()


def discover_and_register_plugins(
    plugin_dirs: Optional[List[str]] = None,
    verbose: bool = False
) -> PluginRegistry:
    """
    从指定目录发现并注册自定义路由器插件。

    Args:
        plugin_dirs: 要扫描插件的目录列表。
                    如果为 None，则使用默认位置：
                    - ./custom_routers/
                    - ~/.llmrouter/plugins/
                    - $LLMROUTER_PLUGINS 环境变量
        verbose: 是否打印发现信息

    Returns:
        包含已发现路由器的 PluginRegistry 实例
    """
    if plugin_dirs is None:
        plugin_dirs = []

        # 默认位置 1：./custom_routers/（相对于当前目录）
        if os.path.exists("custom_routers"):
            plugin_dirs.append("custom_routers")

        # 默认位置 2：~/.llmrouter/plugins/
        home_plugins = Path.home() / ".llmrouter" / "plugins"
        if home_plugins.exists():
            plugin_dirs.append(str(home_plugins))

        # 默认位置 3：环境变量
        env_plugins = os.environ.get("LLMROUTER_PLUGINS")
        if env_plugins:
            plugin_dirs.extend(env_plugins.split(":"))

    # 从所有目录中发现插件
    for plugin_dir in plugin_dirs:
        _global_registry.discover_plugins(plugin_dir, verbose=verbose)

    return _global_registry


def get_plugin_registry() -> PluginRegistry:
    """获取全局插件注册表实例。"""
    return _global_registry

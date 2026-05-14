"""
meta_router 模块
================

本模块定义了 MetaRouter 基类，为所有 LLM 路由器提供统一的抽象接口。
MetaRouter 是所有路由器的基类，负责管理底层 PyTorch 模型，并提供标准的路由接口。

主要功能：
    - 管理底层 PyTorch 模型（nn.Module）
    - 可选地加载配置文件和数据
    - 提供标准的路由接口：route() / forward()
    - 提供基础工具方法：指标计算、模型保存和加载

训练逻辑与路由器解耦，由 Trainer 类负责处理。

使用方式：
    所有路由器实现都应继承自 MetaRouter 并实现其抽象方法：
    - route_batch(): 批量路由决策
    - route_single(): 单个样本路由决策
"""

import os
import yaml
from abc import ABC, abstractmethod

import torch
import torch.nn as nn

from llmrouter.data import DataLoader


class MetaRouter(nn.Module, ABC):
    """
    MetaRouter 路由器基类
    --------------------

    所有 LLM 路由器的统一抽象基类。本类继承自 PyTorch 的 nn.Module 和抽象基类 ABC，
    为不同类型的路由器提供统一的接口规范。

    主要职责：
        - 管理底层 PyTorch 模型（nn.Module）
        - 可选地加载配置文件和数据集
        - 提供标准的路由接口：route() 和 forward()
        - 提供基础工具方法：指标计算、模型保存/加载

    训练逻辑与路由器解耦，由专门的 Trainer 类负责处理，保持本类的职责清晰。

    Attributes:
        model (nn.Module): 执行路由计算的底层 PyTorch 模型
        resources (Any): 可选的共享资源或上下文（如 tokenizer、环境等）
        cfg (dict): 从 YAML 配置文件加载的配置信息
        metric_weights (list): 指标权重列表，用于综合评估路由效果
    """

    def __init__(self, model: nn.Module, yaml_path: str | None = None, resources=None):
        """
        初始化 MetaRouter 路由器实例。

        Args:
            model (nn.Module):
                执行路由计算的底层 PyTorch 模型。所有路由器实现都必须提供此模型。
            yaml_path (str | None):
                可选的 YAML 配置文件路径。如果提供，将在初始化时加载配置和训练数据。
                配置文件格式应符合项目的 YAML 规范。
            resources (Any, optional):
                可选的共享资源或上下文对象，例如 tokenizer、环境变量等。
                可用于在不同组件间共享资源，避免重复加载。

        Raises:
            FileNotFoundError: 当 yaml_path 指定的文件不存在时抛出。

        Note:
            如果提供了 yaml_path，初始化过程会自动：
            - 解析 YAML 配置文件
            - 通过 DataLoader 加载数据集并附加到 self
            - 从配置中提取指标权重
        """
        super().__init__()
        self.model = model
        self.resources = resources
        self.cfg = {}
        self.metric_weights = []

        if yaml_path is not None:
            if not os.path.exists(yaml_path):
                raise FileNotFoundError(f"YAML file not found: {yaml_path}")

            with open(yaml_path, "r", encoding="utf-8") as f:
                self.cfg = yaml.safe_load(f)

            # Compute project root (two levels up from models/)
            project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../..")
            )

            # Load data via DataLoader (side-effect: attach datasets to `self`)
            loader = DataLoader(project_root)
            loader.load_data(self.cfg, self)

            # Load metric weights if provided
            weights_dict = self.cfg.get("metric", {}).get("weights", {})
            self.metric_weights = list(weights_dict.values())

            print("✅ MetaRouter initialized successfully (YAML + data loaded).")

    # ------------------------------------------------------------------
    # Core abstract method: subclasses must define routing behavior
    # ------------------------------------------------------------------

    @abstractmethod
    def route_batch(self, batch):
        """
        定义批量路由决策的计算方式（抽象方法）。

        子类必须实现此方法，定义如何根据输入批次进行路由决策。
        这是路由器的核心功能，决定了每个样本应被路由到哪个模型。

        Args:
            batch (Any):
                用于路由的输入批次。数据结构（dict、tensor 等）
                由具体的路由器实现决定。通常包含查询文本、特征向量等。

        Returns:
            Any:
                路由输出，可以是以下形式之一：
                - logits: 路由器对各模型的预测分数
                - scores: 每个候选模型的匹配度评分
                - indices: 选中的模型索引或模型名称

        Raises:
            NotImplementedError: 子类未实现此方法时抛出。

        Note:
            此方法为抽象方法，必须由所有路由器子类实现。
            实现时应考虑批处理的高效性，充分利用 PyTorch 的张量操作。
        """
        raise NotImplementedError

    @abstractmethod
    def route_single(self, batch):
        """
        定义单个样本路由决策的计算方式（抽象方法）。

        子类必须实现此方法，定义如何根据单个样本输入进行路由决策。
        通常用于推理或在线服务场景，需要快速响应。

        Args:
            batch (Any):
                用于路由的单个样本输入。数据结构（dict、tensor 等）
                由具体的路由器实现决定。通常包含查询文本、特征向量等。

        Returns:
            Any:
                路由输出，可以是以下形式之一：
                - logits: 路由器对各模型的预测分数
                - scores: 每个候选模型的匹配度评分
                - indices: 选中的模型索引或模型名称

        Raises:
            NotImplementedError: 子类未实现此方法时抛出。

        Note:
            此方法为抽象方法，必须由所有路由器子类实现。
            与 route_batch() 不同，本方法针对单个样本优化，
            在推理服务中使用以获得更快的响应速度。
        """
        raise NotImplementedError

    def forward(self, batch):
        """
        PyTorch 兼容的前向传播方法。

        此方法简单地委托给 route_batch()，使路由器可以在训练循环中
        像普通的 nn.Module 一样使用，无缝集成到 PyTorch 的训练框架中。

        Args:
            batch (Any):
                用于路由的输入批次，结构与 route_batch() 要求一致。

        Returns:
            Any:
                路由输出，由 route_batch() 返回的结果。

        Note:
            - 这是 PyTorch nn.Module 的标准接口方法
            - 在训练时会被自动调用
            - 直接调用 route_batch() 完成实际的计算逻辑
        """
        return self.route_batch(batch)

    # ------------------------------------------------------------------
    # Optional shared utilities
    # ------------------------------------------------------------------

    def compute_metrics(self, outputs, batch) -> dict:
        """
        可选的指标计算函数。

        子类可以重写此方法，根据路由输出定义通用的评估指标，
        例如准确率、成本、延迟等。用于评估路由器性能。

        Args:
            outputs (Any):
                来自 route() 的模型输出或路由输出，包含路由决策结果。
            batch (Any):
                原始输入批次，可能包含标签、真实答案等元信息，
                用于计算评估指标。

        Returns:
            dict:
                指标名称到值的映射字典，例如：
                {
                    "accuracy": 0.85,
                    "cost": 0.42,
                    "latency": 0.15
                }

        Note:
            - 默认实现返回空字典
            - 子类应根据实际需求重写此方法
            - 指标可用于模型选择、超参数调优等
        """
        return {}

    def save_router(self, path: str):
        """
        将路由器的完整状态字典保存到磁盘。

        保存路由器的所有可学习参数和状态信息，便于后续加载和恢复。

        Args:
            path (str):
                目标文件路径，用于保存路由器状态。
                建议使用 .pt 或 .pth 作为文件扩展名。
                路径必须具有写入权限。

        Note:
            - 使用 torch.save() 进行序列化
            - 保存的内容包括 self.model 的所有参数
            - 可以通过 load_router() 方法恢复

        Example:
            >>> router.save_router("models/my_router.pt")
            💾 Router state saved to: models/my_router.pt
        """
        torch.save(self.state_dict(), path)
        print(f"💾 Router state saved to: {path}")

    def load_router(self, path: str):
        """
        从磁盘加载路由器的状态字典。

        加载之前保存的路由器状态，恢复模型参数和配置。

        Args:
            path (str):
                源文件路径，指向之前保存的路由器状态文件。
                文件必须存在且具有读取权限。

        Note:
            - 使用 torch.load() 进行反序列化
            - 默认加载到 CPU，可通过 map_location 参数调整
            - 加载完成后路由器状态与保存时完全一致
            - 如果模型结构发生变化，加载可能会失败

        Raises:
            FileNotFoundError: 当路径文件不存在时抛出（由 torch.load 抛出）。

        Example:
            >>> router.load_router("models/my_router.pt")
            📂 Router state loaded from: models/my_router.pt
        """
        state = torch.load(path, map_location="cpu")
        self.load_state_dict(state)
        print(f"📂 Router state loaded from: {path}")

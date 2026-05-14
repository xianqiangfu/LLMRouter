"""
BaseTrainer 模块
================

该模块定义了所有路由器训练器的统一抽象基类。

主要功能:
    - 定义训练器的通用接口和基础功能
    - 提供损失函数计算的抽象方法
    - 提供训练流程的抽象方法
    - 支持不同的路由器模型和优化器

使用场景:
    - 作为所有具体训练器实现的基础类
    - 确保所有训练器遵循统一的接口规范
"""

from abc import ABC, abstractmethod
from typing import Any
import torch


class BaseTrainer(ABC):
    """
    路由器训练器抽象基类
    --------------------

    该类为所有路由器训练器定义统一的接口规范，所有具体训练器都需要继承此类并实现必要的抽象方法。

    主要职责:
        - 定义损失函数的计算接口
        - 定义训练流程的执行接口
        - 管理路由器模型和优化器
        - 处理设备相关的配置

    子类需要实现的方法:
        - loss_func(): 计算特定任务的损失函数
        - train(): 定义完整的训练循环流程
    """

    def __init__(
        self,
        router: torch.nn.Module,
        optimizer: torch.optim.Optimizer | None = None,
        device: str = "cuda",
        **kwargs: Any,
    ):
        """
        初始化基础训练器

        该方法用于初始化训练器的基本配置，包括路由器模型、优化器和设备设置。

        参数:
            router (torch.nn.Module):
                路由器模型实例，通常是 MetaRouter 或其子类的实例
            optimizer (torch.optim.Optimizer | None):
                可选的优化器实例。如果为 None，子类可以自行定义优化器
            device (str):
                模型运行的设备，例如 "cuda" 或 "cpu"
            **kwargs (Any):
                用于未来扩展的额外关键字参数

        属性:
            self.router: 路由器模型实例
            self.optimizer: 优化器实例
            self.device: 设备配置
            self.kwargs: 额外参数字典
        """
        self.router = router
        self.optimizer = optimizer
        self.device = device
        self.kwargs = kwargs

    # ------------------------------------------------------------------
    # 抽象方法（子类必须实现）
    # ------------------------------------------------------------------

    def loss_func(self, outputs: Any, batch: Any) -> torch.Tensor:
        """
        计算任务特定的损失函数

        该方法是一个抽象方法，子类必须实现具体的损失计算逻辑。

        参数:
            outputs (Any):
                路由器模型的输出结果
            batch (Any):
                当前训练批次的数据

        返回:
            torch.Tensor: 计算得到的损失值张量

        异常:
            NotImplementedError: 如果子类未实现此方法
        """
        raise NotImplementedError("Subclasses must implement loss_func()")

    @abstractmethod
    def train(self, dataloader: Any = None):
        """
        定义完整的训练循环流程

        该抽象方法要求子类实现具体的训练逻辑，包括数据迭代、前向传播、损失计算、反向传播和参数更新等步骤。

        参数:
            dataloader (Any, optional):
                可选的数据加载器，用于迭代训练数据。
                某些训练器可能直接使用路由器内部的数据，此时该参数可以为 None

        返回:
            None: 该方法通常不返回值，训练过程会影响模型的内部状态

        异常:
            NotImplementedError: 如果子类未实现此方法

        注意事项:
            - 子类需要根据具体任务设计训练循环
            - 应包含损失记录和模型检查点保存等逻辑
            - 需处理训练过程中的异常情况
        """
        pass




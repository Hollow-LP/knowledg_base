from abc import ABC, abstractmethod

from atguigu.tool import logger
from atguigu.import_process.state import ImportGraphState


class NodeBase(ABC):
    """
    节点基类
    """

    name: str = "node_base"
    def __init__(self):
        if self.name == "node_base":
            raise Exception(f"子类 {self.__class__.__name__} 必须覆盖 name 类属性")

    @abstractmethod
    def process(self,state):
        pass

    def __call__(self, state):
        #1,可以实现每个节点调用统一打印日志
        #2，可以同意进行异常捕获
        try:
            logger.info(f"{self.name} 开始执行")
            # 这个call是后期所有的子类对象在当函数使用的时候，都会自动带哦用这个方法
            result = self.process(state)
            logger.info(f"{self.name} 结束执行")
            return result
        except Exception as e:
            logger.error(f"{self.name} 执行异常")
            raise
# atguigu/import_process/nodes/node_entry.py
from pathlib import Path

from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.json_format_tool import json_format
from atguigu.tool.logger import logger


class NodeEntry(NodeBase):
    """
    入口节点：任务分发
    """

    name = "node_entry"

    def process(self, state: ImportGraphState):
        # 都要先进行防御性编程
        local_file_path = state.get("local_file_path",'')
        if not local_file_path:
            # 判断路径字符串是否提供
            logger.error("local_file_path路径必须提供")
            raise ValueError("local_file_path路径必须提供")

        local_file_path_obj = Path(local_file_path)
        if not local_file_path_obj.exists():
            # 判断文件是否存在
            logger.error("local_file_path路径文件不存在")
            raise ValueError("local_file_path路径文件不存在")

        # logger.info("local_file_path文件开始进行入口判断")

        # 接下来我们要去判断文件是md还是pdf还是其它，进行state赋值，后期可以根据这些值进行路由添加条件边
        file_title = local_file_path_obj.stem #文件名没后缀， name是带后缀
        suffix = local_file_path_obj.suffix
        if suffix.lower() == ".md":
            return {
                "file_title": file_title,
                "md_path": str(local_file_path_obj),
                "is_md_read_enabled": True
            }
        elif suffix.lower() == ".pdf":
            return {
                "file_title": file_title,
                "pdf_path": local_file_path,
                "is_pdf_read_enabled": True
            }
        else:
            logger.error("不支持的文件类型")
            raise ValueError(f"不支持的文件类型：{suffix}")



if __name__ == '__main__':
    node = NodeEntry()
    init_state = {
        "local_file_path": r"D:\output\hak180产品安全手册.pdf"
    }
    result = node(init_state)
    logger.info(json_format(result))






import json

from dns import exception

import main
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.json_format_tool import json_format
from atguigu.tool.logger import logger


class NodeItemNameRecognition(NodeBase):
    """
    主体识别节点：主体识别与标签提取
    """

    name = "node_item_name_recognition"

    def process(self, state: ImportGraphState):
        chunks = state.get("chunks")
        file_title = state.get("file_title")
        if not chunks:
            logger.error(f"chunks是空的，必须有值才能进行主体识别")
            raise Exception("chunks是空的，必须有值才能进行主体识别")

        if not file_title:
            logger.error(f"file_title是空的，必须有值才能进行主体识别")
            raise Exception("file_title是空的，必须有值才能进行主体识别")
        # 根据chunks去让大模型识别主体名称（商品名字）
        # chunks有点多，内容加起来可能超过大模型的token限制，所以我们是从chunks当中截取k个
        chunk_k_list = chunks[:10]
        max_len = 10000
        content_str = '/n'
        # 需要把这些chunk的title content file_title part把这些需要的数据拼接成一个字符串，还得把这个字符串合并拼接到一个大的字符串
        for idx,chunks in enumerate(chunk_k_list,start=1):
            title = chunks.get("title")
            content = chunks.get("content")
            chunk_str = f"[切片{idx}]\n{file_title}\n{title}\n{content}"
            #判段chunk_str是否已经超过max_len
            if len(content_str) > max_len:
                logger.info(f"已经超过最大长度，不再拼接")
                break
            content_str += chunk_str

        content_str = content_str[:max_len]
        return state


if __name__ == '__main__':
    node = NodeItemNameRecognition()
    # with open(r"D:\output\hak180产品安全手册\chunks.json","r",encoding="utf-8") as f:
    #     chunks_json = f.read()  如果这样写，下面需要反序列化

    with open(r"D:\output\hak180产品安全手册\chunks.json","r",encoding="utf-8") as f:
        chunks= json.load(f)

    init_state = {
        "chunks":chunks,
        "file_title":"hak180产品安全手册"
    }
    result = node(init_state)
    logger.info(json_format(result))
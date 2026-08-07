import re
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.json_format_tool import json_format
from atguigu.tool.logger import logger


class NodeDocumentSplit(NodeBase):
    """
    文档切分节点：智能文档切片
    """

    name = "node_document_split"

    def get_md_content(self,state):
        md_path = state.get("md_path", '')
        if not md_path:
            logger.error("未提供MarkDown路径,必须提供MarkDown路径")
            raise Exception("未提供MarkDown路径,必须提供MarkDown路径")
        md_path_obj = Path(md_path)
        if not md_path_obj.exists():
            logger.error("MarkDown文件不存在")
            raise Exception(f"MarkDown文件不存在：{md_path}")
        fifle_title = state.get("file_title", '')
        if not fifle_title:
            fifle_title = md_path_obj.stem
        with open(md_path_obj, 'r', encoding="utf-8") as f:
            md_content = f.read()
        if not md_content:
            logger.error("MarkDown文件内容为空")
            raise Exception(f"MarkDown文件内容为空")
        # 统一换行符
        md_content = md_content.replace("\r\n", "\n").replace("\r", "\n")
        return md_content,fifle_title,md_path_obj

    def get_sectioin_list(self,md_content,fifle_title,md_path_obj):
        # 按行切分
        md_line_list = md_content.split("\n")
        # 按照标题去合并行，所以我们就得遍历这个系列找标题

        # 写代码块的正则
        code_pattern = r"^(`{3,}|~{3,})"
        # 定义是否在代码块的标志
        title_pattern = r'^\s*#{1,6}\s+.+'
        in_code_block = False
        marker = None  # 记录代码块的起始字符
        current_index = 0
        section_list = []
        for idx, line in enumerate(md_line_list):
            line = line.strip()
            # 判断行是不是标题，得先判断是不是在代码块里面
            match = re.match(code_pattern, line)
            if match:
                if not in_code_block:
                    in_code_block = True
                    marker = match.group(1)
                    logger.info(f"开始代码块：{marker}")
                else:
                    if marker == match.group(1):
                        in_code_block = False
                        marker = None
                        logger.info(f"结束代码块")
            # 不在代码块，然后就可以判断是不是标题
            if not in_code_block and re.match(title_pattern, line):
                temp_list = md_line_list[current_index:idx]
                content = '\n'.join(temp_list)
                section_dict = {
                    "title": temp_list[0] if content else None,
                    "content": content,
                    "file_title": fifle_title
                }
                section_list.append(section_dict)
                # 更新起始切片位置
                current_index = idx
        # 最后一个切片，我们循环当中切片是把最后一个标题及内容

        section_list.append({
            "title": md_line_list[current_index:],
            "content": '\n'.join(md_line_list[current_index:]),
            "file_title": fifle_title
        })
        return section_list


    def get_final_section_list(self,section_list,fifle_title,md_path_obj):
        max_length = 300
        over_lap = 30
        final_section_list = []

        spliter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", " "],
            chunk_size=max_length,
            chunk_overlap=over_lap
        )
        for section in section_list:
            title = section.get("title")
            content = section.get("content")
            # 求真实的内容 = content-标题
            # 目的是为了把标题去除，切分只切分真正的内容,，切完之后，每个chunk都需要在前面加上标题
            real_content = content[len(title):] if content.startswith("#") else content

            if len(real_content) < max_length:
                final_section_list.append({
                    **section,
                    "part": 0
                })
                continue
            # 如果内容当中包含表格，防止表格被切断，干脆就不切了
            if "<table" in real_content:
                final_section_list.append({
                    **section,
                    "part": 0
                })
                continue

            # 真正的切分

            splite_chunk_list = spliter.split_text(real_content)
            for idx, splite_chunk in enumerate(splite_chunk_list):
                final_section_list.append({
                    "title": title,
                    "file_title": fifle_title,
                    "content": title + "\n\n" + splite_chunk,
                    "part": idx
                })

        # 备份chunks列表到json文件

        with open(md_path_obj.parent / "chunks.json", "w", encoding="utf-8") as f:
            f.write(json_format(final_section_list))

        return final_section_list

    def process(self, state: ImportGraphState):
        #第一步：获取md的内容，文件标题，路径对象
        md_content,fifle_title,md_path_obj = self.get_md_content(state)

        #第二步：对md内容进行按行切分，根据标题合并section
        section_list = self.get_sectioin_list(md_content,fifle_title,md_path_obj)

        #第三步：对section列表进行精细切分(长切短和),遍历上一部分的section
        #对内容进行去除标题，判断标题符合条件，然后进行切分
        final_section_list = self.get_final_section_list(section_list,fifle_title,md_path_obj)


        return {
            "chunks":final_section_list
        }

if __name__ == '__main__':
    node = NodeDocumentSplit()
    init_state = {
        "md_path":r"D:\output\hak180产品安全手册\hak180产品安全手册_new.md",
        "file_title":"hak180产品安全手册"
    }
    result = node(init_state)
    logger.info(json_format(result))

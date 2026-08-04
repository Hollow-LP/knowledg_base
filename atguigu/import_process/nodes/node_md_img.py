import base64
import os
import re
import time
from collections import deque
from pathlib import Path

from langchain.chat_models import init_chat_model
from minio.deleteobjects import DeleteObject

from atguigu.config.config import LLMconfig, MinIoConfig
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.logger import logger
from atguigu.tool.json_format_tool import json_format
from atguigu.tool.mino_client_tool import get_minio_client


class NodeMDImg(NodeBase):
    """
    MarkDown图片处理节点：多模态图片理解
    """

    name = "node_md_img"

    def get_md_content(self,state):

        #1,获取文件的内容和图片的名字列表
        md_path = state.get("md_path", '')
        if not md_path:
            logger.error("未提供MarkDown路径,必须提供MarkDown路径")
            raise ValueError("未提供MarkDown路径,必须提供MarkDown路径")

        md_path_obj = Path(md_path)
        if not md_path_obj.exists():
            logger.error("MarkDown文件不存在")
            raise FileNotFoundError(f"MarkDown文件不存在：{md_path}")

        with open(md_path_obj, 'r', encoding="utf-8") as f:
            md_content = f.read()

        if not md_content:
            logger.error("MarkDown文件内容为空")
            raise ValueError("MarkDown文件内容为空")
        return md_content,md_path_obj

    def get_image_with_context_list(self,md_content,image_dir_path_obj,image_name_list):

        #2、遍历图片的名字，获取图片的上下文
        IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
        MAX_CONTEXT_LENGTH = 250 #限制图片前后抓取的文本的最大长度,前后最多取250个字符
        image_with_context_list=[]
        for image_name in image_name_list:
            if Path(image_name).suffix.lower() not in IMAGE_EXTENSIONS:
                logger.warning(f"图片{image_name}格式不支持")
                continue
            #构建图片在makrdown当中的正则对象
            pattern = re.compile(r"!\[.*?\]\(.*?" + re.escape(image_name) + r"\)")
            match = pattern.search(md_content)
            if not match:
                logger.warning(f"图片{image_name}在MarkDown中未找到")
                continue
            #获取匹配到的图片的起始和结束位置
            start,end = match.span()
            pre_text = md_content[max(0,start-MAX_CONTEXT_LENGTH):start]
            post_text = md_content[end:min(len(md_content),end+MAX_CONTEXT_LENGTH)]
            #把图片和上下文构造成字典，添加到准备好地列表当中
            #构造这个图片的路径一起放到字典
            image_path = str(image_dir_path_obj / image_name)
            image_with_context_list.append({
                "image_path": image_path,
                "pre_text": pre_text,
                "post_text":post_text,
                "image_name": image_name
            })
        return image_with_context_list


    def get_image_with_summary_list(self,image_with_context_list):
        #进行大模型调用，生成图片摘要
        dq = deque(maxlen=30)
        current_time = time.time()

        llm = init_chat_model(
            model=LLMconfig.llm_default_model,
            model_provider="openai",
            temperature=LLMconfig.llm_default_temperature,
            api_key=LLMconfig.openai_api_key,
            base_url=LLMconfig.openai_api_base
        )

        image_with_summary_list = []
        for image_with_context in image_with_context_list:
            while dq and (current_time - dq[0] > 60):
                dq.popleft()
            if dq and len(dq) == dq.maxlen:
                need_wait_time = 60 - (current_time - dq[0])
                if need_wait_time > 0:
                    time.sleep(need_wait_time)
                    current_time = time.time()
                    while dq and (current_time - dq[0] > 60):
                        dq.popleft()
            dq.append(current_time)

            # 先把图片内容base64编码
            with open(image_with_context.get("image_path"), 'rb') as f:
                image_data = f.read()
                base64_str = base64.b64encode(image_data).decode("utf_8")

            # image_path = image_with_context.get("image_path")
            # suffix = Path(image_path).suffix.lower()
            # mime_map = {
            #     ".jpg": "image/jpeg",
            #     ".jpeg": "image/jpeg",
            #     ".png": "image/png",
            #     ".gif": "image/gif",
            #     ".bmp": "image/bmp",
            #     ".webp": "image/webp"
            # }
            # mime_type = mime_map.get(suffix, "image/jpeg")
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                # 这个格式base64在使用的时候的规定，必须加上这个
                                "url": "data:image/jpeg;base64," + base64_str
                                # "url": f"data:{mime_type};base64,{base64_str}"

                            },
                        },
                        {"type": "text", "text": f"""
                                        这是一张图片，图片上文部分为"{image_with_context.get("pre_text")}"，
                                        下文部分为"{image_with_context.get("post_text")}"，
                                        请用中文简要总结这张图片的摘要,字数在50字以内。"""},
                    ],
                },
            ]
            res = llm.invoke(messages)
            image_with_summary_list.append({
                "image_name": image_with_context.get("image_name"),
                "image_path": image_with_context.get("image_path"),
                "summary": res.content
            })
        return image_with_summary_list
    def get_image_with_summary_and_url_list(self,image_with_summary_list):
        upload_dir = MinIoConfig.minio_img_dir
        minio_client = get_minio_client()
        #幂等性删除这个目录当中的图片
        #1.拿到桶当中这个目录当重点的所有老图片(prefix=upload_dir代表桶下面的目录，不到文件)
        old_image_list = minio_client.list_objects(bucket_name=MinIoConfig.minio_bucket_name,prefix=upload_dir,recursive=True)
        #2.调用api批量删除老图片，delete_object_list
        delete_image_list = [DeleteObject(obj.object_name) for obj in old_image_list]
        minio_client.remove_objects(bucket_name=MinIoConfig.minio_bucket_name,delete_object_list=delete_image_list)
        image_with_summary_and_url_list = []
        #准备上传老图片
        for image_with_summary in image_with_summary_list:
            minio_client.fput_object(
                bucket_name=MinIoConfig.minio_bucket_name,
                object_name=upload_dir + "/" + image_with_summary.get("image_name"),
                file_path=image_with_summary.get("image_path")
            )
            url = f"http://{MinIoConfig.minio_endpoint}/{MinIoConfig.minio_bucket_name}/{upload_dir}/{image_with_summary.get('image_name')}"
            image_with_summary_and_url_list.append({
                **image_with_summary,
                "url":url
            })
        return image_with_summary_and_url_list
    def replace_md_image(self,image_with_summary_and_url_list,md_path_obj,md_content):
        for image_with_summary_and_url in image_with_summary_and_url_list:
            pattern = re.compile(r"!\[.*?\]\(.*?" + re.escape(image_with_summary_and_url.get('image_name')) + r"\)")

            md_content = pattern.sub(
                lambda _: f"![{image_with_summary_and_url.get('summary')}]({image_with_summary_and_url.get('url')})",
                md_content)
        new_md_path_obj = md_path_obj.parent / f"{md_path_obj.stem}.md"
        with open(new_md_path_obj,"w",encoding="utf-8") as f:
            f.write(md_content)
        return new_md_path_obj,md_content


    def process(self, state: ImportGraphState):

        #第一步：获取md的内容和路径对象
        md_content,md_path_obj = self.get_md_content(state)
        #构造图片的存储路径
        image_dir_path_obj = md_path_obj.parent / "images"
        if not image_dir_path_obj.exists():
            return md_content
        #判断图片目录是否为空
        image_name_list = os.listdir(image_dir_path_obj)
        if not image_name_list:
            logger.info("图片目录为空")
            return md_content

        #第二步：获取图片的上下文列表，根据图片正则达到图片的位置，获取上下文
        image_with_context_list = self.get_image_with_context_list(md_content,image_dir_path_obj,image_name_list)

        #第三步：获取图片的摘要列表
        image_with_summary_list = self.get_image_with_summary_list(image_with_context_list)

        #第四步：上传图片到minro,然后构造图片线上url到列表当中
        image_with_summary_and_url_list = self.get_image_with_summary_and_url_list(image_with_summary_list)

        #第五大步：替换md中的图片
        new_md_path_obj,md_content = self.replace_md_image(image_with_summary_and_url_list,md_path_obj,md_content)

        return{
            "md_content":md_content,
        }




if __name__ == '__main__':
    node = NodeMDImg()
    init_state = {
        "md_path": r"D:\output\hak180产品安全手册\hak180产品安全手册.md",
    }
    result = node(init_state)
    logger.info(json_format(result))

from typing import List

from pymilvus.model.hybrid import BGEM3EmbeddingFunction

from atguigu.config.config import EmbeddingConfig
from atguigu.tool.json_format_tool import json_format
from atguigu.tool.logger import logger

bge_m3_model = None
def get_bge_m3_model():
    global bge_m3_model
    if not bge_m3_model:
        bge_m3_model = BGEM3EmbeddingFunction(
            model_name=EmbeddingConfig.bge_m3_path,
            devices=EmbeddingConfig.bge_device,
            use_fp16=EmbeddingConfig.bge_fp16,
        )
    return bge_m3_model


def get_bge_m3_embedding(texts: List[str]):
    bge_m3_model = get_bge_m3_model()
    embedding = bge_m3_model.encode_documents(texts)
    print(embedding)


    return {
        "dense": [dense_item.tolist() for dense_item in embedding.get("dense")],
        "sparse": [
            dict(zip(sparse_item.indices.tolist(),sparse_item.data.tolist()))
            for sparse_item in embedding.get("sparse")
        ]
    }


if __name__ == '__main__':
    texts = ["hello world", "hello milvus"]
    result = get_bge_m3_embedding(texts)
    logger.info(json_format(result))









import os
from dotenv import load_dotenv
# load_dotenv()

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env')) #绝对路径查找.env
load_dotenv(dotenv_path=env_path,override=True)


class MineruConfig:
    mineru_token = os.getenv('MINERU_TOKEN')
    mineru_base_url = os.getenv('MINERU_BASE_URL')

class LLMconfig:
    openai_api_key = os.getenv('OPEN_API_KEY')
    openai_api_base = os.getenv('OPEN_API_BASE_URL')
    llm_default_model = os.getenv('LLM_DEFAULT_MODEL')
    llm_default_temperature = (os.getenv("LLM_DEFAULT_TEMPERATURE", 0.1))
    vl_model = os.getenv('VL_MODEL')
    item_model = os.getenv('ITEM_MODEL')

class MinIoConfig:
    minio_endpoint = os.getenv('MINIO_ENDPOINT')
    minio_access_key = os.getenv('MINIO_ACCESS_KEY')
    minio_secret_key = os.getenv('MINIO_SECRET_KEY')
    minio_bucket_name = os.getenv('MINIO_BUCKET_NAME')
    minio_img_dir = os.getenv('MINIO_IMG_DIR')


class EmbeddingConfig:
    bge_m3_path=os.getenv("BGE_M3_PATH")
    bge_m3=os.getenv("BGE_M3")
    bge_device=os.getenv("BGE_DEVICE")
    # 特殊处理：将.env中的1/0转为布尔值，兼容常见的数字/字符串格式
    bge_fp16=True if os.getenv("BGE_FP16") in ("True",1,True,"1") else False




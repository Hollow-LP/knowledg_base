import os
from dotenv import load_dotenv
# load_dotenv()

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env')) #绝对路径查找.env
load_dotenv(dotenv_path=env_path,override=True)


class MineruConfig:
    mineru_token = os.getenv('MINERU_TOKEN')
    mineru_base_url = os.getenv('MINERU_BASE_URL')

class LLMconfig:
    openai_api_key = os.getenv('OPENAI_API_KEY')
    openai_api_base = os.getenv('OPEN_API_BASE_URL')
    llm_default_model = os.getenv('LLM_DEFAULT_MODEL')
    llm_default_temperature = os.getenv('LLM_DEFAULT_TEMPERATURE')
    vl_model = os.getenv('VL_MODEL')
    item_model = os.getenv('ITEM_MODEL')



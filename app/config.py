from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    llm_base_url: str='http://localhost:1234/v1'
    llm_api_key: str='lm-studio'
    llm_model: str='openai/gpt-oss-20b'
    embedding_model: str='sentence-transformers/all-MiniLM-L6-v2'
    neo4j_uri: str='bolt://localhost:7687'
    neo4j_user: str='neo4j'
    neo4j_password: str='change-me-now'
    redis_url: str='redis://localhost:6379/0'
    human_approval_threshold: float=.55
    # Security settings
    cors_origins: list[str]=['*']          # Set to specific origins in production, e.g. ["https://your-domain.com"]
    max_upload_bytes: int=50*1024*1024      # 50 MB — reject PDFs larger than this
    metrics_token: str=''                   # Set a secret token to protect /metrics; empty = no auth
    model_config=SettingsConfigDict(env_file='.env',extra='ignore')
@lru_cache
def settings(): return Settings()

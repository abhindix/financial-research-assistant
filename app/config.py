import os
from functools import lru_cache

class Settings:
    def __init__(self):
        self.llm_base_url=os.getenv('LLM_BASE_URL','http://localhost:1234/v1')
        self.llm_api_key=os.getenv('LLM_API_KEY','lm-studio')
        self.llm_model=os.getenv('LLM_MODEL','openai/gpt-oss-20b')
        self.embedding_model=os.getenv('EMBEDDING_MODEL','text-embedding-nomic-embed-text-v1.5')
        self.neo4j_uri=os.getenv('NEO4J_URI','bolt://localhost:7687')
        self.neo4j_user=os.getenv('NEO4J_USER','neo4j')
        self.neo4j_password=os.getenv('NEO4J_PASSWORD','change-me-now')
        self.redis_url=os.getenv('REDIS_URL','redis://localhost:6379/0')
        self.human_approval_threshold=float(os.getenv('HUMAN_APPROVAL_THRESHOLD','.55'))
        self.cors_origins=os.getenv('CORS_ORIGINS','*').split(',') if os.getenv('CORS_ORIGINS') else ['*']
        self.max_upload_bytes=int(os.getenv('MAX_UPLOAD_BYTES', str(50*1024*1024)))
        self.metrics_token=os.getenv('METRICS_TOKEN','')

@lru_cache
def settings():
    return Settings()

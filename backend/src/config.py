import os

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    gemini_api_key: str
    gemini_model: str = "gemini-3.5-flash-lite"  
    embedding_model: str = "models/gemini-embedding-001"  # output pinned to 768-dim (see transaction_embedding.py)
    #knowledge_embedding_model: str = "models/text-embedding-001"  
    database_url: str = "postgresql://postgres:1234@localhost:5432/finance"
    agent_database_url: str
    sql_agent_top_k: int = 20 
    secret_key: str = "dev-only-change-me"

    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "finance-agent"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()   

if settings.langsmith_tracing and settings.langsmith_api_key:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint

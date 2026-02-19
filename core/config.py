"""Core configuration settings."""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # GitLab
    gitlab_token: str = os.getenv("GITLAB_TOKEN", "")
    project_id: str = os.getenv("PROJECT_ID", "")
    gitlab_url: str = os.getenv("GITLAB_URL", "https://gitlab.com")
    
    # Azure OpenAI
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ci_rca.db")
    
    # App
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def api_base(self):
        return f"{self.gitlab_url}/api/v4"
    
    @property
    def gitlab_headers(self):
        return {"PRIVATE-TOKEN": self.gitlab_token}

settings = Settings()

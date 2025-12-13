"""
Configuration Management Module
Handles all environment variables and application settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses Pydantic for validation and type safety.
    """
    
    # Application Settings
    app_name: str = Field(default="Multi-Agent RAG Platform", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="production", alias="ENVIRONMENT")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
    # MongoDB Configuration
    mongodb_url: str = Field(..., alias="MONGODB_URL")
    mongodb_db_name: str = Field(default="rag_platform", alias="MONGODB_DB_NAME")
    mongodb_auth_collection: str = Field(default="users", alias="MONGODB_AUTH_COLLECTION")
    mongodb_chat_collection: str = Field(default="chat_history", alias="MONGODB_CHAT_COLLECTION")
    
    # ChromaDB Configuration
    chroma_persist_directory: str = Field(default="./data/chroma", alias="CHROMA_PERSIST_DIRECTORY")
    chroma_collection_name: str = Field(default="policy_documents", alias="CHROMA_COLLECTION_NAME")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")
    openai_temperature: float = Field(default=0.7, alias="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=2000, alias="OPENAI_MAX_TOKENS")
    
    # Embedding Configuration
    sentence_transformer_model: str = Field(default="all-MiniLM-L6-v2", alias="SENTENCE_TRANSFORMER_MODEL")
    embedding_dimension: int = Field(default=384, alias="EMBEDDING_DIMENSION")
    
    # JWT Authentication
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS Configuration
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")
    allowed_hosts: str = Field(default="localhost,127.0.0.1", alias="ALLOWED_HOSTS")
    
    # Upload Settings
    max_upload_size_mb: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")
    allowed_extensions: str = Field(default=".pdf,.docx,.txt,.md,.jpg,.jpeg,.png,.webp,.bmp,.tiff", alias="ALLOWED_EXTENSIONS")
    
    # Agent Configuration
    agent_max_iterations: int = Field(default=5, alias="AGENT_MAX_ITERATIONS")
    agent_timeout_seconds: int = Field(default=60, alias="AGENT_TIMEOUT_SECONDS")
    
    # OPIK Evaluation & Observability
    opik_api_key: str = Field(default="", alias="OPIK_API_KEY")
    opik_workspace: str = Field(default="", alias="OPIK_WORKSPACE")
    opik_project_name: str = Field(default="multi-agent-rag", alias="OPIK_PROJECT_NAME")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """Parse allowed hosts string into list."""
        return [host.strip() for host in self.allowed_hosts.split(",")]
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Parse allowed extensions string into list."""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency injection function for FastAPI.
    Returns the global settings instance.
    """
    return settings


import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from exceptions.no_ntlm_agents_specified_in_env_exception import NoNTLMAgentsSpecifiedInEnvFile
from pathlib import Path, PosixPath

project_root_path = Path(__file__).resolve().parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"      # Ignore unknown keys so it doesn't crash
    )

    SECRET_KEY: str = Field(default_factory=lambda: os.urandom(32).hex())
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    AES_KEY: str = Field(default_factory=lambda: os.urandom(32).hex())

    PORT: int = Field(8000, env="PORT")
    CELERY_BROKER_URL : str = Field("redis://redis:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND : str = Field("redis://redis:6379/1", env="CELERY_RESULT_BACKEND")
    NEO4J_URI: str = Field("bolt://localhost:7687", env="NEO4J_URI")
    NEO4J_USERNAME: str = Field("neo4j", env="NEO4J_USERNAME")
    NEO4J_PASSWORD: str = Field("password", env="NEO4J_PASSWORD")
    DEFAULT_ADMIN_LOGIN: str = Field("admin", env="DEFAULT_ADMIN_LOGIN")
    DEFAULT_ADMIN_PASSWORD: str = Field("admin", env="DEFAULT_ADMIN_PASSWORD")

    NTLM_AGENTS_URIS: str = Field(env="NTLM_AGENTS_URIS")

    NTLM_AGENTS_SECRET: str = Field(env="NTLM_AGENTS_SECRET")

    PROJECT_ROOT_PATH : PosixPath = Field(project_root_path)

    PDF_STORAGE_PATH : PosixPath = Field(project_root_path / 'pdf_storage')

    @property
    def ntlm_agents_uris(self) -> list[str]:
        if self.NTLM_AGENTS_URIS in ['', None]:
            raise NoNTLMAgentsSpecifiedInEnvFile("No NTLM agents were specified in the environment configuration.")
        
        return [uri for uri in self.NTLM_AGENTS_URIS.split(";") if uri]

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()

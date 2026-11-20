import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "TRIPWIRE"
    app_subtitle: str = "SUPERNOVA"
    version: str = "0.1.0"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Workspace & Execution Constraints
    workspace_dir: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "demo_workspace")
    )
    command_timeout_seconds: float = 10.0
    max_output_chars: int = 50_000
    max_file_size_bytes: int = 1_000_000

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()

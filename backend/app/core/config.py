import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Intelligent Candidate Discovery"
    API_V1_STR: str = "/api/v1"
    ENV: str = "development"

    # Database connection string (optional)
    DATABASE_URL: Optional[str] = None

    # Path configurations
    DATA_DIR: str = "../data"
    CHALLENGE_DATA_DIR: str = "../../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge"

    # ML settings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "../data/embeddings/faiss_candidates.index"
    RANKER_MODEL_PATH: str = "../data/processed/xgboost_ranker.json"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_absolute_path(self, relative_path: str) -> str:
        """Helper to resolve paths relative to backend directory or as absolute."""
        if os.path.isabs(relative_path):
            return relative_path
        # Otherwise resolve relative to backend root
        backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.abspath(os.path.join(backend_root, relative_path))


settings = Settings()

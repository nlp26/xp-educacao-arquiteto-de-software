from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Carrega configuração do ambiente ou do arquivo .env"""

    DATABASE_URL: str = "postgresql://app_user:app_secret@localhost:5432/clientes_db"
    APP_TITLE: str = "API de Clientes"
    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"


settings = Settings()

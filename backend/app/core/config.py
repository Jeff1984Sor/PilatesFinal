from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./studiopilates.db"
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    CORS_ORIGINS: str = "http://localhost:3000"

    TOTALPASS_BASE_URL: str = ""
    TOTALPASS_API_KEY: str = ""
    EVOLUTION_BASE_URL: str = ""
    EVOLUTION_TOKEN: str = ""
    EVOLUTION_INSTANCE: str = ""
    ROOT_PATH: str = ""
    STORAGE_DIR: str = "./storage"

    RATE_LIMIT_PER_MINUTE: int = 0

    # Chaves de API para integracoes externas (empresas). Separe varias por virgula.
    INTEGRACAO_API_KEYS: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def integracao_api_keys_list(self) -> list[str]:
        return [k.strip() for k in self.INTEGRACAO_API_KEYS.split(",") if k.strip()]


settings = Settings()

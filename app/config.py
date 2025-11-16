from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_parse_none_str="None",
        extra="ignore"  # Ignora campos extras do .env que não estão no modelo
    )
    
    # Database
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/vamo_junto_db",
        alias="DATABASE_URL"
    )
    
    # JWT
    secret_key: str = Field(
        default="your-secret-key-change-in-production-min-32-chars",
        alias="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=1440, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS - string separada por vírgula (será convertida para lista via property)
    cors_origins: str = Field(
        default="http://localhost:5173",
        alias="CORS_ORIGINS"
    )
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    
    # Environment
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # NFC-e Scraper
    nfce_base_url: str = Field(
        default="https://www.nfce.fazenda.sp.gov.br",
        alias="NFCE_BASE_URL"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        if not self.cors_origins:
            return ["http://localhost:5173"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    


settings = Settings()


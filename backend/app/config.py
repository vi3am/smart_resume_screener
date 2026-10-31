    
    
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str((Path(__file__).resolve().parent.parent / ".env")),
        extra="ignore",
    )
    
    APP_NAME : str = "Smart Resume Screener"
    DEBUG: bool = False
    JWT_SECRET_KEY: str
    DATABASE_URL: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    
    
    
    # class Config:
    #     env_file = ".env"
    #     extra="ignore"
        
        

settings = Settings()

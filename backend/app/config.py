    
    
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    APP_NAME : str = "Smart Resume Screener"
    DEBUG: bool = False
    JWT_SECRET_KEY: str
    DATABASE_URL: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    
    
    
    # class Config:
    #     env_file = ".env"
    #     extra="ignore"
        
        

settings = Settings()
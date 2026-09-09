from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME : str = "Smart Resume Screener"
    DEBUG: bool = False
    JWT_SECRET_KEY: str
    DATABASE_URL: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    class Config:
        env_file = ".env"
        
        

settings = Settings()
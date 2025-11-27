import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme")
    ALGORITHM: str = "HS256"   # Algorithme de signature
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

settings = Settings()

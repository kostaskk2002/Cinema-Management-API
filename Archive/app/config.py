from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    #Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "cinema_user"
    
    #Security
    SECRET_KEY: str = "lqh+!-etvy0(=2-0bdb$vsfa3i@f%0v!c@h_zy#8vzfqh@*#x="
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    #Application
    DEBUG: bool = True
    API_VERSION: str = "v1"
    
    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
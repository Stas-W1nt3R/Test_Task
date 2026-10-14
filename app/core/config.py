from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_name : str
    db_user : str
    db_password : str
    db_host: str
    db_port : int = 5432

    deribit_api_url: str
    redis_url: str

    @property
    def database_url(self):
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"

settings = Settings()
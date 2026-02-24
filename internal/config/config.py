from pathlib import Path

import yaml
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent.parent.parent


def validate_config(config):
    if not isinstance(config.get("database", {}).get("name"), str):
        raise ValueError("Database name must be a string")


def yamlconfig():
    with open(BASE_DIR / "internal" / "config" / "config.yaml", "r") as file:
        conf = yaml.safe_load(file)
        
        # Override with environment variables for Docker Compose compatibility
        import os
        if "DB_HOST" in os.environ:
            conf.setdefault("database", {})["host"] = os.environ["DB_HOST"]
        if "DB_PORT" in os.environ:
            conf["database"]["port"] = int(os.environ["DB_PORT"])
        if "KAFKA_HOST" in os.environ:
            conf.setdefault("kafka", {})["host"] = os.environ["KAFKA_HOST"]
        if "KAFKA_PORT" in os.environ:
            conf.setdefault("kafka", {})["port"] = int(os.environ["KAFKA_PORT"])
            
        validate_config(conf)
        return conf


class AuthJWT(BaseModel):
    private_key_path: Path = BASE_DIR / "certs" / "private.pem"
    public_key_path: Path = BASE_DIR / "certs" / "public.pem"
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 15


class Database(BaseModel):
    username: str = "postgres"
    password: str = "password"
    host: str = "localhost"
    port: int = 5432
    name: str = "SpendingTrackerDB"


class Logger(BaseModel):
    log_level: str = "INFO"


class Kafka(BaseModel):
    host: str = "localhost"
    port: int = 9092

class Settings(BaseModel):
    logger: Logger
    database: Database
    kafka: Kafka
    auth_jwt: AuthJWT = AuthJWT()

    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.database.username}:{self.database.password}@{self.database.host}:{self.database.port}/{self.database.name}"

    @property
    def SYNC_DATABASE_URL(self):
        return f"postgresql+psycopg2://{self.database.username}:{self.database.password}@{self.database.host}:{self.database.port}/{self.database.name}"

    @property
    def KAFKA_URL(self) -> str:
        return f"{self.kafka.host}:{self.kafka.port}"


settings = Settings(**yamlconfig())

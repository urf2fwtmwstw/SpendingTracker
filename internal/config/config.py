from pathlib import Path

import yaml
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent.parent.parent


def validate_config(config):
    if not isinstance(config.get("database", {}).get("name"), str):
        raise ValueError("Database name must be a string")


# Load YAML config
def yamlconfig():
    with open(BASE_DIR / "internal" / "config" / "config.yaml", "r") as file:
        conf = yaml.safe_load(file)
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
        return f"postgresql+asyncpg://{self.database.username}:{self.database.password}@{self.database.host}/{self.database.name}"

    @property
    def KAFKA_URL(self) -> str:
        return f"{self.kafka.host}:{self.kafka.port}"


settings = Settings(**yamlconfig())

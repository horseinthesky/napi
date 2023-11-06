import os
from functools import lru_cache
from typing import Any

from pydantic import BaseSettings

ENV = os.getenv("ENV", "prod")
ENDPOINTS_DIR = "endpoints"


class Settings(BaseSettings):
    nb_api_url: str
    tenants: list[str]
    domains: list[str]
    endpoints: list[str]

    class Config:
        env_file: str = ".env"

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name in ["tenants", "domains", "endpoints"]:
                return raw_val.split(",")
            return cls.json_loads(raw_val)


class ProdSettings(Settings):
    class Config:
        env_prefix: str = "PROD_"


settings_map = {
    "prod": ProdSettings,
}


@lru_cache
def get_settings(env: str):
    settings = settings_map.get(env)
    if settings is None:
        raise ValueError(f"env '{env}' is not supported")

    return settings


settings = get_settings(ENV)()

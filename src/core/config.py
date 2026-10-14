"""
Settings.py
Configuration management using Pydantic Settings.

Parsing Environment Variables with Pydantic
--------------------------------------------

* Pydantic has `Basemodel` for data validation, and also we can implement 'Base' class for parsing settings and secrets from files.

* The `BaseSettings` class is used to load a settings or config class from environment variables or secret files.

* This is useful in production where I don't want to expose secrets inside the code or the container environment.

* When I create a model inheriting from `BaseSettings`, the model initializer will attempt to set values of each fields.

* Set Environment file (dotenv) - ENV is an enviornment variable file that we can use key-value pairs.



"""


from typing import Optional, Annotated
from pydantic import Field, HttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

# Using Pydantic BaseSettings to parse environment variables

# Define AppSettings inheriting from the BaseSettings class from the pydantic_settings
class AppSettings(BaseSettings):
    """Application settings loaded from environment variables."""


    # Configure AppSettings to read environment variables from the ENV file at the root of the project with UTF-8 encoding. 
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


    # =============================================================================
    # API Configuration
    # =============================================================================
    api_title: str = Field(default="Advanced RAG API")
    api_version: str = Field(default="1.0.0")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_debug: bool = Field(default=False)






    # =============================================================================
    # Database URL
    # =============================================================================

    # Redis
    redis_url: str = Field(default="redis://localhost:6379")
    redis_password: Optional[str] = Field(default=None)



@lru_cache
def get_settings() -> AppSettings:
    """
    Get cached settings instance.

    Returns:
        AppSettings instance
    
    """

    return AppSettings()


# Global settings instance
settings = get_settings()
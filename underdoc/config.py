from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    underdoc_api_key: Optional[str] = Field(default=None, description="UnderDoc API key")
    underdoc_api_endpoint: str = Field(default="https://api.underdoc.io", description="UnderDoc API endpoint")

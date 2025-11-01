from pydantic import BaseSettings, AnyUrl

class Settings(BaseSettings):
    telex_api_key: str
    telex_base_url: str = "https://api.telex.im"
    openai_api_key: str | None = None
    redis_url: str = "redis://localhost:6379/0"
    agent_public_url: AnyUrl
    agent_id: str = "iris-agent"
    # set the port uvicorn should use in deployment if needed
    class Config:
        env_file = ".env"

settings = Settings()

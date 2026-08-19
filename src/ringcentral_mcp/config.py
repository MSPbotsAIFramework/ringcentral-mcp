from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Non-credential configuration only.

    Per SOP §3.1/§9: credentials come from HTTP headers on every request,
    never from environment variables. No token/secret/account field belongs
    here — see server.py's GatewayTokenMiddleware for credential handling.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mcp_http_port: int = 8080
    mcp_http_host: str = "0.0.0.0"


def get_settings() -> Settings:
    return Settings()

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mcp_transport: Literal["stdio", "http"] = "stdio"
    mcp_http_port: int = 8080
    mcp_http_host: str = "0.0.0.0"

    # Auth mode:
    # "gateway" — production/SOP-compliant: credentials from HTTP headers per request (no global state)
    # "env"     — local dev only: shared credentials from env vars (not SOP-compliant)
    auth_mode: Literal["env", "gateway"] = "gateway"

    ringcentral_client_id: str | None = None
    ringcentral_client_secret: str | None = None
    ringcentral_jwt: str | None = None

    ringcentral_client_id_header: str = "X-RingCentral-Client-Id"
    ringcentral_client_secret_header: str = "X-RingCentral-Client-Secret"
    ringcentral_jwt_header: str = "X-RingCentral-Jwt"

    @property
    def has_credentials(self) -> bool:
        if self.auth_mode == "gateway":
            return True
        return all(
            [self.ringcentral_client_id, self.ringcentral_client_secret, self.ringcentral_jwt]
        )


def get_settings() -> Settings:
    return Settings()

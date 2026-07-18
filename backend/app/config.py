from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    supabase_url: str = ""
    supabase_anon_key: str = ""
    resend_api_key: str = ""
    resend_from_email: str = "onboarding@resend.dev"
    allowed_origins: str = "http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def db_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key)

    @property
    def email_configured(self) -> bool:
        return bool(self.resend_api_key)


settings = Settings()

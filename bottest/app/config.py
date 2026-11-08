import hashlib
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str
    venice_api_key: str
    crypto_pay_token: str
    crypto_pay_testnet: bool = False
    webhook_secret: str
    webhook_base_url: str
    database_url: str
    admin_ids: str = ""
    channel_id: str = ""
    channel_url: str = ""
    channel_title: str = "канал"
    trial_price_usd: float = 0.0
    pro_price_usd: float = 20.0
    daily_spend_cap: float = 3.0
    free_messages: int = 1
    daily_msg_limit: int = 200
    daily_token_limit: int = 300_000
    strong_daily_limit: int = 60
    auto_create_schema: bool = True
    use_polling: bool = False
    log_level: str = "INFO"
    tz: str = "UTC"
    effect_id: str = ""

    @property
    def admins(self) -> list[int]:
        return [int(x) for x in self.admin_ids.replace(" ", "").split(",") if x]

    @property
    def has_channel(self) -> bool:
        return bool(self.channel_id and self.channel_url)

    @property
    def webhook_path(self) -> str:
        return hashlib.sha256(self.webhook_secret.encode()).hexdigest()[:40]

    @property
    def crypto_base(self) -> str:
        return ("https://testnet-pay.crypt.bot/api" if self.crypto_pay_testnet
                else "https://pay.crypt.bot/api")


@lru_cache
def get_settings() -> Settings:
    return Settings()
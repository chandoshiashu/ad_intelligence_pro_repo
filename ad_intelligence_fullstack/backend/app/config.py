from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    tinyfish_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite-preview"
    demo_mode: bool = True
    cors_origins: str = "http://localhost:3000"
    meta_ad_library_base_url: str = "https://www.facebook.com/ads/library/"
    apify_api_token: str = ""
    apify_actor_id: str = "lergassy~meta-ad-library-scraper"
    apify_max_ads: int = 5
    apify_country: str = "IN"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

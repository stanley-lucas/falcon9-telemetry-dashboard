from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://falcon9:falcon9@localhost:5432/falcon9"
    spacex_api_base_url: str = "https://api.spacexdata.com/v4"
    api_base_url: str = "http://localhost:8000"

    # Falcon 9 reference constants (used for data validation and chart axes)
    FALCON9_ROCKET_ID: str = "5e9d0d95eda69973a809d1ec"
    MAX_ALTITUDE_KM: float = 250.0
    MAX_VELOCITY_KMS: float = 7.8
    FIRST_STAGE_BURN_DURATION_S: int = 162


settings = Settings()

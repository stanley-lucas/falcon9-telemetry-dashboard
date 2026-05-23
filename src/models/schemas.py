from datetime import datetime

from pydantic import BaseModel, computed_field


class LaunchpadSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    full_name: str
    locality: str
    region: str
    latitude: float
    longitude: float
    launch_attempts: int
    launch_successes: int


class CoreSchema(BaseModel):
    model_config = {"from_attributes": True}

    serial: str
    reuse_count: int
    rtls_attempts: int
    rtls_landings: int
    asds_attempts: int
    asds_landings: int


class LaunchCoreSchema(BaseModel):
    model_config = {"from_attributes": True}

    core_serial: str | None
    flight: int | None
    reused: bool | None
    landing_attempt: bool | None
    landing_success: bool | None
    landing_type: str | None


class LaunchSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    flight_number: int
    name: str
    date_utc: datetime
    success: bool | None
    details: str | None
    rocket_id: str
    launchpad_id: str | None
    launch_cores: list[LaunchCoreSchema] = []


class LaunchListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    flight_number: int
    name: str
    date_utc: datetime
    success: bool | None
    launchpad_id: str | None


class LandingStats(BaseModel):
    total_attempts: int
    total_successes: int
    rtls_attempts: int
    rtls_successes: int
    asds_attempts: int
    asds_successes: int

    @computed_field
    @property
    def success_rate_pct(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return round(self.total_successes / self.total_attempts * 100, 2)

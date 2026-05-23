import pandas as pd

from src.config import settings

LAUNCH_COLUMNS = ["id", "flight_number", "name", "date_utc", "success", "details", "rocket", "launchpad", "cores"]
LAUNCHPAD_COLUMNS = ["id", "name", "full_name", "locality", "region", "latitude", "longitude", "launch_attempts", "launch_successes"]
CORE_COLUMNS = ["serial", "reuse_count", "rtls_attempts", "rtls_landings", "asds_attempts", "asds_landings"]


def normalize_launches(raw: list[dict]) -> pd.DataFrame:
    """Filter to Falcon 9 only and normalize column names."""
    df = pd.json_normalize(raw)
    df = df[df["rocket"] == settings.FALCON9_ROCKET_ID].copy()
    df["date_utc"] = pd.to_datetime(df["date_utc"], utc=True)
    df = df[LAUNCH_COLUMNS].rename(columns={"rocket": "rocket_id", "launchpad": "launchpad_id"})
    return df.reset_index(drop=True)


def normalize_launchpads(raw: list[dict]) -> pd.DataFrame:
    df = pd.json_normalize(raw)
    return df[LAUNCHPAD_COLUMNS].reset_index(drop=True)


def normalize_cores(raw: list[dict]) -> pd.DataFrame:
    df = pd.json_normalize(raw)
    return df[CORE_COLUMNS].dropna(subset=["serial"]).reset_index(drop=True)

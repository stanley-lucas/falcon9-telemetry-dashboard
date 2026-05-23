from src.pipeline.transformer import normalize_cores, normalize_launches, normalize_launchpads
from src.config import settings

FALCON9_ID = settings.FALCON9_ROCKET_ID

RAW_LAUNCHES = [
    {
        "id": "launch-f9",
        "flight_number": 42,
        "name": "Starlink Group 1-1",
        "date_utc": "2020-10-24T15:31:00.000Z",
        "success": True,
        "details": "Nominal mission",
        "rocket": FALCON9_ID,
        "launchpad": "pad-1",
        "cores": [
            {
                "core": "B1049",
                "flight": 5,
                "gridfins": True,
                "legs": True,
                "reused": True,
                "landing_attempt": True,
                "landing_success": True,
                "landing_type": "ASDS",
            }
        ],
    },
    {
        "id": "launch-other",
        "flight_number": 1,
        "name": "Falcon 1 Flight 1",
        "date_utc": "2006-03-24T22:30:00.000Z",
        "success": False,
        "details": None,
        "rocket": "other-rocket-id",
        "launchpad": "pad-2",
        "cores": [],
    },
]

RAW_LAUNCHPADS = [
    {
        "id": "pad-1",
        "name": "VAFB SLC 4E",
        "full_name": "Vandenberg Space Force Base Space Launch Complex 4E",
        "locality": "Vandenberg",
        "region": "California",
        "latitude": 34.632,
        "longitude": -120.611,
        "launch_attempts": 50,
        "launch_successes": 48,
    }
]

RAW_CORES = [
    {
        "serial": "B1049",
        "reuse_count": 8,
        "rtls_attempts": 0,
        "rtls_landings": 0,
        "asds_attempts": 8,
        "asds_landings": 8,
    },
    {
        "serial": None,  # Should be dropped
        "reuse_count": 0,
        "rtls_attempts": 0,
        "rtls_landings": 0,
        "asds_attempts": 0,
        "asds_landings": 0,
    },
]


def test_normalize_launches_filters_falcon9_only():
    df = normalize_launches(RAW_LAUNCHES)
    assert len(df) == 1
    assert df.iloc[0]["id"] == "launch-f9"


def test_normalize_launches_renames_rocket_and_launchpad_columns():
    df = normalize_launches(RAW_LAUNCHES)
    assert "rocket_id" in df.columns
    assert "launchpad_id" in df.columns
    assert "rocket" not in df.columns
    assert "launchpad" not in df.columns


def test_normalize_launches_parses_dates_with_timezone():
    df = normalize_launches(RAW_LAUNCHES)
    assert df.iloc[0]["date_utc"].tzinfo is not None


def test_normalize_launches_preserves_cores_list():
    df = normalize_launches(RAW_LAUNCHES)
    cores = df.iloc[0]["cores"]
    assert isinstance(cores, list)
    assert cores[0]["core"] == "B1049"


def test_normalize_launchpads_returns_all_rows():
    df = normalize_launchpads(RAW_LAUNCHPADS)
    assert len(df) == 1
    assert df.iloc[0]["id"] == "pad-1"


def test_normalize_cores_drops_null_serials():
    df = normalize_cores(RAW_CORES)
    assert len(df) == 1
    assert df.iloc[0]["serial"] == "B1049"

import math
import requests
from dataclasses import dataclass
from datetime import date as _date, datetime, timedelta, timezone
from urllib.parse import urlencode

_TIME_FMT = "%Y-%m-%d %H:%M"
_DATAGETTER = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"


@dataclass
class Extreme:
    time: datetime
    value: float
    kind: str  # "H" or "L"


def parse_predictions(data: dict) -> list[Extreme]:
    return [
        Extreme(datetime.strptime(p["t"], _TIME_FMT), float(p["v"]), p["type"])
        for p in data["predictions"]
    ]


def build_datagetter_url(station_id: str, begin_date: str, end_date: str) -> str:
    params = {
        "product": "predictions",
        "station": station_id,
        "begin_date": begin_date,
        "end_date": end_date,
        "datum": "MLLW",
        "time_zone": "lst_ldt",
        "units": "english",
        "interval": "hilo",
        "format": "json",
    }
    return f"{_DATAGETTER}?{urlencode(params)}"


def fetch_tide_extremes(station_id: str, begin_date: str, end_date: str) -> list[Extreme]:
    url = build_datagetter_url(station_id, begin_date, end_date)
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise ValueError(data["error"].get("message", "NOAA datagetter error"))
    return parse_predictions(data)


def interpolate_height(extremes: list[Extreme], t: datetime) -> float | None:
    if not extremes or t < extremes[0].time or t > extremes[-1].time:
        return None
    for a, b in zip(extremes, extremes[1:]):
        if a.time <= t <= b.time:
            span = (b.time - a.time).total_seconds()
            if span == 0:
                return a.value
            frac = (t - a.time).total_seconds() / span
            mid = (a.value + b.value) / 2.0
            amp = (a.value - b.value) / 2.0
            return mid + amp * math.cos(math.pi * frac)
    return extremes[-1].value  # exactly the last extreme's time


def _julian_day_number(d: _date) -> int:
    """Julian Day Number for the calendar date (counting from noon UTC)."""
    a = (14 - d.month) // 12
    y = d.year + 4800 - a
    m = d.month + 12 * a - 3
    return (
        d.day
        + (153 * m + 2) // 5
        + 365 * y
        + y // 4
        - y // 100
        + y // 400
        - 32045
    )


def _julian_to_utc(jd: float) -> datetime:
    """Convert a Julian date to a timezone-aware UTC datetime."""
    unix_seconds = (jd - 2440587.5) * 86400.0
    return datetime.fromtimestamp(unix_seconds, tz=timezone.utc)


def sun_times(
    d: _date, lat: float, lon: float
) -> tuple[datetime | None, datetime | None]:
    """Sunrise and sunset for a calendar date as UTC-aware datetimes.

    Uses the NOAA sunrise equation (longitude east-positive). Returns
    ``(None, None)`` on polar day/night where the sun does not cross the
    horizon.
    """
    n = _julian_day_number(d) - 2451545 + 0.0008
    j_star = n - lon / 360.0  # mean solar noon (lon east-positive)

    M = (357.5291 + 0.98560028 * j_star) % 360.0
    M_rad = math.radians(M)
    C = (
        1.9148 * math.sin(M_rad)
        + 0.0200 * math.sin(2 * M_rad)
        + 0.0003 * math.sin(3 * M_rad)
    )
    lam = (M + C + 180.0 + 102.9372) % 360.0
    lam_rad = math.radians(lam)

    j_transit = (
        2451545.0
        + j_star
        + 0.0053 * math.sin(M_rad)
        - 0.0069 * math.sin(2 * lam_rad)
    )

    decl = math.asin(math.sin(lam_rad) * math.sin(math.radians(23.4397)))
    lat_rad = math.radians(lat)
    cos_w0 = (
        math.sin(math.radians(-0.833)) - math.sin(lat_rad) * math.sin(decl)
    ) / (math.cos(lat_rad) * math.cos(decl))
    if cos_w0 < -1.0 or cos_w0 > 1.0:
        return None, None  # sun stays up (or down) all day at this latitude/date

    w0 = math.degrees(math.acos(cos_w0))
    return (
        _julian_to_utc(j_transit - w0 / 360.0),
        _julian_to_utc(j_transit + w0 / 360.0),
    )


def sample_curve(
    extremes: list[Extreme], start: datetime, end: datetime, n: int
) -> list[tuple[datetime, float]]:
    span = (end - start).total_seconds()
    points: list[tuple[datetime, float]] = []
    for k in range(n + 1):
        t = start + timedelta(seconds=span * k / n)
        h = interpolate_height(extremes, t)
        if h is not None:
            points.append((t, h))
    return points

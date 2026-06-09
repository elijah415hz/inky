import math
import requests
from dataclasses import dataclass
from datetime import datetime, timedelta
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

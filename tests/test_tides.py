from datetime import datetime
from tides import Extreme, parse_predictions


def test_parse_predictions_maps_fields():
    data = {
        "predictions": [
            {"t": "2026-06-08 06:56", "v": "3.991", "type": "L"},
            {"t": "2026-06-08 10:34", "v": "4.638", "type": "H"},
        ]
    }
    result = parse_predictions(data)
    assert result == [
        Extreme(datetime(2026, 6, 8, 6, 56), 3.991, "L"),
        Extreme(datetime(2026, 6, 8, 10, 34), 4.638, "H"),
    ]


def test_parse_predictions_empty_list():
    assert parse_predictions({"predictions": []}) == []


from urllib.parse import urlparse, parse_qs
from tides import build_datagetter_url


def test_build_datagetter_url_has_required_params():
    url = build_datagetter_url("9444971", "20260606", "20260610")
    parsed = urlparse(url)
    assert parsed.netloc == "api.tidesandcurrents.noaa.gov"
    q = parse_qs(parsed.query)
    assert q["station"] == ["9444971"]
    assert q["product"] == ["predictions"]
    assert q["interval"] == ["hilo"]
    assert q["datum"] == ["MLLW"]
    assert q["time_zone"] == ["lst_ldt"]
    assert q["units"] == ["english"]
    assert q["format"] == ["json"]
    assert q["begin_date"] == ["20260606"]
    assert q["end_date"] == ["20260610"]


import pytest
import tides as tides_mod
from tides import fetch_tide_extremes


class _FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code != 200:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_fetch_tide_extremes_parses_ok(monkeypatch):
    payload = {"predictions": [{"t": "2026-06-08 10:34", "v": "4.638", "type": "H"}]}
    monkeypatch.setattr(tides_mod.requests, "get", lambda url, timeout=0: _FakeResponse(payload))
    result = fetch_tide_extremes("9444971", "20260606", "20260610")
    assert len(result) == 1
    assert result[0].kind == "H"


def test_fetch_tide_extremes_raises_on_error_payload(monkeypatch):
    payload = {"error": {"message": "No Predictions data was found."}}
    monkeypatch.setattr(tides_mod.requests, "get", lambda url, timeout=0: _FakeResponse(payload))
    with pytest.raises(ValueError):
        fetch_tide_extremes("9444971", "20260606", "20260610")


from datetime import timedelta
from tides import interpolate_height


def _extremes():
    base = datetime(2026, 6, 8, 0, 0)
    return [
        Extreme(base, 8.0, "H"),
        Extreme(base + timedelta(hours=6), 2.0, "L"),
        Extreme(base + timedelta(hours=12), 9.0, "H"),
    ]


def test_interpolate_returns_endpoints_exactly():
    ex = _extremes()
    assert interpolate_height(ex, ex[0].time) == pytest.approx(8.0)
    assert interpolate_height(ex, ex[1].time) == pytest.approx(2.0)


def test_interpolate_midpoint_is_mean():
    ex = _extremes()
    midpoint = ex[0].time + timedelta(hours=3)  # halfway H->L
    assert interpolate_height(ex, midpoint) == pytest.approx(5.0)


def test_interpolate_outside_range_returns_none():
    ex = _extremes()
    assert interpolate_height(ex, ex[0].time - timedelta(hours=1)) is None
    assert interpolate_height(ex, ex[-1].time + timedelta(hours=1)) is None


def test_interpolate_empty_returns_none():
    assert interpolate_height([], datetime(2026, 6, 8)) is None


from tides import sample_curve


def test_sample_curve_count_and_bounds():
    ex = _extremes()
    start = ex[0].time
    end = ex[-1].time
    pts = sample_curve(ex, start, end, 12)
    assert len(pts) == 13  # n+1 samples, all in range
    assert pts[0][0] == start
    assert pts[-1][0] == end
    # every sampled height is within the extremes' value envelope
    assert all(2.0 - 1e-9 <= h <= 9.0 + 1e-9 for _, h in pts)


def test_sample_curve_drops_points_outside_coverage():
    ex = _extremes()
    # window extends 6h before the first extreme -> leading samples are None and dropped
    start = ex[0].time - timedelta(hours=6)
    end = ex[-1].time
    pts = sample_curve(ex, start, end, 18)
    assert all(t >= ex[0].time for t, _ in pts)
    assert len(pts) < 19


from datetime import date, timezone
from tides import sun_times

# Mystery Bay, Marrowstone Island WA
_LAT, _LON = 48.063, -122.690


def test_sun_times_summer_solstice_matches_known_pacific_times():
    sunrise, sunset = sun_times(date(2026, 6, 20), _LAT, _LON)
    pdt = timezone(timedelta(hours=-7))
    # Port Townsend area solstice: sunrise ~5:11a, sunset ~9:15p PDT
    assert sunrise.astimezone(pdt).strftime("%H:%M") == "05:11"
    assert sunset.astimezone(pdt).strftime("%H:%M") == "21:15"


def test_sun_times_returns_utc_and_sunrise_before_sunset():
    sunrise, sunset = sun_times(date(2026, 12, 21), _LAT, _LON)
    assert sunrise.tzinfo == timezone.utc
    assert sunset.tzinfo == timezone.utc
    assert sunrise < sunset


def test_sun_times_polar_night_returns_none():
    # Above the Arctic Circle in midwinter the sun never rises.
    assert sun_times(date(2026, 12, 21), 78.0, 15.0) == (None, None)

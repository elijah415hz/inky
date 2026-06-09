from datetime import datetime, timedelta
import pytest
from pages.tidePage import (
    time_to_x,
    height_to_y,
    format_compact_time,
    CHART_LEFT,
    CHART_RIGHT,
    CHART_TOP,
    CHART_BOTTOM,
    SCALE_MIN_FT,
    SCALE_MAX_FT,
)


def test_time_to_x_endpoints_and_center():
    start = datetime(2026, 6, 8, 0, 0)
    end = start + timedelta(hours=48)
    assert time_to_x(start, start, end) == pytest.approx(CHART_LEFT)
    assert time_to_x(end, start, end) == pytest.approx(CHART_RIGHT)
    mid = start + timedelta(hours=24)
    assert time_to_x(mid, start, end) == pytest.approx((CHART_LEFT + CHART_RIGHT) / 2)


def test_height_to_y_is_inverted_and_scaled():
    assert height_to_y(SCALE_MIN_FT) == pytest.approx(CHART_BOTTOM)
    assert height_to_y(SCALE_MAX_FT) == pytest.approx(CHART_TOP)


def test_format_compact_time():
    assert format_compact_time(datetime(2026, 6, 8, 23, 54)) == "11:54p"
    assert format_compact_time(datetime(2026, 6, 8, 0, 0)) == "12:00a"
    assert format_compact_time(datetime(2026, 6, 8, 9, 5)) == "9:05a"


from datetime import datetime as _dt, timedelta as _td
from pages.tidePage import TidePage, WIDTH, HEIGHT
import pages.tidePage as tp
import tides


def _fake_window_extremes():
    # 5 days of synthetic extremes bracketing any 48h window around "now"
    base = _dt.now() - _td(days=2)
    vals = [8.5, 1.0, 9.0, 0.5]
    out = []
    t = base
    for i in range(40):
        out.append(tides.Extreme(t, vals[i % 4], "H" if i % 2 == 0 else "L"))
        t += _td(hours=6)
    return out


def test_make_image_returns_canvas(monkeypatch):
    monkeypatch.setattr(tp, "fetch_tide_extremes", lambda *a, **k: _fake_window_extremes())
    img = TidePage().make_image()
    assert img.size == (WIDTH, HEIGHT)
    assert img.mode == "RGBA"


def test_make_image_fallback_on_fetch_error(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("network down")
    monkeypatch.setattr(tp, "fetch_tide_extremes", boom)
    img = TidePage().make_image()
    assert img.size == (WIDTH, HEIGHT)
    assert img.mode == "RGBA"


def test_render_fallback_directly():
    img = TidePage()._render_fallback("Tide data unavailable")
    assert img.size == (WIDTH, HEIGHT)


def test_make_image_uses_red_now_line_and_blue_curve(monkeypatch):
    monkeypatch.setattr(tp, "fetch_tide_extremes", lambda *a, **k: _fake_window_extremes())
    img = TidePage().make_image().convert("RGB")
    colors = {color for _, color in img.getcolors(WIDTH * HEIGHT)}
    assert (255, 0, 0) in colors      # red "now" accent is drawn
    assert (0, 0, 255) in colors      # blue tide curve is drawn
    assert (0, 160, 0) not in colors  # old green now-line is gone

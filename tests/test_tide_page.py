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


@pytest.fixture(autouse=True)
def _isolate_cache(tmp_path, monkeypatch):
    # Each test gets its own cache file so the disk-backed last-good state never
    # leaks between tests (or into the repo).
    monkeypatch.setattr(tp, "CACHE_PATH", str(tmp_path / "tide_cache.json"))


def _extremes_around(anchor):
    # 10 days of synthetic extremes bracketing any 48h window around ``anchor``
    base = anchor - _td(days=2)
    vals = [8.5, 1.0, 9.0, 0.5]
    out = []
    t = base
    for i in range(40):
        out.append(tides.Extreme(t, vals[i % 4], "H" if i % 2 == 0 else "L"))
        t += _td(hours=6)
    return out


def _fake_window_extremes():
    return _extremes_around(_dt.now())


def _max_red_x(img):
    """Rightmost column containing a pure-red pixel (the now-line / its label)."""
    rgb = img.convert("RGB")
    px = rgb.load()
    rightmost = -1
    for x in range(WIDTH):
        for y in range(HEIGHT):
            if px[x, y] == (255, 0, 0):
                rightmost = x
                break
    return rightmost


def test_make_image_returns_canvas(monkeypatch):
    monkeypatch.setattr(tp, "fetch_tide_extremes", lambda *a, **k: _fake_window_extremes())
    img = TidePage().make_image()
    assert img.size == (WIDTH, HEIGHT)
    assert img.mode == "RGBA"


def test_make_image_fallback_on_cold_fetch_error(monkeypatch):
    # No data ever fetched and the API is down -> fallback frame.
    def boom(*a, **k):
        raise RuntimeError("network down")
    monkeypatch.setattr(tp, "fetch_tide_extremes", boom)
    img = TidePage().make_image()
    assert img.size == (WIDTH, HEIGHT)
    assert img.mode == "RGBA"


def test_failed_fetch_freezes_graph_and_advances_now_line(monkeypatch):
    page = TidePage()
    t0 = _dt(2026, 6, 10, 12, 0)
    monkeypatch.setattr(tp, "fetch_tide_extremes", lambda *a, **k: _extremes_around(t0))
    img_ok = page.make_image(now=t0)
    red_ok = _max_red_x(img_ok)

    # API goes down 24h later: the graph must persist (blue curve still drawn,
    # not the fallback frame) and the now-line must have moved to the right.
    def boom(*a, **k):
        raise RuntimeError("network down")
    monkeypatch.setattr(tp, "fetch_tide_extremes", boom)
    img_down = page.make_image(now=t0 + _td(hours=24))

    colors = {color for _, color in img_down.convert("RGB").getcolors(WIDTH * HEIGHT)}
    assert (0, 0, 255) in colors          # frozen tide curve is still there
    assert _max_red_x(img_down) > red_ok  # now-line advanced toward the future


def test_now_line_pins_to_right_edge_past_window(monkeypatch):
    page = TidePage()
    t0 = _dt(2026, 6, 10, 12, 0)
    monkeypatch.setattr(tp, "fetch_tide_extremes", lambda *a, **k: _extremes_around(t0))
    page.make_image(now=t0)

    def boom(*a, **k):
        raise RuntimeError("network down")
    monkeypatch.setattr(tp, "fetch_tide_extremes", boom)
    # 100h later is well past the 36h future edge; the now-line must stay pinned
    # at the right edge of the chart instead of running off the canvas.
    img = page.make_image(now=t0 + _td(hours=100))
    assert tp.CHART_RIGHT - 5 <= _max_red_x(img) < WIDTH


def test_cache_persists_across_instances(monkeypatch):
    t0 = _dt(2026, 6, 10, 12, 0)
    monkeypatch.setattr(tp, "fetch_tide_extremes", lambda *a, **k: _extremes_around(t0))
    TidePage().make_image(now=t0)  # writes the cache to disk

    # A fresh instance (e.g. after a restart) with the API down restores the
    # frozen graph from the on-disk cache rather than falling back.
    def boom(*a, **k):
        raise RuntimeError("network down")
    monkeypatch.setattr(tp, "fetch_tide_extremes", boom)
    img = TidePage().make_image(now=t0 + _td(hours=24))
    colors = {color for _, color in img.convert("RGB").getcolors(WIDTH * HEIGHT)}
    assert (0, 0, 255) in colors


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

from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

from pages.basePage import BasePage
from tides import fetch_tide_extremes, sample_curve, sun_times

STATION_ID = "9444971"
STATION_NAME = "Mystery Bay"
STATION_LAT = 48.063   # Mystery Bay, Marrowstone Island WA
STATION_LON = -122.690  # east-positive longitude

SCALE_MIN_FT = -4.0
SCALE_MAX_FT = 10.0

# "now" sits 1/4 from the left edge: a short look-back, a longer look-ahead.
PAST_HOURS = 12
FUTURE_HOURS = 36
REFRESH_RATE = 900

WIDTH = 600
HEIGHT = 448
MARGIN_X = 12
TITLE_RULE_Y = 60
CHART_LEFT = 12
CHART_RIGHT = 588
CHART_TOP = 122
CHART_BOTTOM = 391
CURVE_SAMPLES = 240

WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
BLUE = (0, 0, 255, 255)
RED = (255, 0, 0, 255)
NIGHT_FILL = (200, 200, 200, 255)  # gray band over hours between sunset and sunrise

TITLE_FONT_SIZE = 34
DATE_FONT_SIZE = 20
LABEL_FONT_SIZE = 22
NOW_LABEL_FONT_SIZE = 13
FALLBACK_FONT_SIZE = 34

CURVE_WIDTH = 3
MARKER_RADIUS = 3
LABEL_GAP = 6
LABEL_LINE_H = LABEL_FONT_SIZE + 2
# Vertical room a 2-line marker label occupies beyond its dot (height + time)
LABEL_BLOCK_H = MARKER_RADIUS + LABEL_GAP + 2 * LABEL_LINE_H
# Night bars span the full extent any label can reach: from above the highest
# high-label down to the bottom edge of the canvas (below the lowest low-label).
NIGHT_TOP = CHART_TOP - LABEL_BLOCK_H
NIGHT_BOTTOM = HEIGHT
TITLE_UNDERLINE_RIGHT = 220  # short editorial underline ends here (px from left)
NOW_DASH = 7                 # dash length on the "now" line (px)
NOW_GAP = 5                  # gap between "now" dashes (px)

_FONT_PATH = "JosefinSans-Bold.ttf"


def time_to_x(t: datetime, start: datetime, end: datetime) -> float:
    frac = (t - start).total_seconds() / (end - start).total_seconds()
    return CHART_LEFT + frac * (CHART_RIGHT - CHART_LEFT)


def height_to_y(value: float) -> float:
    frac = (value - SCALE_MIN_FT) / (SCALE_MAX_FT - SCALE_MIN_FT)
    return CHART_BOTTOM - frac * (CHART_BOTTOM - CHART_TOP)


def format_compact_time(t: datetime) -> str:
    return f"{t.strftime('%-I:%M')}{t.strftime('%p').lower()[0]}"


class TidePage(BasePage):
    refresh_rate = REFRESH_RATE

    def load_page(self):
        self.page_active = True

    def make_image(self) -> Image.Image:
        now = datetime.now()
        try:
            begin = (now - timedelta(days=2)).strftime("%Y%m%d")
            end = (now + timedelta(days=2)).strftime("%Y%m%d")
            extremes = fetch_tide_extremes(STATION_ID, begin, end)
            if not extremes:
                return self._render_fallback("Tide data unavailable")
        except Exception as e:  # network/JSON/error payload -> fallback frame
            print(f"Tide fetch failed: {e}")
            return self._render_fallback("Tide data unavailable")

        image = Image.new("RGBA", [WIDTH, HEIGHT], WHITE)
        d = ImageDraw.Draw(image)
        self._draw_header(d, now)

        window_start = now - timedelta(hours=PAST_HOURS)
        window_end = now + timedelta(hours=FUTURE_HOURS)

        # Night shading (drawn first so the curve and labels render on top)
        self._draw_night_shading(d, window_start, window_end)

        # Curve
        curve = sample_curve(extremes, window_start, window_end, CURVE_SAMPLES)
        pts = [(time_to_x(t, window_start, window_end), height_to_y(v)) for t, v in curve]
        if len(pts) >= 2:
            d.line(pts, fill=BLUE, width=CURVE_WIDTH, joint="curve")

        # "Now" vertical line (1/4 from the left) — thin red dashed accent with a small label
        x_now = time_to_x(now, window_start, window_end)
        self._dashed_vline(d, x_now, CHART_TOP, CHART_BOTTOM, RED)
        now_fnt = ImageFont.truetype(_FONT_PATH, NOW_LABEL_FONT_SIZE)
        d.text((x_now + 5, CHART_TOP - 4), "now", font=now_fnt, fill=RED)

        # H/L markers + labels (only those inside the visible window)
        label_fnt = ImageFont.truetype(_FONT_PATH, LABEL_FONT_SIZE)
        for ex in extremes:
            if not (window_start <= ex.time <= window_end):
                continue
            self._draw_marker(d, ex, window_start, window_end, label_fnt)

        return image

    def _dashed_vline(self, d, x, y0, y1, color) -> None:
        y = y0
        while y < y1:
            d.line((x, y, x, min(y + NOW_DASH, y1)), fill=color, width=2)
            y += NOW_DASH + NOW_GAP

    def _night_spans(self, window_start, window_end):
        """Dark (sunset->sunrise) intervals overlapping the visible window.

        Sun times are computed in UTC, then converted to the device's local
        time so they line up with the device-clock "now" line and the
        station-local tide curve.
        """
        spans = []
        day = (window_start - timedelta(days=1)).date()
        last = window_end.date()
        while day <= last:
            _, sunset = sun_times(day, STATION_LAT, STATION_LON)
            sunrise_next, _ = sun_times(day + timedelta(days=1), STATION_LAT, STATION_LON)
            if sunset is None or sunrise_next is None:
                day += timedelta(days=1)
                continue
            start = sunset.astimezone().replace(tzinfo=None)
            end = sunrise_next.astimezone().replace(tzinfo=None)
            # clip to the visible window
            start = max(start, window_start)
            end = min(end, window_end)
            if start < end:
                spans.append((start, end))
            day += timedelta(days=1)
        return spans

    def _draw_night_shading(self, d, window_start, window_end) -> None:
        for start, end in self._night_spans(window_start, window_end):
            x0 = time_to_x(start, window_start, window_end)
            x1 = time_to_x(end, window_start, window_end)
            d.rectangle([x0, NIGHT_TOP, x1, NIGHT_BOTTOM], fill=NIGHT_FILL)

    def _draw_header(self, d: ImageDraw.ImageDraw, now: datetime) -> None:
        title_fnt = ImageFont.truetype(_FONT_PATH, TITLE_FONT_SIZE)
        date_fnt = ImageFont.truetype(_FONT_PATH, DATE_FONT_SIZE)
        d.text((MARGIN_X, 12), STATION_NAME, font=title_fnt, fill=BLACK)
        date_str = now.strftime("%a %b %-d")
        w = d.textlength(date_str, font=date_fnt)
        # smaller date sits lower so it reads as a subtitle aligned to the title
        d.text((WIDTH - MARGIN_X - w, 26), date_str, font=date_fnt, fill=BLACK)
        # short editorial underline beneath the title only (not a full-width slab)
        d.line((MARGIN_X, TITLE_RULE_Y, TITLE_UNDERLINE_RIGHT, TITLE_RULE_Y), fill=BLACK, width=3)

    def _draw_marker(self, d, ex, window_start, window_end, fnt) -> None:
        x = time_to_x(ex.time, window_start, window_end)
        y = height_to_y(ex.value)
        d.ellipse(
            [x - MARKER_RADIUS, y - MARKER_RADIUS, x + MARKER_RADIUS, y + MARKER_RADIUS],
            fill=BLACK,
        )
        value_str = f"{ex.value:.1f}"
        time_str = format_compact_time(ex.time)
        line_h = LABEL_LINE_H
        vw = d.textlength(value_str, font=fnt)
        tw = d.textlength(time_str, font=fnt)
        block_w = max(vw, tw)

        # Place above highs, below lows
        if ex.kind == "H":
            top = y - MARKER_RADIUS - LABEL_GAP - 2 * line_h
        else:
            top = y + MARKER_RADIUS + LABEL_GAP

        # Horizontal anchor with edge-nudge so labels never clip
        left = x - block_w / 2
        left = max(CHART_LEFT, min(left, CHART_RIGHT - block_w))

        d.text((left + (block_w - vw) / 2, top), value_str, font=fnt, fill=BLACK)
        d.text((left + (block_w - tw) / 2, top + line_h), time_str, font=fnt, fill=BLACK)

    def _render_fallback(self, message: str) -> Image.Image:
        image = Image.new("RGBA", [WIDTH, HEIGHT], WHITE)
        d = ImageDraw.Draw(image)
        self._draw_header(d, datetime.now())
        fnt = ImageFont.truetype(_FONT_PATH, FALLBACK_FONT_SIZE)
        w = d.textlength(message, font=fnt)
        d.text(((WIDTH - w) / 2, HEIGHT / 2 - FALLBACK_FONT_SIZE), message, font=fnt, fill=BLACK)
        return image

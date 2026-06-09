import time
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

from pages.basePage import BasePage
from tides import fetch_tide_extremes, sample_curve

STATION_ID = "9444971"
STATION_NAME = "Mystery Bay"

SCALE_MIN_FT = -4.0
SCALE_MAX_FT = 10.0

WINDOW_HOURS = 24
REFRESH_RATE = 900

WIDTH = 600
HEIGHT = 448
MARGIN_X = 12
TITLE_RULE_Y = 60
CHART_LEFT = 12
CHART_RIGHT = 588
CHART_TOP = 95
CHART_BOTTOM = 395
CURVE_SAMPLES = 240

WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
BLUE = (0, 0, 255, 255)
GREEN = (0, 160, 0, 255)

TITLE_FONT_SIZE = 34
LABEL_FONT_SIZE = 18
FALLBACK_FONT_SIZE = 34
MARKER_HALF = 4
LABEL_GAP = 6

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

    def unload_page(self):
        self.page_active = False

    def start_refresh(self):
        while self.page_active:
            yield self.make_image()
            time.sleep(self.refresh_rate)

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

        window_start = now - timedelta(hours=WINDOW_HOURS)
        window_end = now + timedelta(hours=WINDOW_HOURS)

        # Curve
        curve = sample_curve(extremes, window_start, window_end, CURVE_SAMPLES)
        pts = [(time_to_x(t, window_start, window_end), height_to_y(v)) for t, v in curve]
        if len(pts) >= 2:
            d.line(pts, fill=BLUE, width=4, joint="curve")

        # "Now" vertical line (centered)
        x_now = time_to_x(now, window_start, window_end)
        d.line((x_now, CHART_TOP, x_now, CHART_BOTTOM), fill=GREEN, width=3)

        # H/L markers + labels (only those inside the visible window)
        label_fnt = ImageFont.truetype(_FONT_PATH, LABEL_FONT_SIZE)
        for ex in extremes:
            if not (window_start <= ex.time <= window_end):
                continue
            self._draw_marker(d, ex, window_start, window_end, label_fnt)

        return image

    def _draw_header(self, d: ImageDraw.ImageDraw, now: datetime) -> None:
        title_fnt = ImageFont.truetype(_FONT_PATH, TITLE_FONT_SIZE)
        d.text((MARGIN_X, 12), STATION_NAME, font=title_fnt, fill=BLACK)
        date_str = now.strftime("%a %b %-d")
        w = d.textlength(date_str, font=title_fnt)
        d.text((WIDTH - MARGIN_X - w, 12), date_str, font=title_fnt, fill=BLACK)
        d.line((0, TITLE_RULE_Y, WIDTH, TITLE_RULE_Y), fill=BLACK, width=4)

    def _draw_marker(self, d, ex, window_start, window_end, fnt) -> None:
        x = time_to_x(ex.time, window_start, window_end)
        y = height_to_y(ex.value)
        d.rectangle(
            [x - MARKER_HALF, y - MARKER_HALF, x + MARKER_HALF, y + MARKER_HALF],
            fill=BLACK,
        )
        value_str = f"{ex.value:.1f}"
        time_str = format_compact_time(ex.time)
        line_h = LABEL_FONT_SIZE + 2
        vw = d.textlength(value_str, font=fnt)
        tw = d.textlength(time_str, font=fnt)
        block_w = max(vw, tw)

        # Place above highs, below lows
        if ex.kind == "H":
            top = y - MARKER_HALF - LABEL_GAP - 2 * line_h
        else:
            top = y + MARKER_HALF + LABEL_GAP

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

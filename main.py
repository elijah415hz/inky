"""On-device entrypoint: wires the Inky display to the four hardware buttons.

All hardware imports (inky, gpiod, gpiodevice) live here so the off-device
tooling (preview.py, the test suite, page_controller) stays importable on a
laptop without the Raspberry Pi packages.
"""
import threading

import gpiod
import gpiodevice
from gpiod.line import Bias, Direction, Edge
from inky.auto import auto

from page_controller import PageController
from pages.tidePage import TidePage
from pages.weatherTravelPage import WeatherTravelPage

# Inky Impression buttons A, B, C, D -> BCM GPIO pins (active-low).
BUTTONS = [5, 6, 16, 24]
LABELS = ["A", "B", "C", "D"]

# Page bound to each button. A and B select their page directly; D cycles
# through all pages (one button steps through everything). C is reserved.
PAGES = {
    "A": TidePage(),
    "B": WeatherTravelPage(),
}
START_KEY = "A"
CYCLE_LABEL = "D"


def _watch_buttons(controller: PageController) -> None:
    """Blocking gpiod edge loop, run in a daemon thread -> controller.request.

    Follows Pimoroni's official Inky button example (gpiod + gpiodevice).
    """
    input_settings = gpiod.LineSettings(
        direction=Direction.INPUT, bias=Bias.PULL_UP, edge_detection=Edge.FALLING
    )
    chip = gpiodevice.find_chip_by_platform()
    offsets = [chip.line_offset_from_id(pin) for pin in BUTTONS]
    request = chip.request_lines(
        consumer="inky-buttons", config=dict.fromkeys(offsets, input_settings)
    )
    while True:
        for event in request.read_edge_events():
            label = LABELS[offsets.index(event.line_offset)]
            if label == CYCLE_LABEL:
                controller.cycle()
            else:
                controller.request(label)


def main() -> None:
    display = auto()
    print(display.resolution)
    controller = PageController(PAGES, start_key=START_KEY)
    watcher = threading.Thread(target=_watch_buttons, args=(controller,), daemon=True)
    watcher.start()
    controller.run(display)


if __name__ == "__main__":
    main()

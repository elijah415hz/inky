import pytest

from page_controller import PageController
from pages.basePage import BasePage


class FakePage(BasePage):
    refresh_rate = 1

    def __init__(self, name):
        self.name = name
        self.loaded = 0
        self.unloaded = 0
        self.rendered = 0

    def load_page(self):
        self.page_active = True
        self.loaded += 1

    def unload_page(self):
        self.page_active = False
        self.unloaded += 1

    def make_image(self):
        self.rendered += 1
        return object()


class FakeDisplay:
    def __init__(self):
        self.images = []
        self.shows = 0

    def set_image(self, image):
        self.images.append(image)

    def show(self):
        self.shows += 1


def make_controller():
    pages = {"A": FakePage("A"), "B": FakePage("B")}
    return PageController(pages, start_key="A"), pages


def test_invalid_start_key_raises():
    with pytest.raises(ValueError):
        PageController({"A": FakePage("A")}, start_key="Z")


def test_request_switches_page_and_swaps_load_state():
    ctrl, pages = make_controller()
    ctrl.request("B")
    assert ctrl._wake.is_set()
    ctrl._apply_request()
    assert ctrl.current_key == "B"
    assert ctrl.current_page is pages["B"]
    assert pages["A"].unloaded == 1
    assert pages["B"].loaded == 1


def test_request_same_page_forces_refresh_without_reload():
    ctrl, pages = make_controller()
    ctrl.request("A")
    assert ctrl._wake.is_set()
    ctrl._apply_request()
    assert ctrl.current_key == "A"
    assert pages["A"].unloaded == 0
    assert pages["A"].loaded == 0


def test_unknown_button_is_ignored():
    ctrl, pages = make_controller()
    ctrl.request("C")
    assert not ctrl._wake.is_set()
    ctrl._apply_request()
    assert ctrl.current_key == "A"


def test_cycle_advances_to_next_page_and_wraps():
    ctrl, pages = make_controller()  # starts on A, pages A -> B
    ctrl.cycle()
    assert ctrl._wake.is_set()
    ctrl._apply_request()
    assert ctrl.current_key == "B"
    ctrl.cycle()
    ctrl._apply_request()
    assert ctrl.current_key == "A"  # wrapped back around


def test_cycle_steps_from_pending_request_on_rapid_presses():
    ctrl, pages = make_controller()  # starts on A
    ctrl.cycle()  # queues B
    ctrl.cycle()  # steps past pending B -> wraps to A before any apply
    ctrl._apply_request()
    assert ctrl.current_key == "A"


def test_render_once_draws_active_page_to_display():
    ctrl, pages = make_controller()
    display = FakeDisplay()
    ctrl.render_once(display)
    assert display.shows == 1
    assert len(display.images) == 1
    assert pages["A"].rendered == 1

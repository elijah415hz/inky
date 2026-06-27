from abc import ABC, abstractmethod
from PIL.Image import Image


class BasePage(ABC):
    # Seconds between automatic re-renders while this page is shown.
    # Subclasses override to taste.
    refresh_rate: int = 900
    page_active = False

    @abstractmethod
    def load_page(self):
        pass

    @abstractmethod
    def make_image(self) -> Image:
        pass

    def unload_page(self):
        self.page_active = False

from abc import ABC, abstractmethod
from typing import Generator
from PIL.Image import Image

class BasePage(ABC):
    pageActive = False

    @abstractmethod
    def load_page(self):
        pass

    @abstractmethod
    def start_refresh(self) -> Generator[Image, None, None]:
        pass

    @abstractmethod
    def make_image(self) -> Image:
        pass

    def unload_page(self):
        self.pageActive = False
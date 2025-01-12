from pages.basePage import BasePage
from pages.weatherTravelPage import WeatherTravelPage
import inky.auto as auto


class main():

    page: BasePage = WeatherTravelPage()

    def __init__(self):
        self.display = auto()
        print(self.display.resolution)
        self.page.load_page()
        self.start_refresh_page()

    def start_refresh_page(self):
        for image in self.page.start_refresh():
            self.display.set_image(image)
            self.display.show()

if __name__ == "__main__":
    main()

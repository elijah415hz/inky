from pages.basePage import BasePage
from pages.weatherTravelPage import WeatherTravelPage


class main():

    page: BasePage = WeatherTravelPage()

    def __init__(self):
        self.page.load_page()
        self.start_refresh_page()

    def start_refresh_page(self):
        for image in self.page.start_refresh():
            image.show()

if __name__ == "__main__":
    main()
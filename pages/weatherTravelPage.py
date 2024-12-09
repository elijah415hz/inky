import os
import time
from pages.basePage import BasePage
from PIL import Image, ImageDraw, ImageFont
from image import get_color_from_gradient
from routes import get_time_to_destination
from weather import get_weather
import colorcet as cc


home_address = os.getenv("HOME_ADDRESS") or ""
met_address = os.getenv("MET_ADDRESS") or ""
school_address = os.getenv("SCHOOL_ADDRESS") or ""

class WeatherTravelPage(BasePage):
    refresh_rate = 60

    def load_page(self):
        # Load the page
        self.page_active = True
        self.start_refresh()

    def unload_page(self):
        self.page_active = False

    def start_refresh(self):
        while self.page_active:
            image = self.make_image()
            yield image
            time.sleep(self.refresh_rate)

    def make_image(self):
        home_address = os.getenv("HOME_ADDRESS") or ""
        met_address = os.getenv("MET_ADDRESS") or ""
        school_address = os.getenv("SCHOOL_ADDRESS") or ""

        travel_time = f"""
Time to Misshattan: {get_time_to_destination(home_address, met_address)}
Time to School: {get_time_to_destination(home_address, school_address)}
"""

        api_key = os.getenv("OPEN_WEATHER_API_KEY")
        zip = os.getenv("WEATHER_ZIP")
        weather = get_weather(api_key, zip)

        weather_str = f"Weather: {weather['weather']}\nTemperature: {weather['temp']}°F\nMin Temp: {weather['temp_min']}°F\nMax Temp: {weather['temp_max']}°F"

        text = f"{travel_time}\n\n\n\n{weather_str}"

        bg_color = get_color_from_gradient(int(weather["temp"]), 0, 115, cc.m_coolwarm)
        image = Image.new("RGBA", [600, 448], bg_color)

        # get a font
        fnt = ImageFont.truetype("JosefinSans-Bold.ttf", 40)
        # get a drawing context
        d = ImageDraw.Draw(image)

        # draw text
        text_color=(255, 255, 255, 255)
        d.text((10, 10), text, font=fnt, fill=text_color)
        # draw a line
        d.line((0, 140, image.size[0], 140), fill=text_color, width=7)

        weather_img = Image.open('weather_image.png', 'r')
        image.paste(weather_img, (10, 140), mask=weather_img)

        return image

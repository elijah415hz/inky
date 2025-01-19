import os
import time
from datetime import datetime
from pages.basePage import BasePage
from PIL import Image, ImageDraw, ImageFont
from image import get_color_from_gradient
from routes import get_time_to_destination
from weather import get_weather
import colorcet as cc


home_address = os.getenv("HOME_ADDRESS") or ""
met_address = os.getenv("MET_ADDRESS") or ""
school_address = os.getenv("SCHOOL_ADDRESS") or ""

round_if_float = lambda x: round(x) if isinstance(x, float) else x

class WeatherTravelPage(BasePage):
    refresh_rate = 360

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
Misshattan: {get_time_to_destination(home_address, met_address)}
School: {get_time_to_destination(home_address, school_address)}
"""

        api_key = os.getenv("OPEN_WEATHER_API_KEY")
        zip = os.getenv("WEATHER_ZIP")
        weather = get_weather(api_key, zip)

        weatherDescription = str(weather['weather'])
        for i in range(len(weatherDescription)):
            if i % 28 == 0 and i != 0:
                j = i
                found = False
                while found == False:
                    if weatherDescription[j].isspace():
                        found = True
                        j += 1 # Get in front of the space to leave it on upper line
                        weatherDescription = weatherDescription[:j] + "\n" + weatherDescription[j:]
                    j -= 1
        weather_str = f"{weatherDescription}\n\nTemperature: {round_if_float(weather['temp'])}°F\nLow: {round_if_float(weather['temp_min'])}°F - High: {round_if_float(weather['temp_max'])}°F"

        text = f"{travel_time}\n{weather_str}"

        if weather["temp"] == "??":
            weather['temp'] = 0

        bg_color = get_color_from_gradient(int(weather["temp"]), 0, 115, cc.m_coolwarm)
        image = Image.new("RGBA", [600, 448], bg_color)

        # get a font
        fnt = ImageFont.truetype("JosefinSans-Bold.ttf", 40)
        # get a drawing context
        d = ImageDraw.Draw(image)

        # draw text
        text_color=(0, 0, 0, 255)
        d.text((10, 40), text, font=fnt,  fill=text_color)
        # draw a line
        d.line((0, 160, image.size[0], 160), fill=text_color, width=7)

        weather_img = Image.open('weather_image.png', 'r')
        image.paste(weather_img, (505, 320), mask=weather_img)

        # Add refresh time
        now = datetime.now()
        timeStr = now.strftime("%-I:%M %p")
        fnt = ImageFont.truetype("JosefinSans-Bold.ttf", 20)
        d.text((515, 418), timeStr, font=fnt, fill=text_color)

        return image

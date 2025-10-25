import os
import time
from datetime import datetime
from pages.basePage import BasePage
from PIL import Image, ImageDraw, ImageFont
from image import get_color_from_gradient
from ferries import get_kingston_edmonds_sailing_times, get_kingston_wait_time
from weather import get_weather
from temperature_sensor import get_inside_temperature
import colorcet as cc


round_if_float = lambda x: round(x) if isinstance(x, float) else x

def to_celcius(temp):
    if not isinstance(temp, float):
        return temp
    return round_if_float((temp - 32) * 5.0/9.0)

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
        # Get ferry sailing times and wait time guidance
        try:
            api_key = os.getenv("WSDOT_API_ACCESS_CODE")
            ferry_times = get_kingston_edmonds_sailing_times(api_key)
            wait_guidance = get_kingston_wait_time(api_key)
            ferry_info = f"Ferry (Kingston → Edmonds):\nNext sailings: {ferry_times}\nGuidance: {wait_guidance}"
        except Exception as e:
            ferry_info = f"Ferry info unavailable: {str(e)}"

        # Get inside temperature from sensor
        inside_temp = get_inside_temperature()
        if inside_temp is not None:
            inside_temp_str = f"Inside Temp: {round_if_float(inside_temp)}°F/{to_celcius(inside_temp)}°C"
        else:
            inside_temp_str = "Inside Temp: Unavailable"

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
        weather_str = f"{weatherDescription}\n\nTemperature: {round_if_float(weather['temp'])}°F/{to_celcius(weather['temp'])}°C\nLo: {round_if_float(weather['temp_min'])}°F/{to_celcius(weather['temp_min'])}°C - Hi: {round_if_float(weather['temp_max'])}°F/{to_celcius(weather['temp_max'])}°C"

        text = f"{ferry_info}\n\n{weather_str}\n\n{inside_temp_str}"

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

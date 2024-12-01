import os
import colorcet as cc

from routes import get_time_to_destination
from weather import get_weather
from image import make_image

home_address = os.getenv("HOME_ADDRESS") or ""
met_address = os.getenv("MET_ADDRESS") or ""

travel_time = f"Time to Misshattan: {get_time_to_destination(home_address, met_address)}"

api_key = os.getenv("OPEN_WEATHER_API_KEY")
zip = os.getenv("WEATHER_ZIP")
weather = get_weather(api_key, zip)

weather_str = f"Temperature: {weather['temp']}°F\nWeather: {weather['weather']}\nMax Temp: {weather['temp_max']}°F\nMin Temp: {weather['temp_min']}°F\nFeels Like: {weather['feels_like']}°F"

def get_temperature_color(temp: int) -> tuple[int, int, int, int]:
    min_temp = 0
    max_temp = 115
    normalized_temp = (temp - min_temp) / (max_temp - min_temp)
    color = cc.coolwarm[int(normalized_temp * 255)]
    return color

make_image(f"{travel_time}\n\n{weather_str}", get_temperature_color(int(weather["temp"])))
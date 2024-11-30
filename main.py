from routes import get_time_to_destination
from weather import get_weather
import os
home_address = os.getenv('HOME_ADDRESS') or ""
met_address = os.getenv('MET_ADDRESS') or ""

# print(f"Time to Misshattan: {get_time_to_destination(home_address, met_address)}")

api_key = os.getenv("OPEN_WEATHER_API_KEY")
zip = os.getenv("WEATHER_ZIP")
weather = get_weather(api_key, zip)
print(f"Temperature: {weather['temp']}°F\nWeather: {weather['weather']}\nMax Temp: {weather['temp_max']}°F\nMin Temp: {weather['temp_min']}°F\nFeels Like: {weather['feels_like']}°F")

import requests
import colorcet as cc


def get_weather(api_key, zip) -> dict[str, float | str]:
    url = f"http://api.openweathermap.org/geo/1.0/zip?zip={zip}&appid={api_key}"
    # print(url)
    try:
        response = requests.get(url)
        res = response.json()
        print(res)
        url = f"http://api.openweathermap.org/data/3.0/onecall?lat={res['lat']}&lon={res['lon']}&exclude=hourly&units=imperial&appid={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            res = response.json()
            current = res['current']
            daily = res['daily'][0]
            temp = current['temp']
            weather = daily['summary']
            temp_max = daily['temp']['max']
            temp_min = daily['temp']['min']
            feels_like = current['feels_like']

            img_data = requests.get(f"http://openweathermap.org/img/wn/{current['weather'][0]['icon']}@2x.png").content
            with open('weather_image.png', 'wb') as handler:
                handler.write(img_data)
            return {
                "temp": temp,
                "weather": weather,
                "temp_max": temp_max,
                "temp_min": temp_min,
                "feels_like": feels_like
            }
        else:
            return {
            "temp": "??",
            "weather": "??",
            "temp_max": "??",
            "temp_min": "??",
            "feels_like": "??"
        }
    except Exception as e:
        print(e)
        return {
            "temp": "??",
            "weather": "??",
            "temp_max": "??",
            "temp_min": "??",
            "feels_like": "??"
        }

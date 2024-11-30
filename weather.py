import requests


def get_weather(api_key, zip):
    url = f"http://api.openweathermap.org/geo/1.0/zip?zip={zip}&appid={api_key}"
    print(url)
    response = requests.get(url)
    res = response.json()
    print(res)
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={res['lat']}&lon={res['lon']}&units=imperial&appid={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        res = response.json()
        temp = res['main']['temp']
        weather = res['weather'][0]['description']
        temp_max = res['main']['temp_max']
        temp_min = res['main']['temp_min']
        feels_like = res['main']['feels_like']

        img_data = requests.get(f"http://openweathermap.org/img/wn/{res['weather'][0]['icon']}@2x.png").content
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
        print(response.json())
        return {
            "temp": "??",
            "weather": "??",
            "temp_max": "??",
            "temp_min": "??",
            "feels_like": "??"
        }
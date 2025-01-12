import requests
import os


def get_time_to_destination(origin: str, destination: str) -> str:

    APIKey = os.getenv('GOOGLE_MAPS_API_KEY')

    routesApiURL = 'https://routes.googleapis.com/directions/v2:computeRoutes'

    # print(f"Getting time from", {origin}, "to", {destination})

    body = {
    "origin":{
        "address": origin
    },
    "destination":{
        "address": destination
    },
    "travelMode": "DRIVE",
    "routingPreference": "TRAFFIC_AWARE",
    "computeAlternativeRoutes": False,
    "routeModifiers": {
        "avoidTolls": False,
        "avoidHighways": False,
        "avoidFerries": False
    },
    "languageCode": "en-US",
    "units": "IMPERIAL"
    }
    headers = {
        'X-Goog-Api-Key': APIKey,
        'X-Goog-FieldMask': 'routes.distanceMeters,routes.duration,routes.localizedValues'
    }
    try:
        response = requests.post(routesApiURL, json=body, headers=headers)
        resJson = response.json()
        print(resJson)
        duration = resJson['routes'][0]['localizedValues']['duration']['text']
        return duration
    except Exception as e:
        print(e)
        return "??"

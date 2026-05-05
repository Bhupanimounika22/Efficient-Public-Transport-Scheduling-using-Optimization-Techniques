import requests

WEATHER_API_KEY = "ENTER YOUR API KEY"
weather_cache = {}

def get_weather(city="Vijayawada"):
    if city in weather_cache:
        return weather_cache[city]

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        res = requests.get(url, timeout=5).json()
        main = res['weather'][0]['main']

        if main == "Rain":
            weather = "Rainy"
        elif main == "Clouds":
            weather = "Cloudy"
        else:
            weather = "Clear"

        weather_cache[city] = weather
        return weather

    except:
        return "Clear"


def get_season(month):
    if month in [3,4,5]:
        return "Summer"
    elif month in [6,7,8,9]:
        return "Monsoon"
    return "Winter"


def get_exam_features(month):
    if month in [3,4]:
        return 1, 0
    elif month == 5:
        return 0, 1
    return 0, 0


def get_traffic(hour, day, is_holiday, festival):
    # deterministic logic (NO randomness)

    if 9 <= hour <= 11 or 17 <= hour <= 20:
        traffic = "High"
    elif 12 <= hour <= 16:
        traffic = "Medium"
    else:
        traffic = "Low"

    if day in ["Saturday", "Sunday"]:
        if traffic == "High":
            traffic = "Medium"
        elif traffic == "Medium":
            traffic = "Low"

    if is_holiday:
        traffic = "Low"

    if festival:
        f = festival.lower()
        if any(x in f for x in ["diwali","dussehra"]):
            traffic = "High"
        elif any(x in f for x in ["pongal","sankranti","ugadi"]):
            traffic = "Low"

    return traffic

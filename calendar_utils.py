import requests

HOLIDAY_API_KEY = "ENTER YOUR API KEY"
holiday_cache = {}

def get_calendar_data(date):

    try:
        year = date.year

        if year not in holiday_cache:
            url = f"https://calendarific.com/api/v2/holidays?api_key={HOLIDAY_API_KEY}&country=IN&year={year}"
            res = requests.get(url, timeout=5).json()
            holiday_cache[year] = res['response']['holidays']

        holidays = holiday_cache[year]
        date_str = str(date.date())

        for h in holidays:
            if h['date']['iso'] == date_str:

                name = h['name'].lower()

                if any(x in name for x in ["pongal","sankranti","ugadi"]):
                    return 1, -0.3, h['name']

                if any(x in name for x in ["diwali","dussehra"]):
                    return 1, 0.4, h['name']

                if "National holiday" in h['type']:
                    return 1, -0.5, h['name']

                return 1, 0, h['name']

        return 0, 0, None

    except Exception as e:
        print("Calendar Error:", e)
        return 0, 0, None

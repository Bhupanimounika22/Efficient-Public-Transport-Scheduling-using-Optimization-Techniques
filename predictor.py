import pandas as pd
import joblib
from calendar_utils import get_calendar_data
from utils import get_weather, get_traffic, get_season, get_exam_features

model = joblib.load("model/xgb_model.pkl")
feature_columns = joblib.load("model/feature_columns.pkl")


def predict_passengers(date, route, hour, weather=None):

    day = date.day_name()
    month = date.month

    if weather is None:
        weather = get_weather()

    holiday_flag, _, festival_name = get_calendar_data(date)

    traffic = get_traffic(hour, day, holiday_flag, festival_name)
    exam_s, exam_e = get_exam_features(month)

    input_data = {
        "route": route,
        "day_of_week": day,
        "month": month,
        "hour": hour,
        "is_weekend": 1 if day in ["Saturday","Sunday"] else 0,
        "is_holiday": holiday_flag,
        "season": get_season(month),
        "traffic": traffic,
        "weather": weather,
        "festival_nearby": holiday_flag,
        "exam_season": exam_s,
        "exam_end_rush": exam_e
    }

    df = pd.DataFrame([input_data])

    df = pd.get_dummies(df, columns=[
        "route","day_of_week","season","traffic","weather"
    ])

    df = df.reindex(columns=feature_columns, fill_value=0)

    passengers = int(round(model.predict(df)[0]))

    info = {
        "weather": weather,
        "traffic": traffic,
        "holiday": "Yes" if holiday_flag else "No",
        "festival": festival_name if festival_name else "None"
    }

    return passengers, info
import numpy as np
import pandas as pd
import joblib

df = pd.read_csv("data/bus_demand_real_api_2025.csv")

model = joblib.load("model/xgb_model.pkl")
feature_columns = joblib.load("model/feature_columns.pkl")

df['date'] = pd.to_datetime(df['date'])
routes = df['route'].unique()
hours = df['hour'].unique()

dates_2026 = pd.date_range("2026-01-01","2026-12-31")

future_data = []

for date in dates_2026:
    for route in routes:
        for hour in hours:

            month = date.month
            day = date.day_name()

            future_data.append({
                "date": date,
                "route": route,
                "hour": hour,
                "day_of_week": day,
                "month": month,
                "traffic": "Medium",
                "weather": "Clear",
                "is_holiday": 0,
                "festival_nearby": 0,
                "exam_season": 0,
                "exam_end_rush": 0
            })

future_df = pd.DataFrame(future_data)

future_df['season'] = future_df['month'].apply(
    lambda m: "Summer" if m in [3,4,5] else "Monsoon" if m in [6,7,8,9] else "Winter"
)

df_encoded = pd.get_dummies(future_df, columns=[
    'route','day_of_week','season','traffic','weather'
])

X_full = df_encoded.reindex(columns=feature_columns, fill_value=0)

future_df['predicted_passengers'] = model.predict(X_full).round().astype(int)

# use MAX instead of mean (fix)
df_output = (
    future_df.groupby(['date','route','hour'])['predicted_passengers']
    .max()
    .reset_index()
)

MAX_CAPACITY = 70

def schedule(p):
    if p <= 20:
        return 1, "Low Frequency"
    buses = (p + 69)//70
    return buses, "High Frequency"

df_output[['buses','frequency']] = df_output['predicted_passengers'].apply(
    lambda p: pd.Series(schedule(p))
)

df_output.to_csv("data/final_schedule_2026.csv", index=False)

print("✅ Fixed Smart Schedule Generated")
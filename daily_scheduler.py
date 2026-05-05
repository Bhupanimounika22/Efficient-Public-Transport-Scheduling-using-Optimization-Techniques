import pandas as pd
import joblib
from db import get_connection

MAX_CAPACITY = 70
MAX_SHIFTS_PER_DAY = 10   # 🔥 increased for testing

model = joblib.load("model/xgb_model.pkl")
feature_columns = joblib.load("model/feature_columns.pkl")


# -------------------------
# GET CREW (NO LEAVE FILTER TEMP)
# -------------------------
def get_available_crew():

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM drivers")
    drivers = cur.fetchall()

    cur.execute("SELECT * FROM conductors")
    conductors = cur.fetchall()

    conn.close()

    print("Drivers:", drivers)
    print("Conductors:", conductors)

    return drivers, conductors


# -------------------------
# GENERATE ONE DAY
# -------------------------
def generate_day_schedule(date, routes, hours):

    rows = []

    for route in routes:
        for hour in hours:
            rows.append({
                "date": date,
                "route": route,
                "hour": hour,
                "day_of_week": pd.to_datetime(date).day_name(),
                "month": pd.to_datetime(date).month,
                "traffic": "Medium",
                "weather": "Clear",
                "is_holiday": 0,
                "festival_nearby": 0,
                "exam_season": 0,
                "exam_end_rush": 0
            })

    df = pd.DataFrame(rows)

    df['season'] = df['month'].apply(
        lambda m: "Summer" if m in [3,4,5] else "Monsoon" if m in [6,7,8,9] else "Winter"
    )

    df_encoded = pd.get_dummies(df, columns=[
        'route','day_of_week','season','traffic','weather'
    ])

    X = df_encoded.reindex(columns=feature_columns, fill_value=0)

    df['predicted_passengers'] = model.predict(X).round().astype(int)

    df['buses'] = df['predicted_passengers'].apply(
        lambda p: 1 if p <= 20 else (p + 69)//70
    )

    return df


# -------------------------
# ASSIGN CREW
# -------------------------
def assign_crew(date, df):

    drivers, conductors = get_available_crew()

    if not drivers or not conductors:
        print("❌ No crew available!")
        return

    driver_count = {d['id']: 0 for d in drivers}
    conductor_count = {c['id']: 0 for c in conductors}

    conn = get_connection()
    cur = conn.cursor()

    print(f"\n🚀 Assigning crew for {date}")

    for _, row in df.iterrows():

        buses = int(row['buses'])
        print(f"Route {row['route']} Hour {row['hour']} → {buses} buses")

        for b in range(buses):

            # filter by shift limit
            free_drivers = [d for d in drivers if driver_count[d['id']] < MAX_SHIFTS_PER_DAY]
            free_conductors = [c for c in conductors if conductor_count[c['id']] < MAX_SHIFTS_PER_DAY]

            if not free_drivers or not free_conductors:
                print("⚠️ Not enough crew, leaving unassigned")
                driver_id = None
                conductor_id = None
            else:
                driver = min(free_drivers, key=lambda d: driver_count[d['id']])
                conductor = min(free_conductors, key=lambda c: conductor_count[c['id']])

                driver_id = driver['id']
                conductor_id = conductor['id']

                driver_count[driver_id] += 1
                conductor_count[conductor_id] += 1

                print(f"Assigned Driver {driver_id}, Conductor {conductor_id}")

            cur.execute("""
            INSERT INTO assignments (date,route,hour,bus_no,driver_id,conductor_id)
            VALUES (%s,%s,%s,%s,%s,%s)
            """, (date,row['route'],row['hour'],b+1,driver_id,conductor_id))

    conn.commit()
    conn.close()

    print("✅ Assignment complete")


# -------------------------
# RUN ONE DAY
# -------------------------
def run_day(date, routes, hours):

    df = generate_day_schedule(date, routes, hours)
    assign_crew(date, df)

    print(f"✅ Done for {date}")
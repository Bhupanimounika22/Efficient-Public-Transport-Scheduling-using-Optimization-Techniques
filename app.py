from flask import Flask, render_template, request, redirect, jsonify
import pandas as pd
from predictor import predict_passengers
from calendar_utils import get_calendar_data
from utils import get_weather, get_traffic, get_season, get_exam_features
from db import get_connection


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/predict", methods=["GET","POST"])
def predict():

    today = pd.Timestamp.now()
    weather = get_weather()
    holiday_flag, _, festival_name = get_calendar_data(today)

    if request.method == "POST":

        try:
            date = pd.to_datetime(request.form["date"])
            route = request.form["route"]
            hour = int(request.form["hour"])
        except:
            return "Invalid input"

        passengers, info = predict_passengers(date, route, hour, weather)

        buses = max(1, (passengers + 69)//70)
        served = min(passengers, buses * 70)
        waiting = max(0, passengers - served)

        # demand label
        if passengers > 150:
            demand = "High"
        elif passengers > 70:
            demand = "Medium"
        else:
            demand = "Low"

        return render_template("result.html",
                               passengers=passengers,
                               buses=buses,
                               served=served,
                               waiting=waiting,
                               demand=demand,
                               info=info)

    return render_template("predict.html",
                           weather=weather,
                           holiday="Yes" if holiday_flag else "No",
                           festival=festival_name if festival_name else "None")


@app.route("/get_info", methods=["POST"])
def get_info():

    data = request.json

    date = pd.to_datetime(data["date"])
    hour = int(data.get("hour", 9))

    day = date.day_name()
    month = date.month
    is_weekend = 1 if day in ["Saturday","Sunday"] else 0

    weather = get_weather()
    holiday_flag, _, festival_name = get_calendar_data(date)

    traffic = get_traffic(hour, day, holiday_flag, festival_name)
    exam_s, exam_e = get_exam_features(month)

    return jsonify({
        "weather": weather,
        "holiday": "Yes" if holiday_flag else "No",
        "festival": festival_name if festival_name else "None",
        "day": day,
        "month": month,
        "weekend": "Yes" if is_weekend else "No",
        "season": get_season(month),
        "traffic": traffic,
        "exam_season": exam_s,
        "exam_end": exam_e
    })


@app.route("/about")
def about():
    return render_template("about.html")
from db import get_connection
from daily_scheduler import run_day
import pandas as pd

# ADD DRIVER

# -------------------------------
# ADD DRIVER / CONDUCTOR
# -------------------------------
@app.route("/add_driver", methods=["GET", "POST"])
def add_driver():
    if request.method == "POST":
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO drivers (name,email,phone)
            VALUES (%s,%s,%s)
        """, (request.form['name'], request.form['email'], request.form['phone']))

        conn.commit()
        conn.close()

        return jsonify({"status": "added"})

    return render_template("add_driver.html")


@app.route("/get_drivers")
def get_drivers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM drivers")
    data = cur.fetchall()
    conn.close()
    return jsonify(data)


@app.route("/update_driver", methods=["POST"])
def update_driver():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE drivers
        SET name=%s, email=%s, phone=%s
        WHERE id=%s
    """, (
        request.form['name'],
        request.form['email'],
        request.form['phone'],
        request.form['id']
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "updated"})


@app.route("/delete_driver/<int:id>")
def delete_driver(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM drivers WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})


# =========================
# CONDUCTOR
# =========================

@app.route("/add_conductor", methods=["GET", "POST"])
def add_conductor():
    if request.method == "POST":
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO conductors (name,email,phone)
            VALUES (%s,%s,%s)
        """, (request.form['name'], request.form['email'], request.form['phone']))

        conn.commit()
        conn.close()

        return jsonify({"status": "added"})

    return render_template("add_conductor.html")


@app.route("/get_conductors")
def get_conductors():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM conductors")
    data = cur.fetchall()
    conn.close()
    return jsonify(data)


@app.route("/update_conductor", methods=["POST"])
def update_conductor():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE conductors
        SET name=%s, email=%s, phone=%s
        WHERE id=%s
    """, (
        request.form['name'],
        request.form['email'],
        request.form['phone'],
        request.form['id']
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "updated"})


@app.route("/delete_conductor/<int:id>")
def delete_conductor(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM conductors WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

@app.route("/run_scheduler", methods=["POST"])
def run_scheduler():

    from db import get_connection
    import pandas as pd
    from predictor import predict_passengers

    date_input = request.form["date"]
    date_obj = pd.to_datetime(date_input).normalize()
    date_str = date_obj.strftime("%Y-%m-%d")

    ROUTES = [
        "PNBS–BenzCircle–Autonagar",
        "PNBS–Gunadala–Gannavaram",
        "PNBS–Poranki–Penamaluru",
        "PNBS–Kanuru–Vuyyuru",
        "PNBS–Bhavanipuram–Ibrahimpatnam",
        "BenzCircle–Ramavarappadu–Gannavaram"
    ]

    # 🔥 FULL DAY (5 AM → 11 PM)
    HOURS = list(range(5, 24))   # 5 to 23

    BUS_CAPACITY = 70

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    print("Running scheduler for:", date_str)

    # -------------------------
    # CLEAN OLD DATA
    # -------------------------
    cur.execute("DELETE FROM assignments WHERE DATE(date)=%s", (date_str,))
    conn.commit()

    # -------------------------
    # GET CREW
    # -------------------------
    cur.execute("SELECT * FROM drivers")
    drivers = cur.fetchall()

    cur.execute("SELECT * FROM conductors")
    conductors = cur.fetchall()

    total_crews = min(len(drivers), len(conductors))

    if total_crews == 0:
        return "❌ No crew available"

    # -------------------------
    # LOOP HOURS
    # -------------------------
    for hour in HOURS:

        route_demand = []

        # 🔥 STEP 1: ML PREDICTION
        for route in ROUTES:
            passengers, _ = predict_passengers(date_obj, route, hour)

            buses_needed = max(1, (passengers + BUS_CAPACITY - 1) // BUS_CAPACITY)

            route_demand.append((route, passengers, buses_needed))

        # 🔥 STEP 2: SORT HIGH DEMAND FIRST
        route_demand.sort(key=lambda x: x[1], reverse=True)

        # -------------------------
        # 🔥 STEP 3: SMART CREW LIMIT
        # -------------------------
        available_crews = total_crews
        driver_index = 0
        conductor_index = 0

        for route, passengers, buses_needed in route_demand:

            if available_crews <= 0:
                break

            # 🔥 LIMIT buses based on available crew
            buses_to_assign = min(buses_needed, available_crews)

            for bus_no in range(1, buses_to_assign + 1):

                driver_id = drivers[driver_index]['id']
                conductor_id = conductors[conductor_index]['id']

                cur.execute("""
                    INSERT INTO assignments 
                    (date,route,hour,bus_no,driver_id,conductor_id,passengers)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (date_str, route, hour, bus_no, driver_id, conductor_id, passengers))

                driver_index += 1
                conductor_index += 1
                available_crews -= 1

                if driver_index >= len(drivers) or conductor_index >= len(conductors):
                    break

    conn.commit()
    conn.close()

    return "✅ Smart Adaptive Schedule Generated"
         
@app.route("/assignments")
def view_assignments():

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
    SELECT a.*, 
           d.name AS driver_name, 
           c.name AS conductor_name
    FROM assignments a
    LEFT JOIN drivers d ON a.driver_id = d.id
    LEFT JOIN conductors c ON a.conductor_id = c.id
    ORDER BY a.date, a.hour
    """)

    data = cur.fetchall()
    conn.close()

    return render_template("assignments.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)
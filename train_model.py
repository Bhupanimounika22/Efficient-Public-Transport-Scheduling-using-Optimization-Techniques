import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

# Load data
df = pd.read_csv("data/bus_demand_real_api_2025.csv")

df['date'] = pd.to_datetime(df['date'])
df['day'] = df['date'].dt.day
df['month'] = df['date'].dt.month

df_encoded = pd.get_dummies(df, columns=[
    'route','day_of_week','season','traffic','weather'
], drop_first=True)

y = df_encoded['passengers']
X = df_encoded.drop(['passengers','date'], axis=1)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = XGBRegressor(n_estimators=200, max_depth=8)
model.fit(X_train, y_train)

# SAVE
joblib.dump(model, "model/xgb_model.pkl")
joblib.dump(X.columns, "model/feature_columns.pkl")

print("✅ Model saved")
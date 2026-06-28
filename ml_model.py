# Machine Learning Occupancy Forecasting Model
import os
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
# Patch MySQLdb with pymysql for easy installation on Windows systems
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
import MySQLdb
def get_historical_data():
    try:
        db = MySQLdb.connect(
            host="localhost",
            user="root",
            passwd="pammysaini",
            db="smart_cafe_db"
        )
        cursor = db.cursor()
        cursor.execute("""
        SELECT 
            booking_date,
            DAYOFWEEK(booking_date) as day_id,
            MONTH(booking_date) as month_id,
            CASE 
                WHEN DAYOFWEEK(booking_date) IN (1,7) THEN 1
                ELSE 0
            END as is_weekend,
            AVG(
                CASE booking_slot
                    WHEN 'Morning 10-12' THEN 1
                    WHEN 'Afternoon 1-3' THEN 2
                    WHEN 'Evening 5-7' THEN 3
                    WHEN 'Night 8-10' THEN 4
                END
            ) as avg_slot,
            SUM(guests_count) as total_guests
        FROM bookings
        GROUP BY booking_date
        ORDER BY booking_date ASC
        """)
        data = cursor.fetchall()
        db.close()
        return data
    except Exception as e:
        print(f"Error fetching historical database records: {e}")
        return []
def train_demand_model():
    data = get_historical_data()
    if len(data) < 3:
        print("Not enough historical data (minimum 3 records required) to retrain Random Forest.")
        return False
        
    df = pd.DataFrame(data, columns=[
        'date',
        'day_of_week',
        'month',
        'is_weekend',
        'avg_slot',
        'total_guests'
    ])
    # Feature engineering before modeling
    df['festival'] = df['date'].apply(is_festival)
    df['previous_occupancy'] = df['total_guests'].shift(1)
    df['previous_occupancy'] = df['previous_occupancy'].fillna(df['total_guests'].mean())
    df['weather'] = 0   # Temporary placeholder
    X = df[[
        'day_of_week',
        'month',
        'is_weekend',
        'festival',
        'avg_slot',
        'previous_occupancy'
    ]]
    y = df['total_guests']
    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=10,
        random_state=42
    )
    model.fit(X, y)
    # Save model pkl locally
    with open('cafe_ml_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    print("Random Forest model successfully retrained on current booking history.")
    return True
def is_festival(date):
    festival_dates = [
        '2026-01-14',  # Makar Sankranti
        '2026-03-04',  # Holi
        '2026-11-08',  # Diwali
        '2026-12-25'   # Christmas
    ]
    return 1 if str(date) in festival_dates else 0
def predict_occupancy(
    day_code=6,
    month=6,
    weekend=0,
    festival=0,
    avg_slot=3,
    previous_occupancy=25
):
    if not os.path.exists('cafe_ml_model.pkl'):
        return 75
    try:
        with open('cafe_ml_model.pkl', 'rb') as f:
            model = pickle.load(f)
        input_data = [[
            day_code,
            month,
            weekend,
            festival,
            avg_slot,
            previous_occupancy
        ]]
        predicted = model.predict(input_data)[0]
        occupancy = int(predicted)
        return max(10, min(occupancy, 100))
    except Exception as e:
        print(f"Error predicting occupancy: {e}")
        return 75
if __name__ == "__main__":
    train_demand_model()

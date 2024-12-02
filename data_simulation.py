import sqlite3
import random
import time
from datetime import datetime

# Function to insert simulated data into the WeatherData table
def insert_simulated_data():
    conn = sqlite3.connect("weather_station.db")
    cursor = conn.cursor()

    # Generate random data for temperature, humidity, pressure, and air quality
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    temperature = round(random.uniform(15.0, 35.0), 2)  # Temperature in Celsius
    humidity = round(random.uniform(30.0, 80.0), 2)      # Humidity in percentage
    pressure = round(random.uniform(990.0, 1030.0), 2)   # Atmospheric pressure in hPa
    air_quality = random.randint(0, 500)                  # Air Quality Index (AQI)

    # Insert the simulated data into the WeatherData table
    cursor.execute("INSERT INTO WeatherData (timestamp, temperature, humidity, pressure, air_quality) VALUES (?, ?, ?, ?, ?)",
                   (timestamp, temperature, humidity, pressure, air_quality))
    conn.commit()
    conn.close()

# Main function to simulate data insertion every 5 seconds
def simulate_data():
    while True:
        insert_simulated_data()
        print("Simulated data inserted at", datetime.now())
        time.sleep(5)  # Simulate every 5 seconds

if __name__ == "__main__":
    simulate_data()

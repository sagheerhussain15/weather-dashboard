import sqlite3

# Create the SQLite database and WeatherData table
def create_database():
    conn = sqlite3.connect("weather_station.db")
    cursor = conn.cursor()

    # Create WeatherData table
    cursor.execute('''CREATE TABLE IF NOT EXISTS WeatherData (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        temperature REAL,
                        humidity REAL,
                        pressure REAL,
                        air_quality INTEGER)''')
    conn.commit()
    conn.close()
    print("Database and table created successfully!")

if __name__ == "__main__":
    create_database()

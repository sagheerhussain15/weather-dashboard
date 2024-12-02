from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
import time
import threading
import os
import requests
import base64
import matplotlib.pyplot as plt
import io
import schedule
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# User class
class User(UserMixin):
    def __init__(self, id, username, password_hash, email):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.email = email

# User loader
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2], user_data[3])  # Return User object
    return None

# Database connection
def get_db_connection():
    conn = sqlite3.connect('weather_station.db')
    conn.row_factory = sqlite3.Row  # Enable access to columns by name
    return conn

# Create tables if they don't exist
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # WeatherData table
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS WeatherData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            pressure REAL NOT NULL,
            air_quality INTEGER NOT NULL
        );
    ''')
    conn.commit()

    # Users table
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL
        );
    ''')
    conn.commit()
    conn.close()

# Simulate weather data
def simulate_weather_data():
    temperature = round(random.uniform(15, 35), 2)
    humidity = round(random.uniform(30, 80), 2)
    pressure = round(random.uniform(980, 1020), 2)
    air_quality = random.randint(0, 300)

    # Insert simulated data into the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO WeatherData (timestamp, temperature, humidity, pressure, air_quality)
                      VALUES (?, ?, ?, ?, ?)''',
                   (time.strftime('%Y-%m-%d %H:%M:%S'), temperature, humidity, pressure, air_quality))
    conn.commit()
    conn.close()

# Fetch live weather data from OpenWeatherMap API
def fetch_weather_data(city, country):
    api_key = os.getenv("API_KEY")  # Ensure to store the API key in the .env file
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={api_key}&units=metric"

    response = requests.get(url)
    data = response.json()

    if response.status_code == 200:
        temperature = data['main']['temp']
        humidity = data['main']['humidity']
        pressure = data['main']['pressure']
        description = data['weather'][0]['description']
        country_name = data['sys']['country']
        
        return {
            'temperature': temperature,
            'humidity': humidity,
            'pressure': pressure,
            'description': description,
            'country_name': country_name
        }
    else:
        return {
            'temperature': None,
            'humidity': None,
            'pressure': None,
            'description': 'Data not available',
            'country_name': 'N/A'
        }

# Schedule tasks to run every 10 seconds
schedule.every(10).seconds.do(simulate_weather_data)  # Use fetch_weather_data() for live API data

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.daemon = True
scheduler_thread.start()

# Generate weather graph
def generate_weather_graph():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, temperature, humidity FROM WeatherData ORDER BY timestamp DESC LIMIT 10')
    data = cursor.fetchall()
    conn.close()

    timestamps = [entry['timestamp'] for entry in data]
    temperatures = [entry['temperature'] for entry in data]
    humidities = [entry['humidity'] for entry in data]

    fig, ax = plt.subplots()
    ax.plot(timestamps, temperatures, label="Temperature", color='tab:red')
    ax.plot(timestamps, humidities, label="Humidity", color='tab:blue')
    
    ax.set_xlabel('Time')
    ax.set_ylabel('Value')
    ax.set_title('Temperature and Humidity Trends')
    ax.legend()

    img_stream = io.BytesIO()
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)

    img_base64 = base64.b64encode(img_stream.getvalue()).decode('utf8')
    
    return img_base64

# Route for login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Users WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data and check_password_hash(user_data[2], password):  # Check hashed password
            user = User(user_data[0], user_data[1], user_data[2], user_data[3])
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials. Please try again.")
    
    return render_template("login.html")

# Route for signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Users WHERE username = ?', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Username already exists. Please choose a different one.", "danger")
            return redirect(url_for("signup"))
        
        cursor.execute('INSERT INTO Users (username, email, password_hash) VALUES (?, ?, ?)',
                       (username, email, password_hash))
        conn.commit()
        conn.close()

        flash("Signup successful! Please log in.")
        return redirect(url_for('login'))
    
    return render_template("signup.html")

# Route for dashboard (only accessible when logged in)
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    # Default city and country for initial page load
    city = "London"
    country = "GB"

    if request.method == "POST":
        # Get city and country from the form
        city = request.form["city"]
        country = request.form["country"]

    # Fetch weather data for the city and country
    weather_data = fetch_weather_data(city, country)

    # Generate the weather graph
    weather_graph = generate_weather_graph()

    return render_template("dashboard.html", weather_data=weather_data, weather_graph=weather_graph)

# Route for logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# Route for home page
@app.route("/")
def home():
    return redirect(url_for("login"))

# Main entry point
if __name__ == "__main__":
    create_tables()  # Ensure tables are created on app startup
    app.run(debug=True)

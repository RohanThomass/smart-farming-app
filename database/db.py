import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def init_db():
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()

    # Updated to include email
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            temperature REAL,
            humidity REAL,
            soil_moisture REAL
        )
    ''')

    conn.commit()
    conn.close()

def insert_user(username, email, password):
    try:
        hashed_pwd = generate_password_hash(password)
        conn = sqlite3.connect('sensor.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, hashed_pwd))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def validate_user(username, password):
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    if result and check_password_hash(result[0], password):
        return True
    return False

def insert_sensor_data(temp, humidity, moisture):
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()
    c.execute('INSERT INTO sensor_data (temperature, humidity, soil_moisture) VALUES (?, ?, ?)', (temp, humidity, moisture))
    conn.commit()
    conn.close()

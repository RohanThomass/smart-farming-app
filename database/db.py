import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash





import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()

    # Create users table
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        role TEXT DEFAULT 'farmer'
    )
    ''')

    # Create sensor data table
    c.execute('''
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        temperature REAL,
        humidity REAL,
        soil_moisture REAL
    )
    ''')

    # Create locations table
    c.execute('''
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        latitude REAL,
        longitude REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create admin user if not exists
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        hashed_pwd = generate_password_hash('admin123')
        c.execute("INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                  ('admin', 'admin@example.com', hashed_pwd, 'admin'))

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
    c.execute("SELECT id, password, role FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()

    if user and check_password_hash(user[1], password):
        return (user[0], user[2])  # return user_id and role
    return None



def insert_sensor_data(temp, humidity, moisture):
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()
    c.execute('INSERT INTO sensor_data (temperature, humidity, soil_moisture) VALUES (?, ?, ?)', (temp, humidity, moisture))
    conn.commit()
    conn.close()

def update_user_profile(user_id, username, email):
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()
    c.execute("UPDATE users SET username = ?, email = ? WHERE id = ?", (username, email, user_id))
    conn.commit()
    conn.close()

def change_user_password(user_id, new_password_hashed):
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()
    c.execute("UPDATE users SET password = ? WHERE id = ?", (new_password_hashed, user_id))
    conn.commit()
    conn.close()
    
def require_admin():
    if session.get('role') != 'admin':
        return redirect('/')

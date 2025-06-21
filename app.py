from flask import Flask, render_template, request, redirect, session, jsonify
from database.db import init_db, insert_user, validate_user, insert_sensor_data
import random
import sqlite3
import csv
from flask import send_file
import os
import json

app = Flask(__name__)
app.secret_key = '123'

# Initialize database on app start
init_db()


@app.route('/')
def home():
    if 'user' in session:
        return render_template('index.html')
    return redirect('/login')
@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/download')
def download_csv():
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()
    c.execute('SELECT * FROM sensor_data ORDER BY timestamp DESC')
    data = c.fetchall()
    conn.close()

    with open('sensor_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Timestamp', 'Temperature', 'Humidity', 'Soil Moisture'])
        writer.writerows(data)

    return send_file('sensor_data.csv', as_attachment=True)

@app.route('/history')
def history():
    if 'user' not in session:
        return redirect('/login')
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()
    c.execute('SELECT * FROM sensor_data ORDER BY timestamp DESC')
    data = c.fetchall()
    conn.close()
    return render_template('history.html', data=data)

@app.route('/connect')
def connect_page():
    
    return render_template("connect.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if validate_user(uname, pwd):
            session['user'] = uname
            return redirect('/')
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        uname = request.form['username']
        email = request.form['email']
        pwd = request.form['password']
        if insert_user(uname, email, pwd):
            return redirect('/login')
        return 'User already exists'
    return render_template('signup.html')




@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    message = ''
    if request.method == 'POST':
        uname = request.form['username']
        new_pwd = request.form['new_password']

        conn = sqlite3.connect('sensor.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (uname,))
        user = c.fetchone()
        if user:
            from werkzeug.security import generate_password_hash
            hashed_pwd = generate_password_hash(new_pwd)
            c.execute('UPDATE users SET password = ? WHERE username = ?', (hashed_pwd, uname))
            conn.commit()
            conn.close()
            return redirect('/login')
        else:
            message = 'User not found'
            conn.close()
    return render_template('forgot_password.html', message=message)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

@app.route('/save-location', methods=['POST'])
def save_location():
    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')

    if lat and lon:
        conn = sqlite3.connect('sensor.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS location_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        latitude REAL,
                        longitude REAL
                    )''')
        c.execute('INSERT INTO location_log (latitude, longitude) VALUES (?, ?)', (lat, lon))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Location saved"}), 200
    return jsonify({"status": "error", "message": "Invalid data"}), 400

@app.route('/feedback', methods=["GET", "POST"])
@app.route("/feedback", methods=["GET", "POST"])
def feedback_page():
    submitted = False
    if request.method == "POST":
        feedback_text = request.form["message"]
        # TODO: Save feedback_text to DB or notify
        submitted = True

    faqs = [
        {"q": "How to reset my device?", "a": "Go to My Device → Reset → Confirm."},
        {"q": "What sensors are supported?", "a": "Soil, temperature, humidity, and pH sensors."},
        {"q": "Is this app free?", "a": "Yes, all features are free for farmers."}
    ]

    return render_template("feedback.html", submitted=submitted, faqs=faqs)






@app.route('/devices')
def my_devices():
    connected_devices = [
        {"name": "Soil Sensor", "status": "Active"},
        {"name": "Temp Sensor", "status": "Inactive"}
    ]
    return render_template("devices.html", devices=connected_devices)

@app.route('/data')
def data():
    if 'user' not in session:
        return jsonify({'error': 'unauthorized'}), 403

    # Simulate sensor values
    temp = round(random.uniform(20, 35), 2)
    humidity = round(random.uniform(40, 80), 2)
    moisture = round(random.uniform(300, 800), 2)

    # Store data in DB
    insert_sensor_data(temp, humidity, moisture)

    return jsonify({
        'temperature': temp,
        'humidity': humidity,
        'soil_moisture': moisture
    })

if __name__ == '__main__':
    app.run(debug=True)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
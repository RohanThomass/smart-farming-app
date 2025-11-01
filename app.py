from flask import Flask, render_template, request, redirect, session, jsonify, send_file
from database.db import init_db, insert_user, validate_user, insert_sensor_data, update_user_profile, change_user_password
from genai_service import generate_farming_insight
from flask_mail import Mail
from dotenv import load_dotenv
import random, sqlite3, csv, os, json
from werkzeug.security import generate_password_hash

# Load environment variables early
load_dotenv()

app = Flask(__name__)

# ✅ Secret Key (make sure .env has SECRET_KEY=mystrongsecret)
app.secret_key = os.getenv("SECRET_KEY", "supersecret123")

# ✅ Mail Configuration
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD')
)

mail = Mail(app)

# Initialize database
init_db()


@app.route('/')
def home():
    if 'user_id' in session:
        conn = sqlite3.connect('sensor.db')
        c = conn.cursor()
        c.execute("SELECT username, email, profile_pic FROM users WHERE id = ?", (session['user_id'],))
        user = c.fetchone()
        conn.close()

        if user:
            return render_template(
                'index.html',
                user_name=user[0],
                user_email=user[1],
                profile_pic=user[2] if user[2] else 'default.png'  # fallback to default picture
            )
        else:
            return redirect('/login')
    else:
        return redirect('/login')

    
@app.route('/ask-ai', methods=['POST'])
def ask_ai():
    if 'user' not in session:
        return jsonify({'error': 'unauthorized'}), 403

    data = request.get_json()
    question = data.get('question')

    # fetch latest sensor readings
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()
    c.execute("SELECT temperature, humidity, soil_moisture FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
    latest = c.fetchone()
    conn.close()

    if not latest:
        return jsonify({'error': 'No sensor data found'}), 404

    sensor_data = {'temperature': latest[0], 'humidity': latest[1], 'soil_moisture': latest[2]}
    answer = generate_farming_insight(sensor_data, question)

    return jsonify({'answer': answer})

@app.before_request
def before_request():
    if not request.is_secure and app.config.get("ENV") == "production":
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)



@app.route('/about')
def about():
    company_info = {
        "name": "AgriSmart Solutions",
        "description": "AgriSmart is dedicated to transforming traditional farming through advanced digital technologies. We empower farmers with tools for real-time monitoring, data-driven decisions, and sustainable agriculture.",
        "founded": "2024",
        "location": "Nellore, Andhra Pradesh, India"
    }
    founder_info = {
        "name": "Rohan Battepati",
        "bio": "Rohan is a passionate tech innovator and agricultural enthusiast with a vision to digitize Indian farming. With a background in computer applications and a deep understanding of rural challenges, he leads AgriSmart to deliver impactful solutions."
    }
    return render_template('about.html', company=company_info, founder=founder_info)

@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    # On form submission
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']

        # Handle profile picture upload
        file = request.files.get('profile_pic')
        filename = None
        if file and file.filename != '':
            filename = f"user_{user_id}_" + file.filename
            upload_path = os.path.join('static', 'uploads', filename)
            file.save(upload_path)
        else:
            # Fetch existing profile pic if no new upload
            conn = sqlite3.connect('sensor.db')
            c = conn.cursor()
            c.execute("SELECT profile_pic FROM users WHERE id = ?", (user_id,))
            filename = c.fetchone()[0]
            conn.close()

        # Update in DB
        conn = sqlite3.connect('sensor.db')
        c = conn.cursor()
        c.execute("UPDATE users SET username = ?, email = ?, profile_pic = ? WHERE id = ?", (username, email, filename, user_id))
        conn.commit()
        conn.close()

        return redirect('/')

    # GET request - show profile form
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()
    c.execute("SELECT username, email, profile_pic FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()

    if user:
        return render_template('edit_profile.html', user_name=user[0], user_email=user[1], profile_pic=user[2])

    else:
        return redirect('/login')  # fallback if user not found



@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        new_password = request.form['new_password']
        hashed_pwd = generate_password_hash(new_password)

        conn = sqlite3.connect('sensor.db')
        c = conn.cursor()
        c.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_pwd, session['user_id']))
        conn.commit()
        conn.close()
        return redirect('/')

    return render_template('change_password.html')

@app.route('/welcome')
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

        user_id = validate_user(uname, pwd)

        if user_id:
            # If validate_user returns a tuple like (id,), unpack it
            if isinstance(user_id, tuple):
                user_id = user_id[0]

            session['user'] = uname
            session['user_id'] = user_id

            return redirect('/')

        return 'Invalid credentials'

    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])

def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if entered_otp == session.get('otp'):
            session['user_id'] = session.pop('temp_user')
            session.pop('otp', None)
            return redirect('/')
        else:
            return 'Incorrect OTP. Please try again.'

    return render_template('verify_otp.html')



@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return "Unauthorized", 403

    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()
    c.execute("SELECT id, username, email, role FROM users")
    users = c.fetchall()
    conn.close()
    return render_template("admin.html", users=users)


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
    session.pop('user_id', None)
    return redirect('/login')

@app.route('/save-location', methods=['POST'])
def save_location():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    user_id = session.get('user_id')

    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()
    c.execute("INSERT INTO locations (user_id, latitude, longitude) VALUES (?, ?, ?)", (user_id, latitude, longitude))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

@app.route("/feedback", methods=["GET", "POST"])
def feedback_page():
    submitted = False
    if request.method == "POST":
        feedback_text = request.form["message"]
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

    temp = round(random.uniform(20, 35), 2)
    humidity = round(random.uniform(40, 80), 2)
    moisture = round(random.uniform(300, 800), 2)

    insert_sensor_data(temp, humidity, moisture)

    return jsonify({
        'temperature': temp,
        'humidity': humidity,
        'soil_moisture': moisture
    })

@app.route('/market')
def market():
    return redirect("https://enam.gov.in/web/dashboard/live_price")

@app.route('/dashboard')
def dashboard():
    # Query data from DB
    return render_template('dashboard.html', data=data)

@app.route('/recommend')
def recommend():
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()
    c.execute("SELECT temperature, humidity, moisture FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
    latest = c.fetchone()
    conn.close()

    crop = "Wheat"
    if latest:
        temp, hum, mois = latest
        if temp > 30 and mois < 500:
            crop = "Millet"
        elif hum > 70:
            crop = "Rice"
        elif mois > 700:
            crop = "Sugarcane"
        elif 20 <= temp <= 30 and 500 <= mois <= 700:
            crop = "Wheat"
    return render_template("recommend.html", crop=crop, temp=temp, hum=hum, mois=mois)

@app.route('/data')
def get_sensor_data():
    if 'user' not in session:
        return jsonify({'error': 'unauthorized'}), 403

    temp = round(random.uniform(20, 35), 2)
    humidity = round(random.uniform(40, 80), 2)
    moisture = round(random.uniform(300, 800), 2)

    insert_sensor_data(temp, humidity, moisture)

    alerts = []
    if temp > 33:
        alerts.append("⚠️ High Temperature")
    if moisture < 400:
        alerts.append("⚠️ Soil too dry")

    return jsonify({
        'temperature': temp,
        'humidity': humidity,
        'soil_moisture': moisture,
        'alerts': alerts
    })


@app.route('/ai')
def ai_insights():
    insights = [
        {"sensor": "Temperature", "info": "Helps monitor heat stress and optimize irrigation."},
        {"sensor": "Humidity", "info": "Affects plant transpiration and disease risk."},
        {"sensor": "Soil Moisture", "info": "Ensures correct watering levels for root health."},
    ]
    return render_template("ai.html", insights=insights)

@app.route('/analytics')
def analytics():
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE id = ?", (session['user_id'],))
    user = c.fetchone()

    c.execute("SELECT temperature, humidity, soil_moisture FROM sensor_data")

    data = c.fetchall()
    conn.close()

    if not data:
        return render_template("analytics.html", no_data=True, user_name=user[0])

    temps = [row[0] for row in data]
    hums = [row[1] for row in data]
    moistures = [row[2] for row in data]  # if soil_moisture is at index 2



    analytics = {
        "avg_temp": round(sum(temps) / len(temps), 2),
        "max_temp": max(temps),
        "min_temp": min(temps),
        "avg_hum": round(sum(hums) / len(hums), 2),
        "max_hum": max(hums),
        "min_hum": min(hums),
        "avg_moist": round(sum(moistures) / len(moistures), 2),
        "max_moist": max(moistures),
        "min_moist": min(moistures)
    }

    return render_template("analytics.html", analytics=analytics, chart_data=data, user_name=user[0])

@app.route('/sensors')
def sensor_dashboard():
    dashboards = [
        {"title": "Soil Sensor Dashboard", "image": "soil_sample.png"},
        {"title": "Temperature Sensor Dashboard", "image": "temp_sample.png"},
        {"title": "Humidity Sensor Dashboard", "image": "humidity_sample.png"},
    ]
    return render_template("sensors.html", dashboards=dashboards)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

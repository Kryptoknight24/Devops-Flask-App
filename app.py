import os
import base64
import json
import pymysql
from flask import Flask, render_template, request, redirect
from clerk_backend_api import Clerk

app = Flask(__name__)

# Initialize Clerk 
CLERK_SECRET_KEY = os.environ.get('CLERK_SECRET_KEY')
clerk = Clerk(bearer_auth=CLERK_SECRET_KEY)

def get_db_connection():
    return pymysql.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user='root',
        password='rootpassword',
        database='myappdb',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_clerk_user_id():
    """Extract clerk_user_id from the __session JWT cookie."""
    session_token = request.cookies.get('__session')
    if not session_token:
        return None
    try:
        parts = session_token.split('.')
        if len(parts) != 3:
            return None
        payload_b64 = parts[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_json = base64.b64decode(payload_b64).decode('utf-8')
        payload = json.loads(payload_json)
        return payload.get('sub')
    except Exception:
        return None

# --- 1. DATABASE SETUP ---
@app.route('/init-db')
def init_db():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS players")
            cursor.execute("""
                CREATE TABLE players (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    clerk_id VARCHAR(255) UNIQUE NOT NULL,
                    player_name VARCHAR(255),
                    age INT,
                    weight FLOAT,
                    height FLOAT,
                    level INT DEFAULT 0,
                    hp INT DEFAULT 100,
                    xp INT DEFAULT 0,
                    str_stat INT DEFAULT 0,
                    agi_stat INT DEFAULT 0,
                    end_stat INT DEFAULT 0,
                    vit_stat INT DEFAULT 0,
                    int_stat INT DEFAULT 0,
                    mana_crystals INT DEFAULT 0
                )
            """)
        connection.commit()
        return "Database initialized!"
    finally:
        connection.close()

# --- 2. FRONT DOOR ---
@app.route('/')
def index():
    return render_template('index.html')

# --- 3. PLAYER PROFILE SETUP ---
@app.route('/setup', methods=['GET', 'POST'])
def setup():
    clerk_user_id = get_clerk_user_id()
    if not clerk_user_id:
        return redirect('/')

    if request.method == 'POST':
        player_name = request.form.get('player_name', '').strip()
        age = request.form.get('age', 0, type=int)
        weight = request.form.get('weight', 0, type=float)
        height = request.form.get('height', 0, type=float)

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE players 
                    SET player_name = %s, age = %s, weight = %s, height = %s
                    WHERE clerk_id = %s
                """, (player_name, age, weight, height, clerk_user_id))
            connection.commit()
        finally:
            connection.close()

        return redirect('/status')

    return render_template('profile_setup.html')

# --- 4. SECURE STATUS WINDOW ---
@app.route('/status')
def status():
    clerk_user_id = get_clerk_user_id()
    if not clerk_user_id:
        return "<h3>CRITICAL: No __session cookie found by Flask!</h3>"

    try:
        # Enter the Database
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Check if player exists
                cursor.execute("SELECT * FROM players WHERE clerk_id = %s", (clerk_user_id,))
                player_data = cursor.fetchone()
                
                # If new player, create record and redirect to setup
                if not player_data:
                    cursor.execute("INSERT INTO players (clerk_id) VALUES (%s)", (clerk_user_id,))
                    connection.commit()
                    return redirect('/setup')

                # If player hasn't set up their profile yet, redirect to setup
                if not player_data.get('player_name'):
                    return redirect('/setup')

                # Render the holographic stats 
                return render_template('status.html', player=player_data)
        finally:
            connection.close()

    except Exception as e:
        return f"<h3>BACKEND AUTH ERROR:</h3><p>{str(e)}</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

    
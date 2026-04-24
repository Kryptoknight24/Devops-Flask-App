import os
from flask import Flask, render_template, request, redirect
import pymysql
from clerk_backend_api import Clerk

app = Flask(__name__)

# Initialize Clerk with the Docker environment variable
CLERK_SECRET_KEY = os.environ.get('CLERK_SECRET_KEY')
clerk = Clerk(bearer_auth=CLERK_SECRET_KEY)

def get_db_connection():
    return pymysql.connect(
        host='mysql-db',
        user='root',
        password='rootpassword',
        database='myappdb',
        cursorclass=pymysql.cursors.DictCursor
    )

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
                    level INT DEFAULT 1,
                    hp INT DEFAULT 100,
                    xp INT DEFAULT 0,
                    str_stat INT DEFAULT 10,
                    agi_stat INT DEFAULT 10,
                    end_stat INT DEFAULT 10,
                    vit_stat INT DEFAULT 10,
                    int_stat INT DEFAULT 10,
                    mana_crystals INT DEFAULT 0
                )
            """)
        connection.commit()
        return "Database initialized! Go to the homepage (/) to log in."
    finally:
        connection.close()

# --- 2. FRONT DOOR ---
@app.route('/')
def home():
    return render_template('index.html')

# --- 3. SECURE STATUS WINDOW ---
@app.route('/status')
def status():
    # 1. Look for the secure cookie
    session_token = request.cookies.get('__session')
    if not session_token:
        return redirect('/')

    try:
        # 2. Verify the token is real
        client_state = clerk.clients.verify_token(session_token)
        clerk_user_id = client_state.sub 

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 3. Check if player exists
                cursor.execute("SELECT * FROM players WHERE clerk_id = %s", (clerk_user_id,))
                player_data = cursor.fetchone()
                
                # 4. If new player, build profile
                if not player_data:
                    cursor.execute("INSERT INTO players (clerk_id) VALUES (%s)", (clerk_user_id,))
                    connection.commit()
                    cursor.execute("SELECT * FROM players WHERE clerk_id = %s", (clerk_user_id,))
                    player_data = cursor.fetchone()

                # 5. Render stats (Make sure you still have templates/status.html!)
                return render_template('status.html', player=player_data)
        finally:
            connection.close()

    except Exception as e:
        print(f"Auth Error: {e}")
        return redirect('/')

if __name__ == '__main__':
    # Flask listens internally; Caddy handles the outside world
    app.run(host='0.0.0.0', port=5000)
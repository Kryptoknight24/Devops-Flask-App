import os
from flask import Flask, render_template, request, redirect
import pymysql
from clerk_backend_api import Clerk

app = Flask(__name__)

# --- CLERK SETUP ---
# Grabs the secret key we put in your docker-compose.yml
CLERK_SECRET_KEY = os.environ.get('CLERK_SECRET_KEY')
clerk = Clerk(bearer_auth=CLERK_SECRET_KEY)

# --- DATABASE CONNECTION HELPER ---
def get_db_connection():
    return pymysql.connect(
        host='mysql-db', 
        user='root',
        password='rootpassword',
        database='myappdb',
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5  # <--- ADD THIS LINE
    )

# --- 1. THE DATABASE GENERATOR (This fixes your /init-db issue!) ---
@app.route('/init-db')
def init_db():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Creates the table using Clerk IDs to identify players
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
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
        return "SUCCESS: The System Database is initialized! Go to the home page (/) to log in."
    except Exception as e:
        return f"Database Initialization Failed: {e}"
    finally:
        if 'connection' in locals() and connection:
            connection.close()

# --- 2. MAIN DATABASE CONNECTION / LOGIN ROUTE ---
@app.route('/')
def home():
    # This renders the Clerk login widget from templates/index.html
    return render_template('index.html')

# --- 3. RPG ENGINE STATUS ROUTE ---
@app.route('/status')
def status():
    # Check for the Clerk cookie
    session_token = request.cookies.get('__session')
    
    if not session_token:
        # No cookie = not logged in. Kick them to the front door.
        return redirect('/')

    try:
        # Verify the cookie with Clerk
        client_state = clerk.clients.verify_token(session_token)
        clerk_user_id = client_state.sub 

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Check if the player exists in your database
                cursor.execute("SELECT * FROM players WHERE clerk_id = %s", (clerk_user_id,))
                player_data = cursor.fetchone()
                
                # If this is a brand new player, build their profile
                if not player_data:
                    cursor.execute("INSERT INTO players (clerk_id) VALUES (%s)", (clerk_user_id,))
                    connection.commit()
                    cursor.execute("SELECT * FROM players WHERE clerk_id = %s", (clerk_user_id,))
                    player_data = cursor.fetchone()

                # Render the holographic UI with real data
                return render_template('status.html', player=player_data)
        finally:
            connection.close()

    except Exception as e:
        print(f"Auth Error: {e}")
        return redirect('/')

# --- SERVER STARTUP ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
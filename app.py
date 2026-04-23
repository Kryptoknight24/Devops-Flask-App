import os
from flask import Flask, render_template, request, redirect
import pymysql
from clerk_backend_api import Clerk

app = Flask(__name__)

# --- CLERK INITIALIZATION ---
# Fetch the secret key injected by Docker Compose
CLERK_SECRET_KEY = os.environ.get('CLERK_SECRET_KEY')
clerk = Clerk(bearer_auth=CLERK_SECRET_KEY)

# --- DATABASE HELPER ---
def get_db_connection():
    return pymysql.connect(
        host='mysql-db',
        user='root',
        password='rootpassword',
        database='myappdb',
        cursorclass=pymysql.cursors.DictCursor
    )

# --- 1. THE DATABASE BUILDER ---
@app.route('/init-db')
def init_db():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # We use clerk_id as the unique identifier for each player
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
        return "System Database Initialized for Clerk Auth! Go to the home page (/) to log in."
    except Exception as e:
        return f"Initialization Failed: {e}"
    finally:
        connection.close()

# --- 2. THE FRONT DOOR (LOGIN SCREEN) ---
@app.route('/')
def home():
    # This renders the Clerk login widget from index.html
    return render_template('index.html')

# --- 3. SECURE RPG ENGINE STATUS ROUTE ---
@app.route('/status')
def status():
    # Step A: Grab the session cookie Clerk placed in the browser
    session_token = request.cookies.get('__session')
    
    # Step B: If no cookie exists, kick them back to the login screen
    if not session_token:
        return redirect('/')

    try:
        # Step C: Ask Clerk to verify the token is legitimate
        client_state = clerk.clients.verify_token(session_token)
        clerk_user_id = client_state.sub 

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Step D: Check if this player already exists in our database
                cursor.execute("SELECT * FROM players WHERE clerk_id = %s", (clerk_user_id,))
                player_data = cursor.fetchone()
                
                # Step E: If they don't exist, register them as a Level 1 Player
                if not player_data:
                    cursor.execute("INSERT INTO players (clerk_id) VALUES (%s)", (clerk_user_id,))
                    connection.commit()
                    
                    # Fetch their newly created stats
                    cursor.execute("SELECT * FROM players WHERE clerk_id = %s", (clerk_user_id,))
                    player_data = cursor.fetchone()

                # Step F: Render the UI with their actual live RPG stats!
                return render_template('status.html', player=player_data)
        finally:
            connection.close()

    except Exception as e:
        print(f"Auth Error: {e}")
        # If the token is invalid or expired, redirect to login
        return redirect('/')

# --- SERVER STARTUP ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
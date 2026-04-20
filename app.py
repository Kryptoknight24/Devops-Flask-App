from flask import Flask, render_template
import pymysql

app = Flask(__name__)

# --- MAIN DATABASE CONNECTION ROUTE ---
@app.route('/')
def home():
    try:
        connection = None
        # We try to connect to the database
        connection = pymysql.connect(
            host='mysql-db', 
            user='root',
            password='rootpassword',
            database='myappdb'
        )
        return "Hello! The Flask App is running AND successfully connected to the MySQL Database!"
    except Exception as e:
        return f"Hello! The web app is running, but we are still waiting on the database: {e}"
    finally:
        if connection:
            try:
                connection.close()
            except Exception:
                # ignore errors when closing the connection
                pass

# --- RPG ENGINE STATUS ROUTE ---
@app.route('/status')
def status():
    # This renders the holographic UI
    return render_template('status.html')

# --- SERVER STARTUP ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
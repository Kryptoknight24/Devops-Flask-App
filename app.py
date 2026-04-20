from flask import Flask
import pymysql

app = Flask(__name__)

@app.route('/')
def home():
    try:
        connection = None  # ADD THIS LINE
        # We try to connect to the database
        connection = pymysql.connect(
            host='mysql-db', # This name matches the Docker Compose file!
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

    from flask import Flask, render_template

app = Flask(__name__)

# ... your existing database connection code ...

@app.route('/status')
def status():
    # Later, we will query MySQL here to pass your actual live stats to the HTML!
    return render_template('status.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
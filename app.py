from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import subprocess
import os
from threading import Thread
import time
import sys
import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import schedule

app = Flask(__name__)
CORS(app)
username_list = []
temperatures = []
app_start_time = time.time()

# PostgreSQL connection parameters
db_params = {
    'host': 'localhost',
    'port': '5432',
    'user': 'postgres',
    'password': 'JustFlyItDatabase123',
    'database': 'postgres',
}

def get_usernames():
    try:
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        cursor.execute("SELECT usernames FROM login_details;")
        usernames = cursor.fetchall()

        return [username[0] for username in usernames]

    except psycopg2.Error as error:
        print("Database Not Online/Database Error")
        return []

    finally:
        if connection:
            cursor.close()
            connection.close()

def periodic_database_update():
    global username_list
    while True:
        username_list = get_usernames()
        time.sleep(5)

def backup_database():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_file = f'backup_{timestamp}.sql'

    # Set PGPASSWORD environment variable
    os.environ['PGPASSWORD'] = db_params['password']

    pg_dump_cmd = [
        'pg_dump',
        '--host', db_params['host'],
        '--port', db_params['port'],
        '--username', db_params['user'],
        '--dbname', db_params['database'],
        '--file', backup_file,
        '--no-password',  # Disable password prompts
    ]

    subprocess.run(pg_dump_cmd)

    # Clear the PGPASSWORD environment variable
    del os.environ['PGPASSWORD']

    return backup_file

def send_email_with_attachment(file_path):
    sender_email = "automatedtesting76@gmail.com"
    sender_password = "xmkj qkxl shwd fnno"
    recipient_email = "Haashir150@gmail.com"

    subject = f"{datetime.now().date()} | JFIApp Database Logs"
    body = "Please find the file attached."

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    with open(file_path, "rb") as attachment:
        attachment_content = attachment.read()
        part = MIMEText(attachment_content.decode('utf-8'), "base64")
        part.add_header("Content-Disposition", f"attachment; filename=backup.sql")
        message.attach(part)

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())

    print("Email sent successfully!")

def backup_and_send_email():
    backup_file_path = backup_database()
    send_email_with_attachment(backup_file_path)

# Schedule the backup_and_send_email function to run every two weeks
schedule.every(2).weeks.do(backup_and_send_email)
# Start the threads
database_update_thread = Thread(target=periodic_database_update)
database_update_thread.start()

@app.route("/")
def home():
    return render_template("home.html")

@app.route('/uptime')
def get_uptime():
    current_time = time.time()
    uptime_seconds = current_time - app_start_time
    return jsonify({'uptime': int(uptime_seconds)})

# Route to display database information (admin page)
@app.route('/database')
def view_database():
    try:
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Get table names
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        table_names = cursor.fetchall()

        # Get data from each table
        data = {}
        for table_name in table_names:
            cursor.execute(f"SELECT * FROM {table_name[0]};")

            # Fetch column names
            column_names = [desc[0] for desc in cursor.description]

            # Fetch data
            table_data = [dict(zip(column_names, row)) for row in cursor.fetchall()]

            data[table_name[0]] = table_data

        return render_template('database.html', tables=data)

    except psycopg2.Error as error:
        return f"Database Error: {error}"

    finally:
        if connection:
            cursor.close()
            connection.close()

if __name__ == '__main__':
    host_ip = '192.168.0.106'
    port_number = 80

    app.run(host=host_ip, port=port_number, debug=True)

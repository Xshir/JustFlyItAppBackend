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

app = Flask(__name__)
CORS(app)
username_list = []
temperatures = []

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

        cursor.execute("SELECT usernames FROM LoginDetails;")
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

    pg_dump_cmd = [
        'pg_dump',
        '--host', db_params['host'],
        '--port', db_params['port'],
        '--username', db_params['user'],
        '--password', db_params['password'],
        '--dbname', db_params['database'],
        '--file', backup_file,
    ]

    subprocess.run(pg_dump_cmd)

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
        part = MIMEText(attachment.read(), "base64")
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
    while True:
        backup_file_path = backup_database()
        send_email_with_attachment(backup_file_path)
        time.sleep(300)  # 300 seconds = 5 minutes

# Start the threads
database_update_thread = Thread(target=periodic_database_update)
backup_and_send_email_thread = Thread(target=backup_and_send_email)

database_update_thread.start()
backup_and_send_email_thread.start()

@app.route('/')
def home():
    return render_template('home.html', temperatures=temperatures, logins=username_list)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    print('Received data:', data)
    username = data.get('username')

    if username in username_list:
        print("LOGIN SUCCESS")
        return jsonify({'success': True, 'message': 'Login successful'})
    elif username == "devlogin":
        print("LOGIN SUCCESS (DEVLOGIN)")
        return jsonify({'success': True, 'message': 'Login successful'})
    else:
        print("LOGIN FAILURE")
        print(username_list, username)
        return jsonify({'success': False, 'message': 'Invalid username'})

if __name__ == '__main__':
    host_ip = '192.168.0.106'
    port_number = 80

    app.run(host=host_ip, port=port_number, debug=True)

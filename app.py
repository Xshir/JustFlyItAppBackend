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
import schedule, base64

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

def get_usernames_full_names_pair():
    try:
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        cursor.execute("SELECT usernames, full_names FROM login_details;")
        usernames = cursor.fetchall()

        return {username[0]: username[1] for username in usernames}

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



@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    print('Received data:', data)
    username = data.get('username')

    if username in username_list:
        # Assuming is_staff is retrieved from the database
        is_staff = check_is_staff(username)
        
        print("LOGIN SUCCESS")
        return jsonify({'success': True, 'message': 'Login successful', 'is_staff': is_staff})
    elif username == "devlogin":
        print("LOGIN SUCCESS (DEVLOGIN)")
        return jsonify({'success': True, 'message': 'Login successful', 'is_staff': True})  # Assuming devlogin is staff
    else:
        print("LOGIN FAILURE")
        print(username_list, username)
        return jsonify({'success': False, 'message': 'Invalid username'})

def check_is_staff(username):
    try:
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        cursor.execute("SELECT is_staff FROM login_details WHERE username = %s;", (username,))
        is_staff = cursor.fetchone()

        return is_staff[0] if is_staff else False  # Assuming is_staff is a boolean column

    except psycopg2.Error as error:
        print("Database Error:", error)
        return False

    finally:
        if connection:
            cursor.close()
            connection.close()


    

    
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




@app.route('/trainers_profile_data')
def get_trainers_profile_data():
    try:
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Get data from trainers_profile_data table
        cursor.execute("SELECT * FROM trainers_profile_data;")

        # Fetch column names
        column_names = [desc[0] for desc in cursor.description]

        # Fetch data
        table_data = []
        for row in cursor.fetchall():
            row_dict = dict(zip(column_names, row))

            # Convert boolean values to strings
            for key, value in row_dict.items():
                if isinstance(value, bool):
                    row_dict[key] = str(value)

            # Extract and convert profile picture to base64-encoded string
            if 'profile_picture' in row_dict and row_dict['profile_picture'] is not None:
                profile_picture_bytea = bytes(row_dict['profile_picture'])  # Convert to bytes
                profile_picture_base64 = base64.b64encode(profile_picture_bytea).decode('utf-8')
                row_dict['profile_picture'] = f"data:image/jpeg;base64,{profile_picture_base64}"

            table_data.append(row_dict)

        return jsonify({'trainers_profile_data': table_data})

    except psycopg2.Error as error:
        return jsonify({'error': f"Database Error: {error}"}), 500

    finally:
        if connection:
            cursor.close()
            connection.close()

if __name__ == '__main__':
    host_ip = '192.168.0.106'
    port_number = 80

    app.run(host=host_ip, port=port_number, debug=True)

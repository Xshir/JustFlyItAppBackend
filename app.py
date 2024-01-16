from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import subprocess
import os
from threading import Thread
import time
import sys
import psycopg2

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


database_update_thread = Thread(target=periodic_database_update)
database_update_thread.start()

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

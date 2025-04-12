import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_mysqldb import MySQL
import time
import boto3
from botocore.exceptions import ClientError
app = Flask(__name__)

def get_parameter(name, with_decryption=True):
    ssm = boto3.client('ssm', region_name='us-east-1')
    try:
        response = ssm.get_parameter(Name=name, WithDecryption=with_decryption)
        return response['Parameter']['Value']
    except ClientError as e:
        print(f"Error fetching {name}: {e}")
        return None

app.config['MYSQL_HOST'] = get_parameter('/myapp/db/host') or 'localhost'
app.config['MYSQL_USER'] = get_parameter('/myapp/db/user') or 'default_user'
app.config['MYSQL_PASSWORD'] = get_parameter('/myapp/db/password') or 'default_password'
app.config['MYSQL_DB'] = get_parameter('/myapp/db/name') or 'default_db'

# Initialize MySQL
mysql = MySQL(app)

def init_db():
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            message TEXT
        );
        ''')
        mysql.connection.commit()  
        cur.close()

@app.route('/')
def hello():
    cur = mysql.connection.cursor()
    cur.execute('SELECT message FROM messages')
    messages = cur.fetchall()
    cur.close()
    return render_template('index.html', messages=messages)

@app.route('/submit', methods=['POST'])
def submit():
    new_message = request.form.get('new_message')
    cur = mysql.connection.cursor()
    cur.execute('INSERT INTO messages (message) VALUES (%s)', [new_message])
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': new_message})

if __name__ == '__main__':
    time.sleep(10)
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)


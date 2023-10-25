from flask import Flask, render_template, request, redirect, make_response, session, flash
import hashlib

import psycopg2

import logging
from models import User, db
from flask_mail import Mail, Message
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'vbuvarova@gmail.com'
app.config['MAIL_PASSWORD'] = 'yijb aabj shcd fczb'
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('mail')

mail = Mail(app)


def get_pg_connect():
    conn = psycopg2.connect(
        host='localhost',
        port=37676,
        database='postgres',
        user='admin',
        password='admin'
    )

    return conn


@app.route('/test')
def test():
    conn = get_pg_connect()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    print(cur.fetchall())
    return redirect('/')


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = get_pg_connect()
        cur = conn.cursor()

        try:
            cur.execute("SELECT email FROM users WHERE email = %s", (email,))
            existing_email = cur.fetchone()
            if existing_email:
                conn.close()
                flash(f'Пользователь с почтой {email} уже зарегистрирован', 'error')
                return render_template('register.html')

            cur.execute(
                "INSERT INTO users (email, password) VALUES (%s, %s)",
                (email, password_hash))
            conn.commit()
            conn.close()

            flash('Регистрация успешно завершена. Теперь вы можете войти.', 'success')
            return redirect('/login')

        except Exception as ex:
            logging.error(ex, exc_info=True)
            conn.rollback()
            conn.close()
            flash(f'Произошла ошибка при регистрации: {ex}', 'error')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('data'):
        return redirect('/')
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_pg_connect()
        cur = conn.cursor()
        try:
            cur.execute("select id, email, password from users where email = %s", (email,))
            user = cur.fetchone()
            if user and hashlib.sha256(password.encode()).hexdigest() == user[2]:
                session['data'] = {'id': user[0]}
                return redirect('/')
            
            flash('Ошибка входа. Пожалуйста, проверьте введенные данные.', 'error')
            return redirect('/login')
        except Exception as ex:
            logging.error(ex, exc_info=True)
            conn.rollback()
            conn.close()

            flash('Ошибка входа. Пожалуйста, проверьте введенные данные.', 'error')
            return redirect('/')

    return render_template('login.html', )


@app.route('/profile')
def profile():
    if not session.get('data'):
        flash('Вы должны войти в систему, чтобы увидеть свой профиль.', 'warning')
        return redirect('/')

    conn = get_pg_connect()
    cur = conn.cursor()
    try:
        cur.execute("""select email from users where id = %s """, (str(session.get('data')['id'])))
        emai = cur.fetchone()[0]
        user = {'email': emai}

        return render_template('profile.html', user=user)
    except Exception as ex:
        logging.error(ex, exc_info=True)
        conn.rollback()
        conn.close()
        return redirect('/login')


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        if session.get('data'):
            conn = get_pg_connect()
            cur = conn.cursor()
            cur.execute("select email from users where id = %s", (str(session.get('data')['id'])))
            email = cur.fetchone()[0]
        msg = Message("Вам поступило новое обращение на сайте", sender='vbuvarova@gmail.com', recipients=['vbuvarova@gmail.com'])
        msg.body = f'Email: {email}\nТелефон: {phone}\nСообщение: {message}'
        mail.send(msg)
        return redirect('/')

    return render_template('contact.html')


@app.route('/del_session')
def del_session():
    session.pop('data', None)
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)

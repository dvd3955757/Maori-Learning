from flask import Flask, request, redirect, session, url_for, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maori_learning.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'replace-this-with-a-secret-key'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    verify_token = db.Column(db.String(36))

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    maori = db.Column(db.String(120), nullable=False)
    english = db.Column(db.String(120), nullable=False)

@app.before_first_request
def setup_db():
    db.create_all()
    if not Lesson.query.first():
        lessons = [
            Lesson(maori='Kia ora', english='Hello'),
            Lesson(maori='Haere rā', english='Goodbye'),
            Lesson(maori='Āe', english='Yes'),
            Lesson(maori='Kāo', english='No'),
        ]
        db.session.add_all(lessons)
        db.session.commit()

@app.route('/')
def index():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
    else:
        user = None
    return render_template_string('''
        <h1>Maori Learning App</h1>
        {% if user %}
            <p>Welcome {{user.username}}{% if not user.verified %} (unverified){% endif %}!</p>
            <p><a href="{{url_for('lessons')}}">Go to Lessons</a></p>
            <p><a href="{{url_for('logout')}}">Logout</a></p>
            {% if not user.verified %}
                <p>Please verify your account: <a href="{{url_for('verify', token=user.verify_token)}}">Verify</a></p>
            {% endif %}
        {% else %}
            <p><a href="{{url_for('register')}}">Register</a> | <a href="{{url_for('login')}}">Login</a></p>
        {% endif %}
    ''', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return 'Username already exists', 400
        if User.query.filter_by(email=email).first():
            return 'Email already exists', 400
        token = str(uuid.uuid4())
        user = User(username=username, email=email,
                    password_hash=generate_password_hash(password),
                    verify_token=token)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('index'))
    return render_template_string('''
        <h2>Register</h2>
        <form method="post">
            Username: <input name="username"><br>
            Email: <input name="email" type="email"><br>
            Password: <input name="password" type="password"><br>
            <input type="submit" value="Register">
        </form>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        return 'Invalid credentials', 400
    return render_template_string('''
        <h2>Login</h2>
        <form method="post">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <input type="submit" value="Login">
        </form>
    ''')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/verify/<token>')
def verify(token):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    if user and user.verify_token == token:
        user.verified = True
        db.session.commit()
        return 'Account verified! <a href="/">Home</a>'
    return 'Invalid verification token', 400

@app.route('/lessons')
def lessons():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    if not user.verified:
        return 'Please verify your account first', 403
    lessons = Lesson.query.all()
    return render_template_string('''
        <h2>Lessons</h2>
        <ul>
        {% for lesson in lessons %}
            <li>{{lesson.maori}} - {{lesson.english}}</li>
        {% endfor %}
        </ul>
        <a href="{{url_for('index')}}">Home</a>
    ''', lessons=lessons)

if __name__ == '__main__':
    app.run(debug=True)

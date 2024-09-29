from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
import os

# Initialize Flask app
app = Flask(__name__)

# Set the secret key for session management
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a secure key

# Initialize extensions
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['role'])
    return None

# Registration form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=35)])
    role = StringField('Role', validators=[DataRequired()])
    submit = SubmitField('Register')

# Login form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Route to show inventory items
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items').fetchall()
    conn.close()
    return render_template('index.html', items=items)

# Route to add an item
@app.route('/add', methods=('GET', 'POST'))
@login_required
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        price = request.form['price']

        conn = get_db_connection()
        conn.execute('INSERT INTO items (name, quantity, price) VALUES (?, ?, ?)',
                     (name, quantity, price))
        conn.commit()
        conn.close()

        return redirect('/')
    return render_template('add.html')

# Route to edit an item
@app.route('/edit/<int:id>', methods=('GET', 'POST'))
@login_required
def edit_item(id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        price = request.form['price']
        conn.execute('UPDATE items SET name = ?, quantity = ?, price = ? WHERE id = ?',
                     (name, quantity, price, id))
        conn.commit()
        conn.close()
        return redirect('/')

    conn.close()
    return render_template('edit.html', item=item)

# Route to delete an item
@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_item(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM items WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        role = form.role.data

        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                     (username, password, role))
        conn.commit()
        conn.close()

        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            login_user(User(user['id'], user['username'], user['role']))
            flash('Login successful!')  # Flash message for successful login
            return redirect(url_for('index'))  # Redirect to the homepage
        else:
            flash('Invalid username or password')  # Flash message for invalid login

    return render_template('login.html', form=form)

# New API Login route
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user and bcrypt.check_password_hash(user['password'], password):
        login_user(User(user['id'], user['username'], user['role']))
        return jsonify({"msg": "Login successful"}), 200  # Successful login
    else:
        return jsonify({"msg": "Invalid username or password"}), 401  # Unauthorized


# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Use PORT environment variable or default to 10000
    app.run(host="0.0.0.0", port=port, debug=True)

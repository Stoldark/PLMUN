from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange
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

# Item form for adding and editing
class ItemForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    price = DecimalField('Price', validators=[DataRequired()])
    submit = SubmitField('Add Item')

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
    form = ItemForm()
    if form.validate_on_submit():
        name = form.name.data
        quantity = form.quantity.data
        price = float(form.price.data)  # Convert Decimal to float

        conn = get_db_connection()
        conn.execute('INSERT INTO items (name, quantity, price) VALUES (?, ?, ?)', (name, quantity, price))
        conn.commit()
        conn.close()

        flash('Item added successfully!')
        return redirect(url_for('index'))

    return render_template('add.html', form=form)

# Route to edit an item
@app.route('/edit/<int:id>', methods=('GET', 'POST'))
@login_required
def edit_item(id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()

    if not item:
        flash('Item not found.')
        return redirect(url_for('index'))

    form = ItemForm()

    if form.validate_on_submit():
        name = form.name.data
        quantity = form.quantity.data
        price = float(form.price.data)

        conn.execute('UPDATE items SET name = ?, quantity = ?, price = ? WHERE id = ?',
                     (name, quantity, price, id))
        conn.commit()
        conn.close()
        flash('Item updated successfully!')
        return redirect(url_for('index'))

    # Prepopulate the form with existing item data
    form.name.data = item['name']
    form.quantity.data = item['quantity']
    form.price.data = item['price']

    conn.close()
    return render_template('edit.html', form=form, item=item)

# Route to delete an item
@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_item(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM items WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Item deleted successfully!')
    return redirect(url_for('index'))

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
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
            return render_template('login.html', form=form), 401

    return render_template('login.html', form=form)

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('index'))

# API Endpoints for the inventory system
@app.route('/api/items', methods=['GET'])
@login_required
def api_get_items():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items').fetchall()
    conn.close()
    return jsonify([dict(item) for item in items])

@app.route('/api/items', methods=['POST'])
@login_required
def api_add_item():
    data = request.get_json()
    name = data.get('name')
    quantity = data.get('quantity')
    price = data.get('price')

    conn = get_db_connection()
    conn.execute('INSERT INTO items (name, quantity, price) VALUES (?, ?, ?)',
                 (name, quantity, price))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Item added successfully'}), 201

@app.route('/api/items/<int:id>', methods=['PUT'])
@login_required
def api_update_item(id):
    data = request.get_json()
    name = data.get('name')
    quantity = data.get('quantity')
    price = data.get('price')

    conn = get_db_connection()
    conn.execute('UPDATE items SET name = ?, quantity = ?, price = ? WHERE id = ?',
                 (name, quantity, price, id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Item updated successfully'})

@app.route('/api/items/<int:id>', methods=['DELETE'])
@login_required
def api_delete_item(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM items WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Item deleted successfully'})

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Use PORT environment variable or default to 10000
    app.run(host="0.0.0.0", port=port, debug=True)

from flask import Flask, render_template, request, redirect, flash
import sqlite3
from flask_login import LoginManager, login_user, logout_user, login_required

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

# Route for the index page
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items').fetchall()
    conn.close()
    return render_template('index.html', items=items)

# Route for adding an item
@app.route('/add', methods=('GET', 'POST'))
@login_required
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        price = request.form['price']

        if not name or not quantity or not price:
            flash('Please fill out all fields!')
            return redirect('/add')

        conn = get_db_connection()
        conn.execute('INSERT INTO items (name, quantity, price) VALUES (?, ?, ?)', (name, quantity, price))
        conn.commit()
        conn.close()
        flash('Item added successfully!')
        return redirect('/')
    
    return render_template('add.html')

# Route for editing an item
@app.route('/edit/<int:id>', methods=('GET', 'POST'))
@login_required
def edit_item(id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        price = request.form['price']

        if not name or not quantity or not price:
            flash('Please fill out all fields!')
            return redirect(f'/edit/{id}')

        conn.execute('UPDATE items SET name = ?, quantity = ?, price = ? WHERE id = ?',
                     (name, quantity, price, id))
        conn.commit()
        conn.close()
        flash('Item updated successfully!')
        return redirect('/')

    conn.close()
    return render_template('edit.html', item=item)

# Route for deleting an item
@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_item(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM items WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Item deleted successfully!')
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
            return redirect('/')
        else:
            flash('Login Unsuccessful. Please check your username and password', 'danger')
            # Log for debugging
            app.logger.warning(f'Failed login attempt for username: {username}')
    
    return render_template('login.html', form=form)


# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# API Endpoint to get inventory items
@app.route('/api/items', methods=['GET'])
@login_required
def api_get_items():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items').fetchall()
    conn.close()
    return jsonify([dict(item) for item in items])

# API Endpoint to add an item
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

# API Endpoint to update an item
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

# API Endpoint to delete an item
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
    app.run(debug=True)

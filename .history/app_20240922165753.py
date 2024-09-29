from flask import Flask, render_template, request, redirect, flash
import sqlite3
from flask_login import LoginManager, login_user, logout_user, login_required

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

# Run the app
if __name__ == "__main__":
    app.run(debug=True)

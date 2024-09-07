from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# Connect to SQLite
def get_db_connection():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

# Route to show inventory items
@app.route('/')
def index():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items').fetchall()
    conn.close()
    return render_template('index.html', items=items)

# Route to add an item
@app.route('/add', methods=('GET', 'POST'))
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

if __name__ == "__main__":
    app.run(debug=True)




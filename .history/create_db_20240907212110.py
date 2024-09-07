import sqlite3

# Connect to SQLite and create the database file
connection = sqlite3.connect('inventory.db')

# Create a cursor to execute SQL commands
cursor = connection.cursor()

# Create the items table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL
    )
''')

# Commit the changes and save the table in the database
connection.commit()

# Close the connection to the database
connection.close()

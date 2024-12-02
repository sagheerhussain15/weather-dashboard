import sqlite3

def update_database():
    conn = sqlite3.connect("weather_station.db")
    cursor = conn.cursor()

    # Check if the 'Users' table exists and if 'password_hash' and 'email' columns are missing
    cursor.execute('PRAGMA table_info(Users)')
    columns = cursor.fetchall()

    # Track if 'password_hash' or 'email' columns are missing
    password_column_exists = False
    email_column_exists = False

    for column in columns:
        if column[1] == "password_hash":
            password_column_exists = True
        if column[1] == "email":
            email_column_exists = True

    # Add 'password_hash' column if it doesn't exist
    if not password_column_exists:
        cursor.execute('''ALTER TABLE Users ADD COLUMN password_hash TEXT NOT NULL DEFAULT '' ''')
        print("password_hash column added to Users table")

    # Add 'email' column if it doesn't exist
    if not email_column_exists:
        cursor.execute('''ALTER TABLE Users ADD COLUMN email TEXT''')
        print("email column added to Users table")

    # Commit changes to the database
    conn.commit()
    conn.close()
    print("Database schema updated successfully!")

if __name__ == "__main__":
    update_database()

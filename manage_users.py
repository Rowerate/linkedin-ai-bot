import sqlite3
import hashlib

DB_FILE = "linkedin_bot.db"

def add_user(email, password, is_admin=0):
    """Adds a new user to the SQLite database with a securely hashed password."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Hash the password using SHA-256
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash, is_admin) VALUES (?, ?, ?)",
            (email, password_hash, is_admin)
        )
        conn.commit()
        role = "Admin" if is_admin == 1 else "Employee"
        print(f"✅ Successfully created {role} user: {email}")
    except sqlite3.IntegrityError:
        print(f"❌ Error: A user with the email '{email}' already exists.")
    finally:
        conn.close()

def list_users():
    """Prints all users currently registered in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, is_admin FROM users")
    users = cursor.fetchall()
    conn.close()
    
    print("\n--- Current Users in Database ---")
    for user in users:
        role = "Admin" if user[2] == 1 else "Employee"
        print(f"ID: {user[0]} | Email: {user[1]} | Role: {role}")
    print("---------------------------------\n")

# ==========================================
# RUN EXAMPLES HERE
# ==========================================
if __name__ == "__main__":
    # 1. View current table data
    list_users()
    
    # 2. UNCOMMENT AND CHANGE FIELDS TO ADD USERS:
    # To add an employee:
    # add_user("intern@company.com", "securepass123", is_admin=0)
    
    # To add another administrator:
    add_user("a", "a", is_admin=1)
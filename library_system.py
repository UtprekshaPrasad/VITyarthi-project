import sqlite3
from datetime import datetime, timedelta
import sys

DB_PATH = "library.db"

def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student','teacher','librarian')),
        created_at TEXT NOT NULL DEFAULT (DATETIME('now'))
    );""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT,
        total_copies INTEGER NOT NULL CHECK(total_copies >= 0),
        created_at TEXT NOT NULL DEFAULT (DATETIME('now'))
    );""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        issue_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        returned_at TEXT,
        fine REAL DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
    );""")
    conn.commit()
    return conn

def count_active_issues(conn, book_id):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM issues WHERE book_id = ? AND returned_at IS NULL", (book_id,))
    return cur.fetchone()[0]

def add_user(conn, name, role="student"):
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, role) VALUES (?, ?)", (name, role))
    conn.commit()
    return cur.lastrowid

def add_book(conn, title, author, copies=1):
    cur = conn.cursor()
    cur.execute("INSERT INTO books (title, author, total_copies) VALUES (?, ?, ?)", (title, author, copies))
    conn.commit()
    return cur.lastrowid

def search_books(conn, keyword):
    cur = conn.cursor()
    kw = f"%{keyword}%"
    cur.execute("SELECT id, title, author, total_copies FROM books WHERE title LIKE ? OR author LIKE ?", (kw, kw))
    return cur.fetchall()

def issue_book(conn, user_id, book_id, loan_days=14, issue_date=None):
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if cur.fetchone() is None:
        return False, "User not found."
    cur.execute("SELECT id, total_copies FROM books WHERE id = ?", (book_id,))
    bk = cur.fetchone()
    if bk is None:
        return False, "Book not found."
    total_copies = bk[1]
    if count_active_issues(conn, book_id) >= total_copies:
        return False, "No copies available."
    issue_dt = issue_date if issue_date else datetime.now()
    due_dt = issue_dt + timedelta(days=loan_days)
    cur.execute("INSERT INTO issues (user_id, book_id, issue_date, due_date) VALUES (?, ?, ?, ?)",
                (user_id, book_id, issue_dt.isoformat(), due_dt.isoformat()))
    conn.commit()
    return True, cur.lastrowid

def return_book(conn, issue_id, return_date=None, fine_per_day=1.0):
    cur = conn.cursor()
    cur.execute("SELECT id, issue_date, due_date, returned_at FROM issues WHERE id = ?", (issue_id,))
    issue = cur.fetchone()
    if not issue:
        return False, "Issue record not found."
    if issue[3] is not None:
        return False, "Already returned."
    ret_dt = return_date if return_date else datetime.now()
    due_dt = datetime.fromisoformat(issue[2])
    late_days = (ret_dt.date() - due_dt.date()).days
    fine = fine_per_day * late_days if late_days > 0 else 0.0
    cur.execute("UPDATE issues SET returned_at = ?, fine = ? WHERE id = ?", (ret_dt.isoformat(), fine, issue_id))
    conn.commit()
    return True, {"fine": fine, "late_days": max(late_days, 0)}

def list_books(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, title, author, total_copies FROM books ORDER BY id")
    rows = cur.fetchall()
    result = []
    for r in rows:
        active = count_active_issues(conn, r[0])
        available = r[3] - active
        result.append({"id": r[0], "title": r[1], "author": r[2], "total_copies": r[3], "available": available})
    return result

def list_users(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, name, role FROM users ORDER BY id")
    return cur.fetchall()

def list_active_issues(conn):
    cur = conn.cursor()
    cur.execute("""
    SELECT issues.id, users.name, books.title, issues.issue_date, issues.due_date
    FROM issues
    JOIN users ON issues.user_id = users.id
    JOIN books ON issues.book_id = books.id
    WHERE issues.returned_at IS NULL
    ORDER BY issues.id
    """)
    return cur.fetchall()

def print_books(conn):
    for b in list_books(conn):
        print(f"ID:{b['id']} | {b['title']} by {b['author']} | copies:{b['total_copies']} | available:{b['available']}")

def print_users(conn):
    for u in list_users(conn):
        print(f"ID:{u[0]} | {u[1]} ({u[2]})")

def print_active_issues(conn):
    for i in list_active_issues(conn):
        print(f"IssueID:{i[0]} | User:{i[1]} | Book:{i[2]} | Issued:{i[3][:10]} | Due:{i[4][:10]}")

def sample_data(conn):
    # Add sample users/books if DB empty
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        add_user(conn, "Alice", "student")
        add_user(conn, "Bob", "student")
        add_user(conn, "Libby", "librarian")
    cur.execute("SELECT COUNT(*) FROM books")
    if cur.fetchone()[0] == 0:
        add_book(conn, "1984", "George Orwell", 2)
        add_book(conn, "Clean Code", "Robert C. Martin", 1)
        add_book(conn, "Introduction to Algorithms", "CLRS", 1)
    conn.commit()

def menu():
    conn = init_db()
    sample_data(conn)
    print("Welcome to Mini Library Management (SQLite).")
    while True:
        print("\nMenu:")
        print("1. List books")
        print("2. List users")
        print("3. Add user")
        print("4. Add book")
        print("5. Search books")
        print("6. Issue book")
        print("7. Return book")
        print("8. List active issues")
        print("9. Exit")
        choice = input("Choose (1-9): ").strip()
        if choice == "1":
            print_books(conn)
        elif choice == "2":
            print_users(conn)
        elif choice == "3":
            name = input("Name: ").strip()
            role = input("Role (student/teacher/librarian) [student]: ").strip() or "student"
            uid = add_user(conn, name, role)
            print("Added user id:", uid)
        elif choice == "4":
            title = input("Title: ").strip()
            author = input("Author: ").strip()
            copies = int(input("Copies: ").strip() or "1")
            bid = add_book(conn, title, author, copies)
            print("Added book id:", bid)
        elif choice == "5":
            kw = input("Keyword: ").strip()
            rows = search_books(conn, kw)
            for r in rows:
                print(f"ID:{r[0]} | {r[1]} by {r[2]} | total:{r[3]}")
        elif choice == "6":
            print_users(conn)
            uid = int(input("User ID: ").strip())
            print_books(conn)
            bid = int(input("Book ID: ").strip())
            days = int(input("Loan days (default 14): ").strip() or "14")
            ok, res = issue_book(conn, uid, bid, loan_days=days)
            print("Success:", ok, "Info:", res)
        elif choice == "7":
            print_active_issues(conn)
            iid = int(input("Issue ID to return: ").strip())
            fine_per_day = float(input("Fine per late day (default 1.0): ").strip() or "1.0")
            ok, info = return_book(conn, iid, fine_per_day=fine_per_day)
            print("Success:", ok, "Info:", info)
        elif choice == "8":
            print_active_issues(conn)
        elif choice == "9":
            conn.close()
            print("Goodbye.")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        try:
            sys.exit(0)
        except SystemExit:
            pass

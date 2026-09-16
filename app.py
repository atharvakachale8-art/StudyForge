import sqlite3

from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, render_template, request, redirect, url_for, session

print("Starting Program...")

app = Flask(__name__)

app.secret_key = "studyforge_secret_key"

connection = sqlite3.connect("database/studyforge.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    password TEXT NOT NULL
)
""")

cursor.execute("""CREATE TABLE IF NOT EXISTS assignments(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    title TEXT NOT NULL,

    subject TEXT NOT NULL,

    description TEXT,

    due_date TEXT NOT NULL,

    status TEXT DEFAULT 'Pending'
)""")

connection.commit()
connection.close()


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        connection = sqlite3.connect("database/studyforge.db")
        cursor = connection.cursor()

        email = request.form["email"]
        password = request.form["password"]

        cursor.execute("""
        SELECT * FROM users WHERE email = ?""", (email,))

        user = cursor.fetchone()

        if user is None:
            print("Email not found")
        elif check_password_hash(user[3], password):
            session["username"] = user[1]
            session["user_id"] = user[0]
            return redirect(url_for("dashboard"))
        else:
            print("Incorrect Password")

        connection.close()

    return render_template("login.html")

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

@app.route("/add_assignment", methods=["GET", "POST"])
def add_assignment():

    if session.get("user_id") is None:
        return redirect(url_for("login"))

    if request.method == "POST":

        connection = sqlite3.connect("database/studyforge.db")
        cursor = connection.cursor()

        user_id = session["user_id"]
        title = request.form["title"]
        subject = request.form["subject"]
        description = request.form["description"]
        due_date = request.form["due_date"]

        cursor.execute("""
        INSERT INTO assignments
        (user_id, title, subject, description, due_date)

        VALUES (?, ?, ?, ?, ?)
        """, (user_id, title, subject, description, due_date))

        connection.commit()

        cursor.execute("SELECT * FROM assignments")
        print(cursor.fetchall())
        connection.close()

        return redirect(url_for("dashboard"))

    return render_template("add_assignment.html")

@app.route("/delete_assignment/<int:assignment_id>")
def delete_assignment(assignment_id):

    if session.get("user_id") is None:
        return redirect(url_for("login"))

    connection =sqlite3.connect("database/studyforge.db")
    cursor = connection.cursor()

    cursor.execute("""
    DELETE FROM assignments
    WHERE id = ? AND user_id = ?
    """, (assignment_id, session["user_id"]))

    connection.commit()
    connection.close()

    return redirect(url_for("dashboard"))

@app.route("/complete_assignment/<int:assignment_id>")
def complete_assignment(assignment_id):

    if session.get("user_id") is None:
        return redirect(url_for("login"))

    connection = sqlite3.connect("database/studyforge.db")
    cursor = connection.cursor()

    # Check current status
    cursor.execute("""
    SELECT status
    FROM assignments
    WHERE id = ? AND user_id = ?
    """, (assignment_id, session["user_id"]))

    assignment = cursor.fetchone()

    # Only award XP if still pending
    if assignment and assignment[0] == "Pending":

        cursor.execute("""
        UPDATE assignments
        SET status = 'Completed'
        WHERE id = ? AND user_id = ?
        """, (assignment_id, session["user_id"]))

        cursor.execute("""
        UPDATE users
        SET xp = xp + 50
        WHERE id = ?
        """, (session["user_id"],))

        cursor.execute("""
        UPDATE users
        SET coins = coins + 20
        WHERE id = ?
        """, (session["user_id"],))

        connection.commit()

    connection.close()

    return redirect(url_for("dashboard"))

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        connection = sqlite3.connect("database/studyforge.db")
        cursor = connection.cursor()

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        cursor.execute("""
        INSERT INTO users(username, email, password)
        VALUES (?, ?, ?)
        """, (username, email, hashed_password))

        connection.commit()

        cursor.execute("SELECT * FROM users")
        print(cursor.fetchall())

        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/dashboard")
def dashboard():

    if session.get("user_id") is None:
        return redirect(url_for("login"))

    connection = sqlite3.connect("database/studyforge.db")
    cursor = connection.cursor()

    cursor.execute("""
    SELECT id, title, subject, due_date, status
    FROM assignments
    WHERE user_id = ?
    """, (session["user_id"],))

    assignments = cursor.fetchall()

    quest_deadlines = [assignment[3] for assignment in assignments]

    cursor.execute("""
    SELECT xp, coins
    FROM users
    WHERE id = ?
    """, (session["user_id"],))

    user = cursor.fetchone()

    total_xp = user[0]
    coins = user[1]

    level = (total_xp // 100) + 1
    xp = total_xp % 100
    xp_cap = 100

    if level < 5:
        rank = "🌱 Beginner"

    elif level < 10:
        rank = "📚 Knowledge Seeker"

    elif level < 20:
        rank = "⚔️ Scholar"

    elif level < 30:
        rank = "🔥 Elite Scholar"

    elif level < 50:
        rank = "👑 Master"

    elif level < 100:
        rank = "🌌 Grandmaster"

    else:
        rank = "Ascending Forevermore..."

    connection.close()

    username = session.get("username")

    if username is None:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        username=username,
        assignments=assignments,
        xp=xp,
        xp_cap=xp_cap,
        quest_deadlines=quest_deadlines,
        total_xp=total_xp,
        level=level,
        coins=coins,
        rank=rank
    )

print("Before app.run()")

if __name__ == "__main__":
    app.run(debug=True)
    print("This should never print")
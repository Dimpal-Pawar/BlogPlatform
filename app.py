
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from database import init_db

app = Flask(__name__)
app.secret_key = "Dimpal_BlogPlatform_2026_Secure_Key"

init_db()

def get_connection():
    conn = sqlite3.connect("blog.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return redirect("/login")


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_connection()

        try:
            conn.execute(
                "INSERT INTO users(username,email,password) VALUES(?,?,?)",
                (username, email, password)
            )
            conn.commit()
            flash("Account created successfully!")

            return redirect("/login")

        except sqlite3.IntegrityError:
            flash("Email already exists!")

        finally:
            conn.close()

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect("/dashboard")

        flash("Invalid Email or Password!")


        return redirect("/login")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()

    blogs = conn.execute(
        "SELECT * FROM blogs ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        blogs=blogs,
        username=session["username"]
    )


@app.route("/create", methods=["GET", "POST"])
def create():

    if "user_id" not in session:
        return redirect("/login")


    if request.method == "POST":

        title = request.form["title"]
        content = request.form["content"]

        conn = get_connection()

        conn.execute(
            "INSERT INTO blogs(title,content,user_id) VALUES(?,?,?)",
            (
                title,
                content,
                session["user_id"]
            )
        )

        conn.commit()
        conn.close()

        flash("Blog created successfully!")

        return redirect("/dashboard")


    return render_template("create.html")



@app.route("/blogs")
def blogs():

    conn = get_connection()

    blogs = conn.execute(
        """
        SELECT blogs.*, users.username
        FROM blogs
        JOIN users
        ON blogs.user_id = users.id
        ORDER BY blogs.id DESC
        """
    ).fetchall()


    comments = conn.execute(
        "SELECT * FROM comments ORDER BY id DESC"
    ).fetchall()


    conn.close()


    return render_template(
        "blogs.html",
        blogs=blogs,
        comments=comments
    )


@app.route("/like/<int:id>")
def like(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()

    conn.execute(
        """
        UPDATE blogs
        SET likes = likes + 1
        WHERE id = ?
        """,
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/blogs")





@app.route("/comment/<int:id>", methods=["POST"])
def comment(id):

    if "user_id" not in session:
        return redirect("/login")

    comment_text = request.form["comment"]

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO comments(blog_id, username, comment)
        VALUES(?,?,?)
        """,
        (
            id,
            session["username"],
            comment_text
        )
    )

    conn.commit()
    conn.close()

    return redirect("/blogs")





@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")


    conn = get_connection()


    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()


    blogs = conn.execute(
        """
        SELECT * FROM blogs 
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()


    conn.close()


    return render_template(
        "profile.html",
        user=user,
        blogs=blogs
    )





@app.route("/search")
def search():

    if "user_id" not in session:
        return redirect("/login")


    query = request.args.get("q")


    conn = get_connection()


    blogs = conn.execute(
        """
        SELECT blogs.*, users.username
        FROM blogs
        JOIN users
        ON blogs.user_id = users.id
        WHERE title LIKE ? OR content LIKE ?
        ORDER BY blogs.id DESC
        """,
        (
            "%" + query + "%",
            "%" + query + "%"
        )
    ).fetchall()


    comments = conn.execute(
        "SELECT * FROM comments ORDER BY id DESC"
    ).fetchall()


    conn.close()


    return render_template(
        "blogs.html",
        blogs=blogs,
        comments=comments
    )





@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/login")


    if session.get("username") != "Admin":
        return "Access Denied"


    conn = get_connection()


    users = conn.execute(
        "SELECT * FROM users"
    ).fetchall()


    blogs = conn.execute(
        """
        SELECT blogs.*, users.username
        FROM blogs
        JOIN users
        ON blogs.user_id = users.id
        ORDER BY blogs.id DESC
        """
    ).fetchall()


    conn.close()


    return render_template(
        "admin.html",
        users=users,
        blogs=blogs
    )



@app.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully!")

    return redirect("/login")


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )


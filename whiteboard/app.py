import os

from cs50 import SQL
import datetime
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
import pytz
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

# Application
app = Flask(__name__)

# Session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# SQLite database
db = SQL("sqlite:///whiteboard.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

    #TODO: Get the messages, and followers corresponding to the user to print them in the homepage

    return render_template("index.html", users=users)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    error = None

    # User reached route via POST
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            error = "You must provide a valid username"
            return render_template("login.html", error=error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "You must provide a password"
            return render_template("login.html", error=error)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["pass"], request.form.get("password")
        ):
            error = "invalid username and/or password"
            return render_template("login.html", error=error)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash('You were successfully logged in')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    error = None
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            error = "You must provide a valid username"
            return render_template("register.html", error=error)
        
        # Ensure a name was submitted
        if not request.form.get("name"):
            error = "You must provide a name"
            return render_template("register.html", error=error)

        #Esure an email was submitted
        if not request.form.get("email"):
            error = "You must provide a valid email"
            return render_template("register.html", error=error)

        # Ensure password was submitted
        elif not request.form.get("password") or not request.form.get("confirmation"):
            error = "You must provide password"
            return render_template("register.html", error=error)

        # Ensure the passwords submitted are the same
        elif not request.form.get("password") == request.form.get("confirmation"):
            error = "Passwords must match"
            return render_template("register.html", error=error)

        user = request.form.get("username")
        name = request.form.get("name")
        email = request.form.get("email")
        hash_pass = generate_password_hash(request.form.get("password"), method="scrypt", salt_length=16)

        # Check if the username alerady exist
        check = db.execute("SELECT username FROM users WHERE username = ?", user)
        if check:
            error = "This username already exist"
            return render_template("register.html", error=error)
        
        # Check if the email already exist
        check = db.execute("SELECT email FROM users WHERE email = ?", email)
        if check:
            error = "This email already exist"
            return render_template("register.html", error=error)

        db.execute("INSERT INTO users (username, name, pass, email) VALUES (?, ?, ?, ?)", user, name, hash_pass, email)

        # Redirect user to the login page
        flash('You are successfully registered!')
        return redirect("/login")
    
    return render_template("register.html", error=error)
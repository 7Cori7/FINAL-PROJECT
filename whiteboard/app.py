import os

from cs50 import SQL
import datetime
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
import pytz
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, format_date

# Application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["format_date"] = format_date

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
    """Get the messages, and followers corresponding to the user to print them in the homepage"""
    users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"]) 

    hack = db.execute("SELECT * FROM followers WHERE user_id = ? AND follows = ?", session["user_id"], session["user_id"])

    if not hack:
        db.execute("INSERT INTO followers (user_id, follows) VALUES (?, ?)", session["user_id"], session["user_id"]) 

    # Get all the messages from the people the user is following
    messages = db.execute("SELECT username, image, content, likes, date, messages.id, messages.user_id FROM users, messages, followers WHERE users.id = messages.user_id AND messages.user_id = followers.follows AND followers.user_id = ? ORDER BY date DESC", session["user_id"])

    # Get 5 people the user is following
    following = db.execute("SELECT username, image FROM users, followers WHERE users.id = followers.follows AND followers.user_id = ? AND followers.follows != ? LIMIT 5", session["user_id"], session["user_id"])

    return render_template("index.html", users=users, messages=messages, following=following)


@app.route("/delete-message", methods=["POST"])
@login_required
def delete_message():
    """Delete a message"""
    # Check if all data was correctly sent
    if not request.form.get("id"):
        flash("An error occurred when deleting the message")
        return redirect("/")
    
    message_id = request.form.get("id")

    # Get message by id, and confirm if it match with the user in session
    user_message = db.execute("SELECT * FROM messages WHERE id = ? AND user_id = ?", message_id, session["user_id"])

    if user_message:
        db.execute("DELETE FROM favorites WHERE message_id = ?", message_id)
        db.execute("DELETE FROM messages WHERE id = ?", message_id)
    
    return redirect("/")


@app.route("/edit-message", methods=["POST"])
@login_required
def edit_message():
    """Update a message"""
    # Check if all data was correctly sent
    if not request.form.get("id"):
        flash("An error occurred when updating the message")
        return redirect("/")
    if not request.form.get("content"):
        flash("An error occurred when updating the message")
        return redirect("/")
    
    message_id = request.form.get("id")
    message_content = request.form.get("content")

    # Get message by id, and confirm if it match with the user in session
    user_message = db.execute("SELECT * FROM messages WHERE id = ? AND user_id = ?", message_id, session["user_id"])

    if user_message:
        db.execute("UPDATE messages SET content = ? WHERE id = ? AND user_id = ?", message_content, message_id, session["user_id"])
    
    return redirect("/")


@app.route("/follow/<username>/<int:user_id>")
@login_required
def follow_user(username, user_id):
    """Start following a user"""
    # Prevent the user from following themself
    if user_id == session["user_id"]:
        flash("You can't follow yourself !!! 😭")
        return redirect("/")
    
    # Prevent to follow an user more than once
    following = db.execute("SELECT username, follows FROM users, followers WHERE users.id = followers.follows and followers.user_id = ?", session["user_id"])

    for row in following:
        if row["username"] == username or row["follows"] == user_id:
            flash("You can't follow the same person more than once 😵")
            return redirect("/")

    # Insert user into DB
    if user_id and username:
        db.execute("INSERT INTO followers (user_id, follows) VALUES (?, ?)", session["user_id"], user_id)
        # return redirect("/profile/"+username)
    
    return redirect("/")

@app.route("/liked/<int:message_id>/<int:user>")
@login_required
def liked(message_id, user):
    """Update the likes of a message"""
    # Check if the user already liked the message
    like = db.execute("SELECT * FROM favorites WHERE user_id = ? AND message_id = ?", session["user_id"], message_id)

    # Actions to take accordingly
    if not like:
        db.execute("UPDATE messages SET likes = likes + 1 WHERE user_id = ? AND id = ?", user, message_id)
        db.execute("INSERT INTO favorites (user_id, message_id) VALUES (?, ?)", session["user_id"], message_id)
    
    else:
        db.execute("DELETE FROM favorites WHERE user_id = ? AND message_id = ?", session["user_id"], message_id)
        db.execute("UPDATE messages SET likes = likes - 1 WHERE user_id = ? AND id = ?", user, message_id)
    
    # Refresh the page
    return redirect("/")
    

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
        return render_template("login.html", error=error, page="login")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


#TODO: Route for Profile


@app.route("/publish", methods=["POST"])
@login_required
def publish():
    """Publishing a new message"""
    
    # Ensure a message content is submitted
    if not request.form.get("content"):
        return
    # Get the data
    content = request.form.get("content")
    date = datetime.datetime.now(pytz.timezone("US/Eastern"))

    # Insert in db
    db.execute("INSERT INTO messages (user_id, content, date) VALUES (?,?,?)", session["user_id"], content, date)

    # Refresh homepage
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


@app.route("/search")
def search():
    """Search for users"""
    users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"]) 
    if not request.args.get("user"):
        flash("Enter a name to search")
        return redirect("/")
    search = request.args.get("user")
    search_list = db.execute("SELECT image, username, id FROM users WHERE username LIKE ? OR name LIKE ?", '%'+search+'%', '%'+search+'%')
    following_list = db.execute("SELECT * FROM followers WHERE user_id = ?", session["user_id"])

    for user in search_list:
        for row in following_list:
            if user["id"] == row["follows"]:
                user["following"] = True
            else:
                user["following"] = False

    return render_template("search.html", search_list=search_list, users=users)


@app.route("/unfollow/<username>/<int:user_id>")
@login_required
def unfollow_user(username, user_id):
    """Stop following a user"""
    if user_id and username:
        db.execute("DELETE FROM followers WHERE user_id = ? AND follows = ?", session["user_id"], user_id)
    
    return redirect("/")
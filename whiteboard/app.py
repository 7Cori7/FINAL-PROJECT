import os

from cs50 import SQL
import datetime
from fileinput import filename
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
import pytz
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import login_required, format_date, allowed_file

# Application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["format_date"] = format_date

# Session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Handle file upload
UPLOAD_FOLDER = "./static"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1000 * 1000

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
    path = "home"
    hack = db.execute("SELECT * FROM followers WHERE user_id = ? AND follows = ?", session["user_id"], session["user_id"])

    if not hack:
        db.execute("INSERT INTO followers (user_id, follows) VALUES (?, ?)", session["user_id"], session["user_id"]) 

    # Get all the messages from the people the user is following
    messages = db.execute("SELECT username, image, content, likes, date, messages.id, messages.user_id FROM users, messages, followers WHERE users.id = messages.user_id AND messages.user_id = followers.follows AND followers.user_id = ? ORDER BY date DESC", session["user_id"])
    # Get messages liked by the user
    for row in messages:
        is_liked = db.execute("SELECT * FROM favorites WHERE message_id = ? AND user_id = ?", row["id"], session["user_id"])
        if is_liked:
            row["liked"] = True
        else:
            row["liked"] = False

    # Get 5 people the user is following
    following = db.execute("SELECT username, image FROM users, followers WHERE users.id = followers.follows AND followers.user_id = ? AND followers.follows != ? LIMIT 5", session["user_id"], session["user_id"])

    return render_template("index.html", users=users, messages=messages, following=following, path=path)


@app.route("/delete", methods=["POST"])
@login_required
def delete():
    """Delete profile"""
    if not request.form.get("delete"):
        flash("An error has occurred 😵")
        return redirect("/settings")
    
    id = request.form.get("delete")

    if not int(id) == session["user_id"]:
        flash("An error has occurred 😵")
        return redirect("/settings")
    
    # delete user from followers
    db.execute("DELETE FROM followers WHERE user_id = ?", session["user_id"])
    db.execute("DELETE FROM followers WHERE follows = ?",  session["user_id"])
    # delete user's messages that were liked by others if there are any
    messages = db.execute("SELECT * FROM messages WHERE user_id = ?", session["user_id"])
    if messages:
        for row in messages:
            db.execute("DELETE FROM favorites WHERE message_id = ?", row["id"])
    # delete from favorites 
    db.execute("DELETE FROM favorites WHERE user_id = ?", session["user_id"])       
    # delete from messages
    db.execute("DELETE FROM messages WHERE user_id = ?", session["user_id"])
    # delete from users
    db.execute("DELETE FROM users WHERE id = ?", session["user_id"])
    # clear session
    session.clear()

    return redirect("/")


@app.route("/delete-message/<path>", methods=["POST"])
@login_required
def delete_message(path):
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
    
    if path == "home":
        return redirect("/")
    else:
        return redirect("/"+path)


@app.route("/edit-message/<path>", methods=["POST"])
@login_required
def edit_message(path):
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
    
    if path == "home":
        return redirect("/")
    else:
        return redirect("/"+path)


@app.route("/edit-profile/<username>", methods=["POST"])
@login_required
def edit_profile(username):
    """Edit the user profile"""
    # Check if the profile belongs to user in session
    user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    if user[0]["username"] != username:
        flash("Error! 😵❌")
        return redirect("/")
    # Check if all input fields were delivered
    if not request.form.get("workplace") or not request.form.get("location") or not request.form.get("studies") or not request.form.get("phone"):
        flash("❌An error occurred when updating the profile❌")
        return redirect("/profile-"+username)
    
    # if all is good
    workplace = request.form.get("workplace")
    location = request.form.get("location")
    studies = request.form.get("studies")
    phone = request.form.get("phone")

    db.execute("UPDATE users SET workplace = ?, location= ?, studies = ?, phone = ? WHERE username = ?", workplace, location, studies, phone, username)
    flash("Your profile has been sucessfully updated! ✔️")
    return redirect("/profile-"+username)


@app.route("/favorites-<username>")
@login_required
def favorites(username):
    """Show all favorited messages in the favorites page"""
    path = "favorites-"+username
    if not username:
        return render_template("notfound.html")
    # Get the session
    users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    # Get the profile data
    profile = db.execute("SELECT * FROM users WHERE username = ?", username)
    if not profile:
        return render_template("notfound.html")
    
    profile_id = profile[0]["id"]

    if profile_id == session["user_id"]:
        profile[0]["session"] = True
    else:
        profile[0]["session"] = False
        is_followed = db.execute("SELECT * FROM followers WHERE follows = ? AND user_id = ?", profile_id, session["user_id"])
        if is_followed:
            profile[0]["following"] = True
        else:
            profile[0]["following"] = False
    
    # Get the followers count
    followers = db.execute("SELECT COUNT(follows) FROM followers JOIN users ON followers.follows = users.id WHERE users.username = ? AND followers.user_id != ?", username, profile_id)
    total_followers = followers[0]["COUNT(follows)"]
    # Get the following count
    following = db.execute("SELECT COUNT(user_id) FROM followers JOIN users ON followers.user_id = users.id WHERE users.username = ? AND followers.follows != ?", username, profile_id)
    total_following = following[0]["COUNT(user_id)"]
    # Get the user's list of favorites
    favorites = db.execute("SELECT message_id, username, image, users.id AS id, content, likes, date FROM favorites, users, messages WHERE favorites.message_id = messages.id AND messages.user_id = users.id AND favorites.user_id = ? ORDER BY stamp DESC", profile_id)

    return render_template("favorites.html", path=path, users=users, profile=profile, followers=total_followers, following=total_following, favorites=favorites)


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
        return redirect("/profile-"+username)
    
    return redirect("/profile-"+username)


@app.route("/followers-<username>")
@login_required
def followers(username):
    """Print all followers in the followers page"""
    if not username:
        return render_template("notfound.html")
    # Get the session
    users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    # Get the profile data
    profile = db.execute("SELECT * FROM users WHERE username = ?", username)
    if not profile:
        return render_template("notfound.html")
    
    profile_id = profile[0]["id"]
    # Get followers list
    list_followers = db.execute("SELECT username, name, image FROM users, followers WHERE users.id = followers.user_id AND followers.follows = ? AND followers.user_id != ?", profile_id, profile_id)

    return render_template("followers.html", users=users, profile=profile, followers=list_followers)


@app.route("/following-<username>")
@login_required
def following(username):
    """Print all users in the following page"""
    if not username:
        return render_template("notfound.html")
    # Get the session
    users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    # Get the profile data
    profile = db.execute("SELECT * FROM users WHERE username = ?", username)
    if not profile:
        return render_template("notfound.html")
    
    profile_id = profile[0]["id"]
    # Get following list
    list_following = db.execute("SELECT username, name, image FROM users, followers WHERE users.id = followers.follows AND followers.user_id = ? AND followers.follows != ?", profile_id, profile_id)

    return render_template("following.html", users=users, profile=profile, following=list_following)


@app.route("/history-<username>")
@login_required
def history(username):
    """Show all messages made by the user in the history page"""
    path = "history-"+username
    if not username:
        return render_template("notfound.html")
    # Get the session
    users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    # Get the profile data
    profile = db.execute("SELECT * FROM users WHERE username = ?", username)
    if not profile:
        return render_template("notfound.html")
    
    profile_id = profile[0]["id"]

    if profile_id == session["user_id"]:
        profile[0]["session"] = True
    else:
        profile[0]["session"] = False
        is_followed = db.execute("SELECT * FROM followers WHERE follows = ? AND user_id = ?", profile_id, session["user_id"])
        if is_followed:
            profile[0]["following"] = True
        else:
            profile[0]["following"] = False
    
    # Get the followers count
    followers = db.execute("SELECT COUNT(follows) FROM followers JOIN users ON followers.follows = users.id WHERE users.username = ? AND followers.user_id != ?", username, profile_id)
    total_followers = followers[0]["COUNT(follows)"]
    # Get the following count
    following = db.execute("SELECT COUNT(user_id) FROM followers JOIN users ON followers.user_id = users.id WHERE users.username = ? AND followers.follows != ?", username, profile_id)
    total_following = following[0]["COUNT(user_id)"]
    # Get the user's messages
    messages = db.execute("SELECT users.id AS id, username, image, content, likes, date, messages.id AS msg_id FROM users JOIN messages ON users.id = messages.user_id WHERE users.username = ? ORDER BY messages.date DESC", username)
    # Get messages liked by the user
    for row in messages:
        is_liked = db.execute("SELECT * FROM favorites WHERE message_id = ? AND user_id = ?", row["msg_id"], session["user_id"])
        if is_liked:
            row["liked"] = True
        else:
            row["liked"] = False
                                      
    return render_template("history.html", users=users, path=path, profile=profile, followers=total_followers, following=total_following, messages=messages)


@app.route("/info-<username>")
@login_required
def info(username):
    """Show the profile information in the info page"""
    path = "info-"+username
    if not username:
        return render_template("notfound.html")
    # Get the session
    users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    # Get the profile data
    profile = db.execute("SELECT * FROM users WHERE username = ?", username)
    if not profile:
        return render_template("notfound.html")
    
    profile_id = profile[0]["id"]

    if profile_id == session["user_id"]:
        profile[0]["session"] = True
    else:
        profile[0]["session"] = False
        is_followed = db.execute("SELECT * FROM followers WHERE follows = ? AND user_id = ?", profile_id, session["user_id"])
        if is_followed:
            profile[0]["following"] = True
        else:
            profile[0]["following"] = False
    
    # Get the followers count
    followers = db.execute("SELECT COUNT(follows) FROM followers JOIN users ON followers.follows = users.id WHERE users.username = ? AND followers.user_id != ?", username, profile_id)
    total_followers = followers[0]["COUNT(follows)"]
    # Get the following count
    following = db.execute("SELECT COUNT(user_id) FROM followers JOIN users ON followers.user_id = users.id WHERE users.username = ? AND followers.follows != ?", username, profile_id)
    total_following = following[0]["COUNT(user_id)"]

    # Get followers list of 3
    list_followers = db.execute("SELECT username, image FROM users, followers WHERE users.id = followers.user_id AND followers.follows = ? AND followers.user_id != ? LIMIT 3", profile_id, profile_id)
    # Get following list of 3
    list_following = db.execute("SELECT username, image FROM users, followers WHERE users.id = followers.follows AND followers.user_id = ? AND followers.follows != ? LIMIT 3", profile_id, profile_id)
    
    return render_template("info.html", path=path, users=users, profile=profile, following=total_following, followers= total_followers, list_followers=list_followers, list_following=list_following)


@app.route("/image/<username>", methods=["POST"])
@login_required
def image(username):
    """Change profile's picture"""
    if "image" not in request.files:
        flash("No file was sent❌")
        return redirect("/profile-"+username)
    
    f = request.files["image"]

    if f.filename == "":
        flash("No selected file")
        return redirect("/profile-"+username)
    
    if f and allowed_file(f.filename):
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        print(filename)

    db.execute("UPDATE users SET image = ? WHERE id = ?", filename, session["user_id"])
    
    flash("Your profile picture has been updated! ✔️")
    return redirect("/profile-"+username)


@app.route("/liked/<path>/<int:message_id>/<int:user>")
@login_required
def liked(path, message_id, user):
    """Update the likes of a message"""
    # Check if the user already liked the message
    like = db.execute("SELECT * FROM favorites WHERE user_id = ? AND message_id = ?", session["user_id"], message_id)
    now = datetime.datetime.now()
    timpeStamp = datetime.datetime.timestamp(now)
    # Actions to take accordingly
    if not like:
        db.execute("UPDATE messages SET likes = likes + 1 WHERE user_id = ? AND id = ?", user, message_id)
        db.execute("INSERT INTO favorites (user_id, message_id, stamp) VALUES (?, ?, ?)", session["user_id"], message_id, timpeStamp)
    
    else:
        db.execute("DELETE FROM favorites WHERE user_id = ? AND message_id = ?", session["user_id"], message_id)
        db.execute("UPDATE messages SET likes = likes - 1 WHERE user_id = ? AND id = ?", user, message_id)
    
    # Refresh the page
    if path == "home":
        return redirect("/")
    else:
        return redirect("/"+path)
    

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    error = None

    # Route via POST
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

    # Route via GET
    else:
        return render_template("login.html", error=error, page="login")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/profile-<username>")
@login_required
def profile(username):
    """Getting data for profile page"""
    path = "profile-"+username
    if not username:
        return render_template("notfound.html")
    # Get the session
    users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    # Get the profile data
    profile = db.execute("SELECT * FROM users WHERE username = ?", username)
    if not profile:
        return render_template("notfound.html")
    
    for row in profile:
        profile_id = row["id"]
        if profile_id == session["user_id"]:
            row["session"] = True
        else:
            row["session"] = False
            is_followed = db.execute("SELECT * FROM followers WHERE follows = ? AND user_id = ?", profile_id, session["user_id"])
            if is_followed:
                row["following"] = True
            else:
                row["following"] = False
    
    # Get the followers count
    followers = db.execute("SELECT COUNT(follows) FROM followers JOIN users ON followers.follows = users.id WHERE users.username = ? AND followers.user_id != ?", username, profile_id)
    for item in followers:
        total_followers = item["COUNT(follows)"]
    # Get the following count
    following = db.execute("SELECT COUNT(user_id) FROM followers JOIN users ON followers.user_id = users.id WHERE users.username = ? AND followers.follows != ?", username, profile_id)
    for item in following:
        total_following = item["COUNT(user_id)"]
    # Get the user's last favorite
    favorite = db.execute("SELECT message_id, username, image, users.id AS id, content, likes, date FROM favorites, users, messages WHERE favorites.message_id = messages.id AND messages.user_id = users.id AND favorites.user_id = ? ORDER BY stamp DESC LIMIT 1", profile_id)
    if favorite:
        favorite[0]["liked"] = True
    # Get the user's last message
    message = db.execute("SELECT users.id AS id, username, image, content, likes, date, messages.id AS msg_id FROM users JOIN messages ON users.id = messages.user_id WHERE users.username = ? ORDER BY messages.date DESC LIMIT 1", username)
    if message:
        # Get messages liked by the user
        for row in message:
            is_liked = db.execute("SELECT * FROM favorites WHERE message_id = ? AND user_id = ?", row["msg_id"], session["user_id"])
            if is_liked:
                row["liked"] = True
            else:
                row["liked"] = False

    return render_template("profile.html", users=users, profile=profile, followers=total_followers, following=total_following, favorite=favorite, message=message, path=path)


@app.route("/publish/<path>", methods=["POST"])
@login_required
def publish(path):
    """Posting a new message"""
    # Ensure a message content is submitted
    if not request.form.get("content"):
        flash("Your message was empty")
        if path == "home":
            return redirect("/")   
        else:
            return redirect("/"+path)
    # Get the data
    content = request.form.get("content")
    if len(content) > 150:
        flash("The message is too long")
        if path == "home":
            return redirect("/")   
        else:
            return redirect("/"+path)
    
    date = datetime.datetime.now(pytz.timezone("US/Eastern"))

    # Insert into db
    db.execute("INSERT INTO messages (user_id, content, date) VALUES (?,?,?)", session["user_id"], content, date)

    # Refresh homepage
    if path == "home":
        return redirect("/")   
    else:
        return redirect("/"+path)
        

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
        date = datetime.date.today()
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

        db.execute("INSERT INTO users (username, name, pass, email, joined) VALUES (?, ?, ?, ?, ?)", user, name, hash_pass, email, date)

        # Redirect user to the login page
        flash('You are successfully registered!')
        return redirect("/login")
    
    return render_template("register.html", error=error)


@app.route("/search")
def search():
    """Search for users and show them in the search page"""
    users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"]) 
    if not request.args.get("user"):
        flash("Enter a name to search")
        return redirect("/")
    search = request.args.get("user")
    search_list = db.execute("SELECT image, username, id FROM users WHERE username LIKE ? OR name LIKE ?", '%'+search+'%', '%'+search+'%')

    # Check if the results of search have users being followed or if it's the session user
    for user in search_list:
        is_followed = db.execute("SELECT * FROM followers WHERE user_id = ? AND follows = ?", session["user_id"], user["id"])
        if is_followed:

            user["following"] = True
            
            for row in is_followed:
                if row["follows"] == session["user_id"]:
                    user["session"] = True
                else:
                    user["session"] = False
        else:
            user["following"] = False
    
    return render_template("search.html", search_list=search_list, users=users)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Edit settings for user profile"""
    users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    if request.method == "POST":
        # Ensure password was submitted
        if not request.form.get("password") or not request.form.get("confirmation"):
            flash("You must provide password ❌")
            return redirect("/settings")
        # Ensure the passwords submitted are the same
        if not request.form.get("password") == request.form.get("confirmation"):
            flash("Passwords must match ❌")
            return redirect("/settings")
        
        hash_pass = generate_password_hash(request.form.get("password"), method="scrypt", salt_length=16)
        db.execute("UPDATE users SET pass = ? WHERE id = ?", hash_pass, session["user_id"])

        flash("Your password has been sucessfully updated! ✔️")
        return redirect("/")
    # Get the followers count
    followers = db.execute("SELECT COUNT(follows) FROM followers JOIN users ON followers.follows = users.id WHERE users.id = ? AND followers.user_id != ?", session["user_id"], session["user_id"])
    total_followers = followers[0]["COUNT(follows)"]
    # Get the following count
    following = db.execute("SELECT COUNT(user_id) FROM followers JOIN users ON followers.user_id = users.id WHERE users.id = ? AND followers.follows != ?", session["user_id"], session["user_id"])
    total_following = following[0]["COUNT(user_id)"] 

    return render_template("settings.html", users=users, followers=total_followers, following=total_following)


@app.route("/settings/username", methods=["POST"])
@login_required
def change_username():
    """Change the username"""
    if not request.form.get("username ❌"):
        flash("Invalid username")
        return redirect("/settings")
    
    username = request.form.get("username")
    check = db.execute("SELECT * FROM users WHERE username = ?", username)

    if check:
        flash("The username already exists ❌")
        return redirect("/settings")
    
    db.execute("UPDATE users SET username = ? WHERE users.id = ?", username, session["user_id"])
    flash("Your username has been sucessfully updated! ✔️")
    return redirect("/")


@app.route("/unfollow/<username>/<int:user_id>")
@login_required
def unfollow_user(username, user_id):
    """Stop following a user"""
    if user_id and username:
        db.execute("DELETE FROM followers WHERE user_id = ? AND follows = ?", session["user_id"], user_id)

    return redirect("/")
import datetime
from flask import redirect, render_template, request, session
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def format_date(date):
    """Format the date"""
    date_obj = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    new_format = date_obj.strftime('%B %d, %Y %I:%M %p')
    return new_format
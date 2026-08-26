from functools import wraps
from flask import flash, redirect, url_for, session
from app.models import User
from app.extensions import db


def current_user():
    user_id = session.get("user_id")
    return db_get_user(user_id) if user_id else None


def db_get_user(user_id):
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login", next=request_path()))
        return view(*args, **kwargs)
    return wrapped


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login"))
            if user.role not in roles:
                flash("You are not authorized to access that page.", "danger")
                return redirect(url_for("main.dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def request_path():
    from flask import request
    return request.path

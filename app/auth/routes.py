from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import User


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email, is_active=True).first()
        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            session["user_role"] = user.role
            flash(f"Welcome back, {user.full_name}.", "success")
            return redirect(request.args.get("next") or url_for("main.dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

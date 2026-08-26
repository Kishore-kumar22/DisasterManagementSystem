from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models import Alert, Disaster, AuditLog
from app.auth.utils import login_required, current_user, roles_required


alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.route("/")
@login_required
def list_alerts():
    now = datetime.utcnow()
    expired = Alert.query.filter(Alert.status == "Active", Alert.expires_at.isnot(None), Alert.expires_at < now).all()
    for alert in expired:
        alert.status = "Expired"
    if expired:
        db.session.commit()
    alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    disasters = Disaster.query.order_by(Disaster.created_at.desc()).all()
    return render_template("alerts/list.html", alerts=alerts, disasters=disasters)


@alerts_bp.route("/new", methods=["GET", "POST"])
@roles_required("admin")
def create_alert():
    disasters = Disaster.query.order_by(Disaster.created_at.desc()).all()
    if request.method == "POST":
        try:
            disaster_id = int(request.form.get("disaster_id"))
        except (TypeError, ValueError):
            disaster_id = 0
        disaster = Disaster.query.get(disaster_id)
        if not disaster:
            flash("Choose a valid disaster incident.", "danger")
            return render_template("alerts/form.html", disasters=disasters)
        title = request.form.get("title", "").strip()
        message = request.form.get("message", "").strip()
        severity = request.form.get("severity", "Medium")
        if not title or not message:
            flash("Alert title and message are required.", "danger")
            return render_template("alerts/form.html", disasters=disasters)
        alert = Alert(disaster_id=disaster.id, created_by=current_user().id, title=title, message=message, severity=severity, status="Active")
        db.session.add(alert)
        db.session.add(AuditLog(user_id=current_user().id, action="created", entity_type="alert", details=title))
        db.session.commit()
        flash("Emergency alert published in the application.", "success")
        return redirect(url_for("alerts.list_alerts"))
    return render_template("alerts/form.html", disasters=disasters)


@alerts_bp.route("/<int:alert_id>/close", methods=["POST"])
@login_required
def close_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.status = "Closed"
    db.session.commit()
    flash("Alert closed.", "info")
    return redirect(url_for("alerts.list_alerts"))

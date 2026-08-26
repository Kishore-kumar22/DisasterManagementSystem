from flask import Blueprint, render_template, redirect, url_for, session, request, flash    
from sqlalchemy import func, or_

from app.extensions import db
from app.models import (
    Disaster,
    Resource,
    Response,
    Alert,
    Shelter,
)
from app.auth.utils import login_required


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if session.get("user_id"):
        return dashboard()

    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    # Incident statistics
    total_incidents = Disaster.query.count()

    active_incidents = (
        Disaster.query
        .filter(Disaster.status != "Resolved")
        .count()
    )

    critical_incidents = (
        Disaster.query
        .filter(
            or_(
                Disaster.severity == "Critical",
                Disaster.priority_category == "CRITICAL",
            )
        )
        .count()
    )

    people_affected = (
        db.session
        .query(
            func.coalesce(
                func.sum(Disaster.affected_population),
                0,
            )
        )
        .scalar()
        or 0
    )

    # Resource statistics
    available_resources = (
        db.session
        .query(
            func.coalesce(
                func.sum(Resource.available_quantity),
                0,
            )
        )
        .scalar()
        or 0
    )

    # Shelter statistics
    total_shelters = Shelter.query.count()

    shelter_capacity = (
        db.session
        .query(
            func.coalesce(
                func.sum(Shelter.capacity),
                0,
            )
        )
        .scalar()
        or 0
    )

    shelter_occupied = (
        db.session
        .query(
            func.coalesce(
                func.sum(Shelter.occupied),
                0,
            )
        )
        .scalar()
        or 0
    )

    shelter_available = max(
        0,
        shelter_capacity - shelter_occupied,
    )

    # Recent incidents
    recent_incidents = (
        Disaster.query
        .order_by(Disaster.created_at.desc())
        .limit(6)
        .all()
    )

    # Highest-priority active incidents
    priority_incidents = (
        Disaster.query
        .filter(Disaster.status != "Resolved")
        .order_by(Disaster.priority_score.desc())
        .limit(6)
        .all()
    )

    # Active alerts
    recent_alerts = (
        Alert.query
        .filter(Alert.status == "Active")
        .order_by(Alert.created_at.desc())
        .limit(5)
        .all()
    )

    # Response count
    response_count = Response.query.count()

    return render_template(
        "dashboard.html",
        total_incidents=total_incidents,
        active_incidents=active_incidents,
        critical_incidents=critical_incidents,
        people_affected=people_affected,
        available_resources=available_resources,
        recent_incidents=recent_incidents,
        priority_incidents=priority_incidents,
        recent_alerts=recent_alerts,
        response_count=response_count,
        total_shelters=total_shelters,
        shelter_capacity=shelter_capacity,
        shelter_occupied=shelter_occupied,
        shelter_available=shelter_available,
    )
@main_bp.route("/shelters")
@login_required
def shelters():
    shelters = Shelter.query.order_by(Shelter.name).all()

    return render_template(
        "shelters/list.html",
        shelters=shelters,
    )


@main_bp.route("/shelters/new", methods=["GET", "POST"])
@login_required
def create_shelter():
    if request.method == "POST":
        try:
            capacity = int(request.form.get("capacity", 0))
            occupied = int(request.form.get("occupied", 0))

            if capacity < 0 or occupied < 0:
                raise ValueError("Capacity and occupied values cannot be negative.")

            if occupied > capacity:
                raise ValueError(
                    "Occupied people cannot exceed shelter capacity."
                )

        except (TypeError, ValueError) as exc:
            flash(str(exc), "danger")
            return render_template("shelters/form.html", shelter=None)

        shelter = Shelter(
            name=request.form.get("name", "").strip(),
            location=request.form.get("location", "").strip(),
            capacity=capacity,
            occupied=occupied,
            contact=request.form.get("contact", "").strip(),
        )

        if not shelter.name or not shelter.location:
            flash("Shelter name and location are required.", "danger")
            return render_template("shelters/form.html", shelter=None)

        shelter.sync_status()

        db.session.add(shelter)
        db.session.commit()

        flash("Shelter added successfully.", "success")
        return redirect(url_for("main.shelters"))

    return render_template(
        "shelters/form.html",
        shelter=None,
    )
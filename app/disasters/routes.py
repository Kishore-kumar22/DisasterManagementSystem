from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import or_
from app.extensions import db
from app.models import Disaster, DisasterStatusHistory, AuditLog, User, Resource
from app.auth.utils import login_required, current_user, roles_required
from .scoring import calculate_priority


disasters_bp = Blueprint("disasters", __name__)
STATUS_VALUES = ["Reported", "Responding", "Resolved"]
SEVERITY_VALUES = ["Low", "Medium", "High", "Critical"]


def parse_datetime(value):
    if not value:
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return datetime.utcnow()


def get_shortage_ratio(disaster):
    allocated = 0
    capacity = 0
    for response in disaster.responses:
        for allocation in response.allocations:
            allocated += allocation.quantity_allocated
            capacity += max(1, allocation.resource.total_quantity)
    return min(1.0, allocated / capacity) if capacity else 0.0


def recalculate_score(disaster):
    result = calculate_priority(disaster.severity, disaster.affected_population, get_shortage_ratio(disaster))
    disaster.severity_component = result["severity_component"]
    disaster.population_component = result["population_component"]
    disaster.shortage_component = result["shortage_component"]
    disaster.priority_score = result["priority_score"]
    disaster.priority_category = result["priority_category"]
    return result


def validate_incident_form(form):
    errors = []
    title = form.get("title", "").strip()
    disaster_type = form.get("disaster_type", "").strip()
    severity = form.get("severity", "")
    try:
        population = int(form.get("affected_population", 0))
    except ValueError:
        population = -1
    try:
        latitude = float(form.get("latitude", 0))
        longitude = float(form.get("longitude", 0))
    except ValueError:
        latitude, longitude = 91, 181
    if not title:
        errors.append("Title is required.")
    if not disaster_type:
        errors.append("Disaster type is required.")
    if severity not in SEVERITY_VALUES:
        errors.append("Choose a valid severity.")
    if population < 0:
        errors.append("Affected population cannot be negative.")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        errors.append("Latitude/longitude values are invalid.")
    return errors, title, disaster_type, severity, population, latitude, longitude


@disasters_bp.route("/")
@login_required
def list_incidents():
    query = Disaster.query
    disaster_type = request.args.get("type", "").strip()
    severity = request.args.get("severity", "").strip()
    status = request.args.get("status", "").strip()
    if disaster_type:
        query = query.filter(Disaster.disaster_type == disaster_type)
    if severity:
        query = query.filter(Disaster.severity == severity)
    if status:
        query = query.filter(Disaster.status == status)
    incidents = query.order_by(Disaster.priority_score.desc(), Disaster.created_at.desc()).all()
    types = [row[0] for row in db.session.query(Disaster.disaster_type).distinct().order_by(Disaster.disaster_type).all()]
    return render_template("disasters/list.html", incidents=incidents, types=types, severities=SEVERITY_VALUES, statuses=STATUS_VALUES)


@disasters_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_incident():
    if request.method == "POST":
        errors, title, disaster_type, severity, population, latitude, longitude = validate_incident_form(request.form)
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("disasters/form.html", incident=None, severities=SEVERITY_VALUES)
        incident = Disaster(
            title=title,
            disaster_type=disaster_type,
            description=request.form.get("description", "").strip(),
            severity=severity,
            affected_population=population,
            latitude=latitude,
            longitude=longitude,
            status="Reported",
            reported_by=current_user().id,
            occurred_at=parse_datetime(request.form.get("occurred_at")),
        )
        db.session.add(incident)
        db.session.flush()
        recalculate_score(incident)
        db.session.add(DisasterStatusHistory(disaster_id=incident.id, changed_by=current_user().id, new_status="Reported", remarks="Incident reported."))
        db.session.add(AuditLog(user_id=current_user().id, action="created", entity_type="disaster", entity_id=incident.id, details=incident.title))
        db.session.commit()
        flash("Disaster incident created successfully.", "success")
        return redirect(url_for("disasters.detail", disaster_id=incident.id))
    return render_template("disasters/form.html", incident=None, severities=SEVERITY_VALUES)


@disasters_bp.route("/<int:disaster_id>")
@login_required
def detail(disaster_id):
    incident = Disaster.query.get_or_404(disaster_id)
    responders = User.query.filter_by(role="responder", is_active=True).order_by(User.full_name).all()
    available_resources = Resource.query.filter(Resource.available_quantity > 0).order_by(Resource.name).all()
    return render_template("disasters/detail.html", incident=incident, responders=responders, statuses=STATUS_VALUES, available_resources_for_page=available_resources)


@disasters_bp.route("/<int:disaster_id>/edit", methods=["GET", "POST"])
@login_required
def edit(disaster_id):
    incident = Disaster.query.get_or_404(disaster_id)
    if request.method == "POST":
        errors, title, disaster_type, severity, population, latitude, longitude = validate_incident_form(request.form)
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("disasters/form.html", incident=incident, severities=SEVERITY_VALUES)
        incident.title = title
        incident.disaster_type = disaster_type
        incident.description = request.form.get("description", "").strip()
        incident.severity = severity
        incident.affected_population = population
        incident.latitude = latitude
        incident.longitude = longitude
        incident.occurred_at = parse_datetime(request.form.get("occurred_at"))
        recalculate_score(incident)
        db.session.add(AuditLog(user_id=current_user().id, action="updated", entity_type="disaster", entity_id=incident.id, details=incident.title))
        db.session.commit()
        flash("Incident updated.", "success")
        return redirect(url_for("disasters.detail", disaster_id=incident.id))
    return render_template("disasters/form.html", incident=incident, severities=SEVERITY_VALUES)


@disasters_bp.route("/<int:disaster_id>/status", methods=["POST"])
@login_required
def update_status(disaster_id):
    incident = Disaster.query.get_or_404(disaster_id)
    new_status = request.form.get("status", "")
    remarks = request.form.get("remarks", "").strip()
    if new_status not in STATUS_VALUES:
        flash("Invalid status.", "danger")
        return redirect(url_for("disasters.detail", disaster_id=disaster_id))
    old_status = incident.status
    if old_status != new_status:
        incident.status = new_status
        db.session.add(DisasterStatusHistory(disaster_id=incident.id, changed_by=current_user().id, old_status=old_status, new_status=new_status, remarks=remarks))
        db.session.add(AuditLog(user_id=current_user().id, action="status_changed", entity_type="disaster", entity_id=incident.id, details=f"{old_status} -> {new_status}"))
        db.session.commit()
        flash("Incident status updated.", "success")
    return redirect(url_for("disasters.detail", disaster_id=disaster_id))


@disasters_bp.route("/<int:disaster_id>/delete", methods=["POST"])
@roles_required("admin")
def delete(disaster_id):
    incident = Disaster.query.get_or_404(disaster_id)
    db.session.delete(incident)
    db.session.commit()
    flash("Incident deleted.", "info")
    return redirect(url_for("disasters.list_incidents"))


@disasters_bp.route("/api/map-data")
@login_required
def map_data():
    incidents = Disaster.query.order_by(Disaster.created_at.desc()).all()
    return jsonify([{
        "id": incident.id,
        "title": incident.title,
        "type": incident.disaster_type,
        "description": incident.description,
        "latitude": float(incident.latitude),
        "longitude": float(incident.longitude),
        "severity": incident.severity,
        "affected_population": incident.affected_population,
        "status": incident.status,
        "priority_score": incident.priority_score,
        "priority_category": incident.priority_category,
    } for incident in incidents])

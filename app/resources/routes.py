from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models import Resource, Response, ResponseResource, Disaster, User, AuditLog
from app.auth.utils import login_required, current_user, roles_required
from app.disasters.routes import recalculate_score


resources_bp = Blueprint("resources", __name__)
RESPONSE_STATUSES = ["Assigned", "In Progress", "Completed"]


def positive_int(value, field_name):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a whole number.")
    if number < 0:
        raise ValueError(f"{field_name} cannot be negative.")
    return number


@resources_bp.route("/")
@login_required
def list_resources():
    resources = Resource.query.order_by(Resource.category, Resource.name).all()
    return render_template("resources/list.html", resources=resources)


@resources_bp.route("/new", methods=["GET", "POST"])
@roles_required("admin")
def create_resource():
    if request.method == "POST":
        try:
            total = positive_int(request.form.get("total_quantity"), "Total quantity")
            available = positive_int(request.form.get("available_quantity"), "Available quantity")
            if available > total:
                raise ValueError("Available quantity cannot exceed total quantity.")
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("resources/form.html", resource=None)
        resource = Resource(
            name=request.form.get("name", "").strip(),
            category=request.form.get("category", "General").strip(),
            total_quantity=total,
            available_quantity=available,
            unit=request.form.get("unit", "units").strip(),
            location_name=request.form.get("location_name", "").strip(),
            status="Available",
        )
        if not resource.name or not resource.location_name:
            flash("Name and location are required.", "danger")
            return render_template("resources/form.html", resource=None)
        resource.sync_status()
        db.session.add(resource)
        db.session.commit()
        flash("Resource added.", "success")
        return redirect(url_for("resources.list_resources"))
    return render_template("resources/form.html", resource=None)


@resources_bp.route("/<int:resource_id>/edit", methods=["GET", "POST"])
@roles_required("admin")
def edit_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    if request.method == "POST":
        try:
            total = positive_int(request.form.get("total_quantity"), "Total quantity")
            available = positive_int(request.form.get("available_quantity"), "Available quantity")
            if available > total:
                raise ValueError("Available quantity cannot exceed total quantity.")
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("resources/form.html", resource=resource)
        resource.name = request.form.get("name", "").strip()
        resource.category = request.form.get("category", "General").strip()
        resource.total_quantity = total
        resource.available_quantity = available
        resource.unit = request.form.get("unit", "units").strip()
        resource.location_name = request.form.get("location_name", "").strip()
        resource.sync_status()
        db.session.commit()
        flash("Resource updated.", "success")
        return redirect(url_for("resources.list_resources"))
    return render_template("resources/form.html", resource=resource)


@resources_bp.route("/responses/<int:response_id>/status", methods=["POST"])
@login_required
def update_response_status(response_id):
    response = Response.query.get_or_404(response_id)
    new_status = request.form.get("status", "")
    if new_status not in RESPONSE_STATUSES:
        flash("Invalid response status.", "danger")
        return redirect(url_for("disasters.detail", disaster_id=response.disaster_id))
    response.status = new_status
    if new_status == "In Progress" and not response.started_at:
        response.started_at = datetime.utcnow()
    if new_status == "Completed" and not response.completed_at:
        response.completed_at = datetime.utcnow()
    db.session.commit()
    flash("Response status updated.", "success")
    return redirect(url_for("disasters.detail", disaster_id=response.disaster_id))


@resources_bp.route("/disasters/<int:disaster_id>/assign", methods=["POST"])
@login_required
def assign_responder(disaster_id):
    disaster = Disaster.query.get_or_404(disaster_id)
    try:
        responder_id = int(request.form.get("responder_id"))
    except (TypeError, ValueError):
        flash("Choose a responder.", "danger")
        return redirect(url_for("disasters.detail", disaster_id=disaster_id))
    responder = User.query.filter_by(id=responder_id, role="responder", is_active=True).first()
    if not responder:
        flash("The selected responder is not valid.", "danger")
        return redirect(url_for("disasters.detail", disaster_id=disaster_id))
    response = Response(disaster_id=disaster.id, responder_id=responder.id, status="Assigned", notes=request.form.get("notes", "").strip())
    disaster.status = "Responding" if disaster.status == "Reported" else disaster.status
    db.session.add(response)
    db.session.add(AuditLog(user_id=current_user().id, action="assigned_responder", entity_type="disaster", entity_id=disaster.id, details=responder.full_name))
    db.session.commit()
    flash(f"{responder.full_name} assigned to the incident.", "success")
    return redirect(url_for("disasters.detail", disaster_id=disaster_id))


@resources_bp.route("/responses/<int:response_id>/allocate", methods=["POST"])
@login_required
def allocate_resource(response_id):
    response = Response.query.get_or_404(response_id)
    try:
        resource_id = int(request.form.get("resource_id"))
        quantity = positive_int(request.form.get("quantity"), "Allocation quantity")
        if quantity <= 0:
            raise ValueError("Allocation quantity must be greater than zero.")
    except (TypeError, ValueError) as exc:
        flash(str(exc), "danger")
        return redirect(url_for("disasters.detail", disaster_id=response.disaster_id))

    resource = db.session.get(Resource, resource_id)
    if not resource:
        flash("Resource not found.", "danger")
        return redirect(url_for("disasters.detail", disaster_id=response.disaster_id))
    if quantity > resource.available_quantity:
        flash(f"Allocation rejected: only {resource.available_quantity} {resource.unit} available.", "danger")
        return redirect(url_for("disasters.detail", disaster_id=response.disaster_id))

    allocation = ResponseResource.query.filter_by(response_id=response.id, resource_id=resource.id).first()
    if allocation:
        allocation.quantity_allocated += quantity
    else:
        allocation = ResponseResource(response_id=response.id, resource_id=resource.id, quantity_allocated=quantity)
        db.session.add(allocation)
    resource.available_quantity -= quantity
    if resource.available_quantity < 0:
        db.session.rollback()
        flash("Allocation rejected: resource quantity cannot become negative.", "danger")
        return redirect(url_for("disasters.detail", disaster_id=response.disaster_id))
    resource.sync_status()
    recalculate_score(response.disaster)
    db.session.add(AuditLog(user_id=current_user().id, action="allocated_resource", entity_type="response", entity_id=response.id, details=f"{quantity} {resource.name}"))
    db.session.commit()
    flash(f"Allocated {quantity} {resource.unit} of {resource.name}.", "success")
    return redirect(url_for("disasters.detail", disaster_id=response.disaster_id))

from collections import OrderedDict
import pandas as pd
from flask import Blueprint, jsonify, render_template
from app.auth.utils import login_required
from app.models import Disaster, Response, Resource


analytics_bp = Blueprint("analytics", __name__)


def frame_from_records(records):
    return pd.DataFrame(records)


def build_summary():
    disasters = Disaster.query.order_by(Disaster.occurred_at.asc()).all()
    responses = Response.query.all()
    resources = Resource.query.order_by(Resource.name).all()

    disaster_records = [{
        "type": d.disaster_type,
        "severity": d.severity,
        "status": d.status,
        "occurred_at": d.occurred_at,
        "affected_population": d.affected_population,
    } for d in disasters]
    df = frame_from_records(disaster_records)
    if df.empty:
        df = pd.DataFrame(columns=["type", "severity", "status", "occurred_at", "affected_population"])
    else:
        df["occurred_at"] = pd.to_datetime(df["occurred_at"])
        df["month"] = df["occurred_at"].dt.strftime("%Y-%m")

    def grouped(column):
        if df.empty:
            return {"labels": [], "values": []}
        series = df.groupby(column).size().sort_index()
        return {"labels": series.index.astype(str).tolist(), "values": series.astype(int).tolist()}

    incident_types = grouped("type")
    severity = grouped("severity")
    by_month = grouped("month")
    population_by_month = {"labels": [], "values": []}
    if not df.empty:
        pop = df.groupby("month")["affected_population"].sum().sort_index()
        population_by_month = {"labels": pop.index.astype(str).tolist(), "values": pop.astype(int).tolist()}

    response_records = []
    for response in responses:
        hours = None
        if response.started_at and response.assigned_at:
            hours = round((response.started_at - response.assigned_at).total_seconds() / 3600, 2)
        response_records.append({"status": response.status, "response_hours": hours})
    response_df = frame_from_records(response_records)
    response_status = {"labels": [], "values": []}
    average_response_hours = 0
    if not response_df.empty:
        counts = response_df.groupby("status").size().sort_index()
        response_status = {"labels": counts.index.astype(str).tolist(), "values": counts.astype(int).tolist()}
        valid_hours = pd.to_numeric(response_df["response_hours"], errors="coerce").dropna()
        if not valid_hours.empty:
            average_response_hours = round(float(valid_hours.mean()), 2)

    resource_availability = {"labels": [], "available": [], "total": []}
    resource_utilization = {"labels": [], "values": []}
    if resources:
        rdf = frame_from_records([{
            "name": r.name,
            "available": r.available_quantity,
            "total": r.total_quantity,
            "category": r.category,
        } for r in resources])
        resource_availability = {
            "labels": rdf["name"].tolist(),
            "available": rdf["available"].astype(int).tolist(),
            "total": rdf["total"].astype(int).tolist(),
        }
        category = rdf.groupby("category")[["available", "total"]].sum()
        utilization = ((category["total"] - category["available"]) / category["total"].replace(0, 1) * 100).round(1)
        resource_utilization = {"labels": utilization.index.tolist(), "values": utilization.tolist()}

    unresolved = int((df["status"] != "Resolved").sum()) if not df.empty else 0
    return {
        "incident_types": incident_types,
        "incidents_by_month": by_month,
        "incidents_by_severity": severity,
        "response_status": response_status,
        "resource_availability": resource_availability,
        "resource_utilization": resource_utilization,
        "affected_population_trend": population_by_month,
        "average_response_hours": average_response_hours,
        "unresolved_incidents": unresolved,
    }


@analytics_bp.route("/")
@login_required
def analytics_page():
    return render_template("analytics.html")


@analytics_bp.route("/api/summary")
@login_required
def summary():
    return jsonify(build_summary())

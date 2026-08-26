from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Disaster, Resource, Response, ResponseResource, Alert, DisasterStatusHistory
from app.disasters.routes import recalculate_score


# Run from the project root: python seed\\seed_data.py
app = create_app()


def make_dt(days_ago, hour=9):
    return datetime.utcnow().replace(hour=hour, minute=0, second=0, microsecond=0) - timedelta(days=days_ago)


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        admin = User(full_name="Asha Rao", email="admin@example.com", role="admin")
        admin.set_password("Admin@123")
        responder = User(full_name="Arjun Mehta", email="responder@example.com", role="responder")
        responder.set_password("Responder@123")
        responder2 = User(full_name="Nisha Verma", email="nisha@example.com", role="responder")
        responder2.set_password("Responder@123")
        db.session.add_all([admin, responder, responder2])
        db.session.flush()

        resources = [
            Resource(name="Ambulance", category="Medical", total_quantity=18, available_quantity=12, unit="vehicles", location_name="Central dispatch"),
            Resource(name="Medical Kit", category="Medical", total_quantity=240, available_quantity=175, unit="kits", location_name="Central warehouse"),
            Resource(name="Food Packet", category="Relief", total_quantity=5000, available_quantity=4200, unit="packets", location_name="North relief hub"),
            Resource(name="Water Bottle", category="Relief", total_quantity=8000, available_quantity=6100, unit="bottles", location_name="South relief hub"),
            Resource(name="Rescue Team", category="Personnel", total_quantity=12, available_quantity=7, unit="teams", location_name="Regional command"),
            Resource(name="Temporary Shelter", category="Shelter", total_quantity=450, available_quantity=310, unit="beds", location_name="East logistics centre"),
        ]
        for resource in resources:
            resource.sync_status()
        db.session.add_all(resources)
        db.session.flush()

        incident_data = [
            ("Riverside flood evacuation", "Flood", "Water levels have exceeded the riverbank near Riverside ward. Evacuation support and medical triage are required.", "Critical", 6200, 12.9716, 77.5946, "Responding", 2),
            ("Industrial area fire", "Fire", "A warehouse fire has affected nearby industrial units. Smoke control and first response teams are active.", "High", 850, 19.0760, 72.8777, "Responding", 4),
            ("Coastal storm warning", "Storm", "High winds and heavy rainfall are affecting low-lying coastal communities.", "High", 3100, 13.0827, 80.2707, "Reported", 7),
            ("Landslide on Hill Road", "Landslide", "Road access is blocked after a slope failure. Two settlements need welfare checks.", "Medium", 420, 30.3165, 78.0322, "Responding", 11),
            ("Urban heat emergency", "Heatwave", "Extended high temperatures have increased demand for water and first-aid support.", "Medium", 1800, 28.6139, 77.2090, "Reported", 15),
            ("Earthquake shelter support", "Earthquake", "Aftershocks have displaced residents from older buildings in the eastern district.", "Critical", 4100, 26.8467, 80.9462, "Resolved", 23),
            ("Flash flood in market district", "Flood", "Short-duration rainfall has flooded the market access roads.", "Medium", 690, 17.3850, 78.4867, "Resolved", 31),
            ("Forest fire perimeter", "Fire", "A forest fire is being monitored near the western perimeter. Firebreak support is on standby.", "Low", 120, 11.0168, 76.9558, "Resolved", 40),
        ]
        incidents = []
        for title, dtype, description, severity, population, lat, lon, status, days in incident_data:
            incident = Disaster(title=title, disaster_type=dtype, description=description, severity=severity, affected_population=population, latitude=lat, longitude=lon, status=status, reported_by=admin.id, occurred_at=make_dt(days))
            db.session.add(incident)
            incidents.append(incident)
        db.session.flush()
        for incident in incidents:
            recalculate_score(incident)
            db.session.add(DisasterStatusHistory(disaster_id=incident.id, changed_by=admin.id, new_status="Reported", changed_at=incident.occurred_at, remarks="Initial incident report created."))
            if incident.status != "Reported":
                db.session.add(DisasterStatusHistory(disaster_id=incident.id, changed_by=admin.id, old_status="Reported", new_status=incident.status, changed_at=incident.occurred_at + timedelta(hours=3), remarks="Operational status updated by command."))

        assignments = [
            (incidents[0], responder, "Flood evacuation coordination", [(resources[0], 3), (resources[1], 25), (resources[3], 500), (resources[4], 2)], "In Progress"),
            (incidents[1], responder2, "Industrial fire perimeter support", [(resources[4], 1), (resources[0], 2), (resources[1], 12)], "In Progress"),
            (incidents[3], responder, "Hill Road access and welfare checks", [(resources[4], 1), (resources[5], 20)], "Assigned"),
            (incidents[5], responder2, "Shelter transition support", [(resources[5], 80), (resources[2], 200)], "Completed"),
            (incidents[6], responder, "Market district recovery", [(resources[2], 100), (resources[3], 160)], "Completed"),
        ]
        for incident, assigned_responder, notes, allocations, response_status in assignments:
            response = Response(disaster_id=incident.id, responder_id=assigned_responder.id, status=response_status, assigned_at=incident.occurred_at + timedelta(hours=4), notes=notes)
            if response_status in ("In Progress", "Completed"):
                response.started_at = response.assigned_at + timedelta(hours=1)
            if response_status == "Completed":
                response.completed_at = response.started_at + timedelta(hours=7)
            db.session.add(response)
            db.session.flush()
            for resource, quantity in allocations:
                db.session.add(ResponseResource(response_id=response.id, resource_id=resource.id, quantity_allocated=quantity))
                resource.available_quantity = max(0, resource.available_quantity - quantity)
                resource.sync_status()
            recalculate_score(incident)

        db.session.add_all([
            Alert(disaster_id=incidents[0].id, created_by=admin.id, title="Riverside evacuation support active", message="Prioritize medical kits, water distribution, and shelter coordination for Riverside ward.", severity="Critical", status="Active", created_at=make_dt(1, 8)),
            Alert(disaster_id=incidents[1].id, created_by=admin.id, title="Industrial fire response update", message="Responder teams are maintaining a perimeter. Verify medical kit readiness before redeployment.", severity="High", status="Active", created_at=make_dt(2, 11)),
            Alert(disaster_id=incidents[2].id, created_by=admin.id, title="Coastal storm readiness notice", message="Review low-lying community access plans and confirm water availability.", severity="Medium", status="Active", created_at=make_dt(4, 15)),
        ])
        db.session.commit()
        print("Database seeded successfully.")
        print("Admin: admin@example.com / Admin@123")
        print("Responder: responder@example.com / Responder@123")


if __name__ == "__main__":
    seed()

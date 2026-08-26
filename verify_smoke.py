from app import create_app
from app.extensions import db
from config import TestConfig
from app.models import User, Resource, Disaster, Response


def run():
    app = create_app(TestConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(full_name="Smoke Admin", email="smoke-admin@example.com", role="admin")
        admin.set_password("Admin@123")
        responder = User(full_name="Smoke Responder", email="smoke-responder@example.com", role="responder")
        responder.set_password("Responder@123")
        resource = Resource(name="Smoke Kit", category="Medical", total_quantity=10, available_quantity=10, unit="kits", location_name="Smoke base")
        resource.sync_status()
        db.session.add_all([admin, responder, resource])
        db.session.commit()
        responder_id, resource_id = responder.id, resource.id

    client = app.test_client()
    login = client.post("/auth/login", data={"email": "smoke-admin@example.com", "password": "Admin@123"})
    assert login.status_code == 302
    creation = client.post("/disasters/new", data={
        "title": "Smoke test flood", "disaster_type": "Flood", "description": "Smoke test",
        "severity": "Critical", "affected_population": "6000", "latitude": "12.9",
        "longitude": "77.5", "occurred_at": "2026-01-01T10:00",
    })
    assert creation.status_code == 302
    with app.app_context():
        disaster = Disaster.query.filter_by(title="Smoke test flood").one()
        assert disaster.priority_score == 4.0
        assert disaster.priority_category == "HIGH"
        disaster_id = disaster.id

    assert client.get(f"/disasters/{disaster_id}").status_code == 200
    assignment = client.post(f"/resources/disasters/{disaster_id}/assign", data={"responder_id": responder_id, "notes": "Smoke assignment"})
    assert assignment.status_code == 302
    with app.app_context():
        response_id = Response.query.filter_by(disaster_id=disaster_id).one().id

    accepted = client.post(f"/resources/responses/{response_id}/allocate", data={"resource_id": resource_id, "quantity": "4"})
    assert accepted.status_code == 302
    rejected = client.post(f"/resources/responses/{response_id}/allocate", data={"resource_id": resource_id, "quantity": "7"}, follow_redirects=True)
    assert rejected.status_code == 200
    assert b"allocation rejected" in rejected.data.lower()
    assert client.get("/dashboard").status_code == 200
    assert client.get("/disasters/").status_code == 200
    assert client.get("/disasters/new").status_code == 200
    assert client.get("/resources/").status_code == 200
    assert client.get("/analytics/").status_code == 200
    assert client.get("/alerts/").status_code == 200
    assert client.get("/analytics/api/summary").status_code == 200
    assert client.get("/disasters/api/map-data").status_code == 200
    required_routes = ["auth.login", "main.dashboard", "disasters.create_incident", "resources.allocate_resource", "analytics.summary"]
    route_names = {rule.endpoint for rule in app.url_map.iter_rules()}
    assert all(route in route_names for route in required_routes)
    print("Smoke verification passed: imports, routes, templates, CRUD, score, assignment, allocation, dashboard, analytics, and map.")


if __name__ == "__main__":
    run()

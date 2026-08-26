from app.extensions import db
from app.models import Disaster, Resource, Response, ResponseResource, User
from app.disasters.scoring import calculate_priority
from tests.conftest import login


def test_priority_score_and_category():
    result = calculate_priority("Critical", 6200, 1.0)
    assert result["severity_component"] == 5.0
    assert result["population_component"] == 5.0
    assert result["shortage_component"] == 5.0
    assert result["priority_score"] == 5.0
    assert result["priority_category"] == "CRITICAL"


def test_login_and_logout(client):
    response = login(client)
    assert response.status_code == 200
    assert b"Emergency command dashboard" in response.data
    response = client.get("/auth/logout", follow_redirects=True)
    assert b"Sign in" in response.data


def test_unauthorized_access_redirects_to_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_responder_cannot_manage_resources(app, client):
    login(client, "responder@test.local", "Responder@123")
    response = client.get("/resources/new", follow_redirects=True)
    assert response.status_code == 200
    assert b"not authorized" in response.data.lower()


def test_disaster_creation(client, app):
    login(client)
    response = client.post("/disasters/new", data={
        "title": "Test flood incident",
        "disaster_type": "Flood",
        "description": "Test description",
        "severity": "High",
        "affected_population": "800",
        "latitude": "12.9716",
        "longitude": "77.5946",
        "occurred_at": "2026-01-01T10:00",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Test flood incident" in response.data
    with app.app_context():
        incident = Disaster.query.filter_by(title="Test flood incident").one()
        assert incident.priority_score > 0
        assert incident.status_history[0].new_status == "Reported"


def test_resource_over_allocation_is_rejected(app, client):
    with app.app_context():
        admin = User.query.filter_by(email="admin@test.local").one()
        responder = User.query.filter_by(email="responder@test.local").one()
        disaster = Disaster(title="Allocation test", disaster_type="Fire", description="test", severity="Medium", affected_population=100, latitude=1, longitude=2, status="Reported", reported_by=admin.id)
        resource = Resource(name="Test Kit", category="Medical", total_quantity=5, available_quantity=2, unit="kits", location_name="Test base")
        response = Response(disaster=disaster, responder=responder)
        db.session.add_all([disaster, resource, response])
        db.session.commit()
        response_id = response.id
        resource_id = resource.id
    login(client)
    result = client.post(f"/resources/responses/{response_id}/allocate", data={"resource_id": resource_id, "quantity": "3"}, follow_redirects=True)
    assert result.status_code == 200
    assert b"allocation rejected" in result.data.lower()
    with app.app_context():
        assert db.session.get(Resource, resource_id).available_quantity == 2
        assert ResponseResource.query.count() == 0


def test_dashboard_and_analytics_are_database_backed(client):
    login(client)
    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    summary = client.get("/analytics/api/summary")
    assert summary.status_code == 200
    assert b"incident_types" in summary.data

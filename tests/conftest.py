import pytest
from app import create_app
from app.extensions import db
from config import TestConfig
from app.models import User


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(full_name="Test Admin", email="admin@test.local", role="admin")
        admin.set_password("Admin@123")
        responder = User(full_name="Test Responder", email="responder@test.local", role="responder")
        responder.set_password("Responder@123")
        db.session.add_all([admin, responder])
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email="admin@test.local", password="Admin@123"):
    return client.post("/auth/login", data={"email": email, "password": password}, follow_redirects=True)

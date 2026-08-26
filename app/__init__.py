from flask import Flask
from config import Config
from .extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)

    from .auth.routes import auth_bp
    from .disasters.routes import disasters_bp
    from .resources.routes import resources_bp
    from .analytics.routes import analytics_bp
    from .alerts.routes import alerts_bp
    from .main_routes import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(disasters_bp, url_prefix="/disasters")
    app.register_blueprint(resources_bp, url_prefix="/resources")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(alerts_bp, url_prefix="/alerts")

    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()

    return app

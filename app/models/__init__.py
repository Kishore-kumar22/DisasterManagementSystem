from datetime import datetime, timezone

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="responder", index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    reported_disasters = db.relationship(
        "Disaster",
        back_populates="reporter",
        foreign_keys="Disaster.reported_by",
    )

    responses = db.relationship(
        "Response",
        back_populates="responder",
        foreign_keys="Response.responder_id",
    )

    alerts_created = db.relationship(
        "Alert",
        back_populates="creator",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Disaster(db.Model):
    __tablename__ = "disasters"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    disaster_type = db.Column(db.String(80), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False, default="")
    severity = db.Column(db.String(20), nullable=False, index=True)
    affected_population = db.Column(db.Integer, nullable=False, default=0)

    latitude = db.Column(db.Numeric(10, 7), nullable=False)
    longitude = db.Column(db.Numeric(10, 7), nullable=False)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Reported",
        index=True,
    )

    reported_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    occurred_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utcnow,
        index=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    severity_component = db.Column(
        db.Float,
        nullable=False,
        default=0,
    )

    population_component = db.Column(
        db.Float,
        nullable=False,
        default=0,
    )

    shortage_component = db.Column(
        db.Float,
        nullable=False,
        default=0,
    )

    priority_score = db.Column(
        db.Float,
        nullable=False,
        default=0,
    )

    priority_category = db.Column(
        db.String(20),
        nullable=False,
        default="LOW",
        index=True,
    )

    reporter = db.relationship(
        "User",
        back_populates="reported_disasters",
        foreign_keys=[reported_by],
    )

    responses = db.relationship(
        "Response",
        back_populates="disaster",
        cascade="all, delete-orphan",
    )

    alerts = db.relationship(
        "Alert",
        back_populates="disaster",
        cascade="all, delete-orphan",
    )

    status_history = db.relationship(
        "DisasterStatusHistory",
        back_populates="disaster",
        cascade="all, delete-orphan",
        order_by="DisasterStatusHistory.changed_at.desc()",
    )


class Resource(db.Model):
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(120),
        nullable=False,
    )

    category = db.Column(
        db.String(80),
        nullable=False,
        index=True,
    )

    total_quantity = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    available_quantity = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    unit = db.Column(
        db.String(40),
        nullable=False,
        default="units",
    )

    location_name = db.Column(
        db.String(160),
        nullable=False,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Available",
        index=True,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    allocations = db.relationship(
        "ResponseResource",
        back_populates="resource",
    )

    def sync_status(self):
        if self.available_quantity <= 0:
            self.status = "Depleted"
        elif self.available_quantity <= max(
            1,
            int(self.total_quantity * 0.25),
        ):
            self.status = "Low Stock"
        else:
            self.status = "Available"


class Response(db.Model):
    __tablename__ = "responses"

    id = db.Column(db.Integer, primary_key=True)

    disaster_id = db.Column(
        db.Integer,
        db.ForeignKey("disasters.id"),
        nullable=False,
        index=True,
    )

    responder_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Assigned",
        index=True,
    )

    assigned_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utcnow,
    )

    started_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    notes = db.Column(
        db.Text,
        nullable=False,
        default="",
    )

    disaster = db.relationship(
        "Disaster",
        back_populates="responses",
    )

    responder = db.relationship(
        "User",
        back_populates="responses",
        foreign_keys=[responder_id],
    )

    allocations = db.relationship(
        "ResponseResource",
        back_populates="response",
        cascade="all, delete-orphan",
    )


class ResponseResource(db.Model):
    __tablename__ = "response_resources"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    response_id = db.Column(
        db.Integer,
        db.ForeignKey("responses.id"),
        nullable=False,
        index=True,
    )

    resource_id = db.Column(
        db.Integer,
        db.ForeignKey("resources.id"),
        nullable=False,
        index=True,
    )

    quantity_allocated = db.Column(
        db.Integer,
        nullable=False,
    )

    response = db.relationship(
        "Response",
        back_populates="allocations",
    )

    resource = db.relationship(
        "Resource",
        back_populates="allocations",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "response_id",
            "resource_id",
            name="uq_response_resource",
        ),
    )


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    disaster_id = db.Column(
        db.Integer,
        db.ForeignKey("disasters.id"),
        nullable=False,
        index=True,
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    title = db.Column(
        db.String(180),
        nullable=False,
    )

    message = db.Column(
        db.Text,
        nullable=False,
    )

    severity = db.Column(
        db.String(20),
        nullable=False,
        default="Medium",
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Active",
        index=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utcnow,
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    disaster = db.relationship(
        "Disaster",
        back_populates="alerts",
    )

    creator = db.relationship(
        "User",
        back_populates="alerts_created",
    )


class DisasterStatusHistory(db.Model):
    __tablename__ = "disaster_status_history"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    disaster_id = db.Column(
        db.Integer,
        db.ForeignKey("disasters.id"),
        nullable=False,
        index=True,
    )

    changed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    old_status = db.Column(
        db.String(20),
        nullable=True,
    )

    new_status = db.Column(
        db.String(20),
        nullable=False,
    )

    changed_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utcnow,
    )

    remarks = db.Column(
        db.Text,
        nullable=False,
        default="",
    )

    disaster = db.relationship(
        "Disaster",
        back_populates="status_history",
    )

    user = db.relationship("User")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
    )

    action = db.Column(
        db.String(120),
        nullable=False,
    )

    entity_type = db.Column(
        db.String(80),
        nullable=False,
    )

    entity_id = db.Column(
        db.Integer,
        nullable=True,
    )

    details = db.Column(
        db.Text,
        nullable=False,
        default="",
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utcnow,
    )

    user = db.relationship("User")


class Shelter(db.Model):
    __tablename__ = "shelters"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.String(160),
        nullable=False,
    )

    location = db.Column(
        db.String(200),
        nullable=False,
    )

    capacity = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    occupied = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    contact = db.Column(
        db.String(120),
        nullable=False,
        default="",
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Available",
        index=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utcnow,
    )

    @property
    def available_spaces(self):
        return max(
            0,
            self.capacity - self.occupied,
        )

    def sync_status(self):
        if self.occupied >= self.capacity:
            self.status = "Full"
        elif self.occupied >= self.capacity * 0.8:
            self.status = "Nearly Full"
        else:
            self.status = "Available"
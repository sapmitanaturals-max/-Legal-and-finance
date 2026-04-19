from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from . import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Organization(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    country = db.Column(db.String(60), nullable=False, default="CA")
    currency = db.Column(db.String(10), nullable=False, default="CAD")


class Role(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    permissions = db.Column(db.String(500), nullable=False, default="")

    def has(self, permission: str) -> bool:
        permission_set = {p.strip() for p in self.permissions.split(",") if p.strip()}
        return permission in permission_set


class User(UserMixin, TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    organization = db.relationship("Organization", backref="users")
    role = db.relationship("Role", backref="users")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def can(self, permission: str) -> bool:
        return self.role.has(permission)


class SubscriptionPlan(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    monthly_price = db.Column(db.Float, nullable=False)
    yearly_price = db.Column(db.Float, nullable=False)
    features = db.Column(db.Text, nullable=False, default="")


class OrganizationSubscription(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("subscription_plan.id"), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="active")
    starts_on = db.Column(db.Date, nullable=False)
    ends_on = db.Column(db.Date, nullable=True)
    renews_automatically = db.Column(db.Boolean, default=True)

    organization = db.relationship("Organization", backref="subscriptions")
    plan = db.relationship("SubscriptionPlan", backref="subscriptions")


class TaxProfile(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False, unique=True)
    gst_number = db.Column(db.String(60), nullable=True)
    pst_number = db.Column(db.String(60), nullable=True)
    hst_number = db.Column(db.String(60), nullable=True)
    filing_frequency = db.Column(db.String(20), nullable=False, default="monthly")

    organization = db.relationship("Organization", backref="tax_profile", uselist=False)


class Invoice(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)
    customer_name = db.Column(db.String(120), nullable=False)
    amount_subtotal = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, nullable=False)
    amount_total = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="CAD")
    status = db.Column(db.String(20), nullable=False, default="draft")
    issued_on = db.Column(db.Date, nullable=False)

    organization = db.relationship("Organization", backref="invoices")


class LedgerEntry(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)
    entry_type = db.Column(db.String(30), nullable=False)  # expense/income/adjustment
    category = db.Column(db.String(60), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    posted_on = db.Column(db.Date, nullable=False)

    organization = db.relationship("Organization", backref="ledger_entries")


class AuditLog(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    entity = db.Column(db.String(120), nullable=False)
    metadata = db.Column(db.Text, nullable=True)

    organization = db.relationship("Organization", backref="audit_logs")
    user = db.relationship("User", backref="audit_logs")

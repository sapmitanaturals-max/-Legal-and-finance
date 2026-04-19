from datetime import date

from . import db
from .models import (
    Organization,
    Role,
    User,
    SubscriptionPlan,
    OrganizationSubscription,
    TaxProfile,
)


def seed_data() -> None:
    if Role.query.count() == 0:
        roles = [
            Role(name="owner", permissions="manage_users,manage_billing,manage_books,view_dashboard"),
            Role(name="accountant", permissions="manage_books,view_dashboard,view_audit"),
            Role(name="auditor", permissions="view_dashboard,view_audit"),
            Role(name="member", permissions="view_dashboard"),
        ]
        db.session.add_all(roles)
        db.session.commit()

    if SubscriptionPlan.query.count() == 0:
        db.session.add_all(
            [
                SubscriptionPlan(
                    code="starter",
                    name="Starter",
                    monthly_price=49,
                    yearly_price=490,
                    features="1 entity, basic bookkeeping, GST tracking",
                ),
                SubscriptionPlan(
                    code="growth",
                    name="Growth",
                    monthly_price=149,
                    yearly_price=1490,
                    features="5 entities, advanced reporting, audit logs",
                ),
                SubscriptionPlan(
                    code="enterprise",
                    name="Enterprise",
                    monthly_price=499,
                    yearly_price=4990,
                    features="unlimited entities, SSO, API, custom tax engine",
                ),
            ]
        )
        db.session.commit()

    if Organization.query.count() == 0:
        org = Organization(name="Demo Legal & Finance", country="CA", currency="CAD")
        db.session.add(org)
        db.session.commit()

        owner_role = Role.query.filter_by(name="owner").first()
        admin = User(
            full_name="System Owner",
            email="owner@example.com",
            organization_id=org.id,
            role_id=owner_role.id,
        )
        admin.set_password("ChangeMe123!")
        db.session.add(admin)

        starter_plan = SubscriptionPlan.query.filter_by(code="growth").first()
        sub = OrganizationSubscription(
            organization_id=org.id,
            plan_id=starter_plan.id,
            status="active",
            starts_on=date.today(),
        )
        db.session.add(sub)

        tax_profile = TaxProfile(
            organization_id=org.id,
            gst_number="GST-DEMO-001",
            filing_frequency="monthly",
        )
        db.session.add(tax_profile)
        db.session.commit()

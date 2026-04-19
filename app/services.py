from functools import wraps
from datetime import date

from flask import abort
from flask_login import current_user

from . import db
from .models import AuditLog, Invoice


def require_permission(permission: str):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.can(permission):
                abort(403)
            return fn(*args, **kwargs)

        return wrapped

    return decorator


def add_audit(action: str, entity: str, metadata: str = "") -> None:
    if not current_user.is_authenticated:
        return
    log = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=action,
        entity=entity,
        metadata=metadata,
    )
    db.session.add(log)
    db.session.commit()


def compute_invoice_total(subtotal: float, tax_percent: float) -> tuple[float, float]:
    tax_amount = round((subtotal * tax_percent) / 100, 2)
    total = round(subtotal + tax_amount, 2)
    return tax_amount, total


def kpi_for_org(org_id: int) -> dict:
    invoices = Invoice.query.filter_by(organization_id=org_id).all()
    revenue = sum(i.amount_total for i in invoices if i.status == "paid")
    receivables = sum(i.amount_total for i in invoices if i.status != "paid")
    return {
        "today": date.today().isoformat(),
        "invoice_count": len(invoices),
        "revenue": round(revenue, 2),
        "receivables": round(receivables, 2),
    }

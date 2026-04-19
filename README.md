# Legal & Finance SaaS Platform (Canada-first, Global-ready)

Production-ready starter SaaS application for legal/finance operations with:

- Multi-user tenancy (organization-based)
- Role-based access control (Owner, Accountant, Auditor, Member)
- Subscription and plan management
- Dashboard with KPI summary
- Bookkeeping ledgers and invoice management
- Tax profile (GST/PST/HST + filing frequency)
- Audit logging for compliance workflows
- Expandable architecture (modular services, models, routes)

## Tech Stack

- Python 3.11+
- Flask + SQLAlchemy
- SQLite (default; switchable to PostgreSQL/MySQL)
- Server-rendered HTML for quick admin usability

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Then open:

- `http://127.0.0.1:5000/bootstrap` (seed demo data once)
- `http://127.0.0.1:5000/login`

Demo login:

- Email: `owner@example.com`
- Password: `ChangeMe123!`

## SaaS Modules

### 1) Multi-user Role System

- Users belong to an `Organization`
- Roles define comma-separated permissions and are enforced by decorators:
  - `manage_users`
  - `manage_billing`
  - `manage_books`
  - `view_dashboard`
  - `view_audit`

### 2) Subscription System

- Define plans (`starter`, `growth`, `enterprise`)
- Assign current organization plan
- Keep history in `OrganizationSubscription`

### 3) Dashboard

- Revenue, receivables, invoice count KPI
- Recent bookkeeping and invoices
- Current subscription summary

### 4) Tax & Bookkeeping

- Track GST/PST/HST numbers and filing frequency
- Create invoices with tax computation
- Maintain ledger entries for income/expense/adjustment

### 5) Auditing

- All key actions recorded in `AuditLog`
- Auditor role can inspect activity by tenant

## Architecture & Extensibility

- `app/models.py`: persistent domain entities
- `app/services.py`: reusable business logic (RBAC, KPIs, tax calculations, auditing)
- `app/routes.py`: HTTP controllers and API endpoint (`/api/v1/dashboard`)
- `app/seed.py`: reusable bootstrap fixtures

For enterprise scale:

- Replace SQLite with managed PostgreSQL
- Add migration tooling (`alembic`)
- Add job queues for invoice reminders/reconciliations
- Add SSO and external payment provider (Stripe/Paddle)
- Add external tax API integrations per country

## Security Notes

Before production:

1. Change `SECRET_KEY`
2. Enforce HTTPS + secure session cookies
3. Rotate demo credentials and add password policy
4. Add rate limiting + CSRF protection
5. Add backups and retention policy for audit records

## License

You can adapt this project as your internal SaaS foundation.

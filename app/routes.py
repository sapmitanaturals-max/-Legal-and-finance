from datetime import date

from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from . import db
from .models import User, Role, Invoice, LedgerEntry, TaxProfile, OrganizationSubscription, SubscriptionPlan, Organization
from .seed import seed_data
from .services import require_permission, add_audit, compute_invoice_total, kpi_for_org


def register_routes(app):
    @app.get("/")
    def home():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email, is_active=True).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for("dashboard"))
            flash("Invalid credentials", "danger")
        return render_template("login.html")

    @app.get("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    @app.get("/bootstrap")
    def bootstrap():
        seed_data()
        return "Seeded successfully"

    @app.get("/dashboard")
    @login_required
    def dashboard():
        org_id = current_user.organization_id
        kpi = kpi_for_org(org_id)
        subscriptions = OrganizationSubscription.query.filter_by(organization_id=org_id).all()
        latest_sub = subscriptions[-1] if subscriptions else None
        entries = LedgerEntry.query.filter_by(organization_id=org_id).order_by(LedgerEntry.posted_on.desc()).limit(10)
        invoices = Invoice.query.filter_by(organization_id=org_id).order_by(Invoice.issued_on.desc()).limit(10)
        return render_template(
            "dashboard.html",
            kpi=kpi,
            subscription=latest_sub,
            entries=entries,
            invoices=invoices,
        )

    @app.route("/users", methods=["GET", "POST"])
    @login_required
    @require_permission("manage_users")
    def users():
        org_id = current_user.organization_id
        roles = Role.query.all()
        if request.method == "POST":
            user = User(
                full_name=request.form["full_name"],
                email=request.form["email"].lower().strip(),
                organization_id=org_id,
                role_id=int(request.form["role_id"]),
            )
            user.set_password(request.form["password"])
            db.session.add(user)
            db.session.commit()
            add_audit("create", "user", f"user_id={user.id}")
            flash("User added", "success")
            return redirect(url_for("users"))

        org_users = User.query.filter_by(organization_id=org_id).all()
        return render_template("users.html", users=org_users, roles=roles)

    @app.route("/subscriptions", methods=["GET", "POST"])
    @login_required
    @require_permission("manage_billing")
    def subscriptions():
        org_id = current_user.organization_id
        plans = SubscriptionPlan.query.all()
        if request.method == "POST":
            chosen_plan = int(request.form["plan_id"])
            sub = OrganizationSubscription(
                organization_id=org_id,
                plan_id=chosen_plan,
                status="active",
                starts_on=date.today(),
                renews_automatically=True,
            )
            db.session.add(sub)
            db.session.commit()
            add_audit("create", "subscription", f"plan_id={chosen_plan}")
            flash("Subscription updated", "success")
            return redirect(url_for("subscriptions"))

        current = OrganizationSubscription.query.filter_by(organization_id=org_id).order_by(OrganizationSubscription.id.desc()).first()
        return render_template("subscriptions.html", current=current, plans=plans)

    @app.route("/bookkeeping", methods=["GET", "POST"])
    @login_required
    @require_permission("manage_books")
    def bookkeeping():
        org_id = current_user.organization_id
        if request.method == "POST":
            entry = LedgerEntry(
                organization_id=org_id,
                entry_type=request.form["entry_type"],
                category=request.form["category"],
                description=request.form["description"],
                amount=float(request.form["amount"]),
                posted_on=date.fromisoformat(request.form["posted_on"]),
            )
            db.session.add(entry)
            db.session.commit()
            add_audit("create", "ledger_entry", f"entry_id={entry.id}")
            flash("Entry posted", "success")
            return redirect(url_for("bookkeeping"))

        entries = LedgerEntry.query.filter_by(organization_id=org_id).order_by(LedgerEntry.posted_on.desc()).all()
        return render_template("bookkeeping.html", entries=entries)

    @app.route("/invoices", methods=["GET", "POST"])
    @login_required
    @require_permission("manage_books")
    def invoices():
        org_id = current_user.organization_id
        if request.method == "POST":
            subtotal = float(request.form["amount_subtotal"])
            tax_percent = float(request.form["tax_percent"])
            tax_amount, total = compute_invoice_total(subtotal, tax_percent)

            invoice = Invoice(
                organization_id=org_id,
                customer_name=request.form["customer_name"],
                amount_subtotal=subtotal,
                tax_amount=tax_amount,
                amount_total=total,
                status=request.form.get("status", "draft"),
                issued_on=date.fromisoformat(request.form["issued_on"]),
            )
            db.session.add(invoice)
            db.session.commit()
            add_audit("create", "invoice", f"invoice_id={invoice.id}")
            flash("Invoice saved", "success")
            return redirect(url_for("invoices"))

        invoice_list = Invoice.query.filter_by(organization_id=org_id).order_by(Invoice.issued_on.desc()).all()
        return render_template("invoices.html", invoices=invoice_list)

    @app.route("/tax", methods=["GET", "POST"])
    @login_required
    @require_permission("manage_books")
    def tax():
        org_id = current_user.organization_id
        profile = TaxProfile.query.filter_by(organization_id=org_id).first()

        if request.method == "POST":
            if profile is None:
                profile = TaxProfile(organization_id=org_id)
                db.session.add(profile)

            profile.gst_number = request.form.get("gst_number", "")
            profile.pst_number = request.form.get("pst_number", "")
            profile.hst_number = request.form.get("hst_number", "")
            profile.filing_frequency = request.form.get("filing_frequency", "monthly")
            db.session.commit()
            add_audit("update", "tax_profile", f"org_id={org_id}")
            flash("Tax profile saved", "success")
            return redirect(url_for("tax"))

        return render_template("tax.html", profile=profile)

    @app.get("/audit")
    @login_required
    @require_permission("view_audit")
    def audit():
        logs = current_user.audit_logs
        org_logs = [x for x in logs if x.organization_id == current_user.organization_id]
        org_logs.sort(key=lambda x: x.created_at, reverse=True)
        return render_template("audit.html", logs=org_logs)

    @app.get("/api/v1/dashboard")
    @login_required
    def dashboard_api():
        data = kpi_for_org(current_user.organization_id)
        org = Organization.query.get(current_user.organization_id)
        return jsonify({"organization": org.name, "kpi": data})

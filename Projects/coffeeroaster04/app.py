import os
import secrets
import uuid
from datetime import datetime
from functools import wraps

from flask import Flask, abort, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import calculations as calc
from data_persistence import (
    load_roast_profiles,
    load_roast_records,
    load_users,
    save_roast_profiles,
    save_roast_records,
    save_users,
)
from validators import (
    validate_bean_name,
    validate_date,
    validate_email,
    validate_finished_weight,
    validate_first_crack,
    validate_green_weight,
    validate_password,
    validate_profile_name,
    validate_roast_time,
    validate_temperature,
)

ROAST_TABLE_COLUMNS = [
    "Date",
    "Bean Name",
    "Roast Profile",
    "Green (g)",
    "Finished (g)",
    "Roast Time",
    "1st Crack",
    "Weight Loss (%)",
    "Dev Time",
    "Classification",
]

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)


def format_mm_ss(total_seconds):
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"

roast_records = load_roast_records()
roast_profiles = load_roast_profiles()
users = load_users()


def sorted_profiles():
    owned = {
        profile_id: profile
        for profile_id, profile in roast_profiles.items()
        if profile.get("owner") == session.get("user_email")
    }
    return sorted(
        owned.items(),
        key=lambda item: (not item[1].get("favorite", False), item[1]["name"].lower()),
    )


def _is_safe_next(next_url):
    return bool(next_url) and next_url.startswith("/") and not next_url.startswith("//")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_email" not in session:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@app.route("/signup", methods=["GET", "POST"])
def signup():
    values = {"email": ""}
    error = None
    next_url = request.values.get("next", "")

    if request.method == "POST":
        values["email"] = request.form.get("email", "")
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        next_url = request.form.get("next", "")

        try:
            email = validate_email(values["email"])
            validate_password(password)
            if password != confirm:
                raise ValueError("Passwords do not match.")
            if email in users:
                raise ValueError("An account with this email already exists.")
        except ValueError as exc:
            error = str(exc)
        else:
            is_first_account = not users
            users[email] = {
                "password_hash": generate_password_hash(password),
                "created_at": datetime.now().isoformat(),
            }
            save_users(users)

            if is_first_account:
                migrated = False
                for record in roast_records.values():
                    if "owner" not in record:
                        record["owner"] = email
                        migrated = True
                for profile in roast_profiles.values():
                    if "owner" not in profile:
                        profile["owner"] = email
                        migrated = True
                if migrated:
                    save_roast_records(roast_records)
                    save_roast_profiles(roast_profiles)

            session["user_email"] = email
            return redirect(next_url if _is_safe_next(next_url) else url_for("home"))

    return render_template("signup.html", values=values, error=error, next=next_url)


@app.route("/login", methods=["GET", "POST"])
def login():
    values = {"email": ""}
    error = None
    next_url = request.values.get("next", "")

    if request.method == "POST":
        values["email"] = request.form.get("email", "")
        password = request.form.get("password", "")
        next_url = request.form.get("next", "")

        email = values["email"].strip().lower()
        user = users.get(email)
        if user is None or not check_password_hash(user["password_hash"], password):
            error = "Invalid email or password."
        else:
            session["user_email"] = email
            return redirect(next_url if _is_safe_next(next_url) else url_for("home"))

    return render_template("login.html", values=values, error=error, next=next_url)


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_email", None)
    return redirect(url_for("home"))


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/roasts")
@login_required
def view_roasts():
    rows = []
    for record_id, record in roast_records.items():
        if record.get("owner") != session["user_email"]:
            continue
        weight_loss = calc.calculate_weight_loss(
            record["green_weight"], record["finished_weight"]
        )
        development_time = calc.calculate_development_time(
            record["total_roast_time"], record["time_of_first_crack"]
        )
        profile = roast_profiles.get(record.get("roast_profile_id"))
        classification = calc.classify_roast(weight_loss)
        rows.append(
            {
                "id": record_id,
                "date": record["date"],
                "bean_name": record["bean_name"],
                "profile_name": profile["name"] if profile else "-",
                "green_weight": record["green_weight"],
                "finished_weight": record["finished_weight"],
                "total_roast_time": format_mm_ss(record["total_roast_time"]),
                "time_of_first_crack": format_mm_ss(record["time_of_first_crack"]),
                "weight_loss": weight_loss,
                "development_time": format_mm_ss(development_time),
                "classification": classification,
                "classification_class": classification.lower().replace(" ", "-"),
            }
        )
    return render_template("roasts.html", columns=ROAST_TABLE_COLUMNS, rows=rows)


@app.route("/roasts/<record_id>")
@login_required
def roast_detail(record_id):
    record = roast_records.get(record_id)
    if record is None or record.get("owner") != session["user_email"]:
        abort(404)

    minutes = list(range(1, 13))
    target_temps = record.get("target_temps") or [None] * 12
    actual_temps = record.get("actual_temps") or [None] * 12
    profile = roast_profiles.get(record.get("roast_profile_id"))

    return render_template(
        "roast_detail.html",
        record=record,
        record_id=record_id,
        profile_name=profile["name"] if profile else "-",
        minutes=minutes,
        target_temps=target_temps,
        actual_temps=actual_temps,
    )


@app.route("/roasts/new")
@login_required
def select_profile():
    return render_template("select_profile.html", profiles=sorted_profiles())


@app.route("/roasts/new/<profile_id>", methods=["GET", "POST"])
@login_required
def add_roast(profile_id):
    profile = roast_profiles.get(profile_id)
    if profile is None or profile.get("owner") != session["user_email"]:
        abort(404)

    minutes = list(range(1, 13))
    target_temps = calc.fill_forward(profile.get("temps", [None] * 12))
    values = {
        "date": "",
        "bean_name": "",
        "green_weight": "",
        "actual_temps": [""] * 12,
        "first_crack": "",
        "roast_time": "",
        "finished_weight": "",
    }
    error = None

    if request.method == "POST":
        values["date"] = request.form.get("date", "")
        values["bean_name"] = request.form.get("bean_name", "")
        values["green_weight"] = request.form.get("green_weight", "")
        values["actual_temps"] = [
            request.form.get(f"actual_temp_{minute}", "") for minute in minutes
        ]
        values["first_crack"] = request.form.get("first_crack", "")
        values["roast_time"] = request.form.get("roast_time", "")
        values["finished_weight"] = request.form.get("finished_weight", "")

        try:
            date = validate_date(values["date"])
            bean_name = validate_bean_name(values["bean_name"])
            green_weight = validate_green_weight(values["green_weight"])
            entered_actual_temps = [
                validate_temperature(value) for value in values["actual_temps"]
            ]
            total_roast_time = validate_roast_time(values["roast_time"])
            time_of_first_crack = validate_first_crack(
                values["first_crack"], total_roast_time
            )
            finished_weight = validate_finished_weight(
                values["finished_weight"], green_weight
            )
        except ValueError as exc:
            error = str(exc)
        else:
            actual_temps = calc.resolve_actual_temps(
                entered_actual_temps, total_roast_time
            )
            record_id = str(uuid.uuid4())
            roast_records[record_id] = {
                "date": date,
                "bean_name": bean_name,
                "green_weight": green_weight,
                "finished_weight": finished_weight,
                "total_roast_time": total_roast_time,
                "time_of_first_crack": time_of_first_crack,
                "roast_profile_id": profile_id,
                "target_temps": target_temps,
                "actual_temps": actual_temps,
                "owner": session["user_email"],
            }
            save_roast_records(roast_records)
            return redirect(url_for("roast_detail", record_id=record_id))

    return render_template(
        "add_roast.html",
        profile=profile,
        profile_id=profile_id,
        minutes=minutes,
        target_temps=target_temps,
        values=values,
        error=error,
    )


@app.route("/profiles")
@login_required
def list_profiles():
    return render_template("profiles.html", profiles=sorted_profiles())


@app.route("/profiles/<profile_id>/favorite", methods=["POST"])
@login_required
def toggle_profile_favorite(profile_id):
    profile = roast_profiles.get(profile_id)
    if profile is None or profile.get("owner") != session["user_email"]:
        abort(404)

    profile["favorite"] = not profile.get("favorite", False)
    save_roast_profiles(roast_profiles)

    next_url = request.form.get("next")
    safe_targets = {url_for("list_profiles"), url_for("select_profile")}
    if next_url in safe_targets:
        return redirect(next_url)
    return redirect(url_for("list_profiles"))


@app.route("/profiles/new", methods=["GET", "POST"])
@app.route("/profiles/<profile_id>", methods=["GET", "POST"])
@login_required
def add_edit_profile(profile_id=None):
    existing_profile = None
    if profile_id is not None:
        existing_profile = roast_profiles.get(profile_id)
        if existing_profile is None or existing_profile.get("owner") != session["user_email"]:
            abort(404)

    minutes = list(range(1, 13))
    existing_temps = existing_profile["temps"] if existing_profile else [None] * 12
    values = {
        "name": existing_profile["name"] if existing_profile else "",
        "temps": ["" if temp is None else str(temp) for temp in existing_temps],
    }
    error = None

    if request.method == "POST":
        values["name"] = request.form.get("name", "")
        values["temps"] = [
            request.form.get(f"temp_{minute}", "") for minute in minutes
        ]

        try:
            name = validate_profile_name(values["name"])
            temps = [validate_temperature(value) for value in values["temps"]]
        except ValueError as exc:
            error = str(exc)
        else:
            saved_profile_id = profile_id or str(uuid.uuid4())
            favorite = existing_profile.get("favorite", False) if existing_profile else False
            owner = existing_profile["owner"] if existing_profile else session["user_email"]
            roast_profiles[saved_profile_id] = {
                "name": name,
                "temps": temps,
                "favorite": favorite,
                "owner": owner,
            }
            save_roast_profiles(roast_profiles)
            return redirect(url_for("list_profiles"))

    return render_template(
        "profile_form.html",
        profile_id=profile_id,
        minutes=minutes,
        values=values,
        error=error,
    )


@app.route("/roasts/<record_id>/delete", methods=["GET", "POST"])
@login_required
def delete_roast(record_id):
    record = roast_records.get(record_id)
    if record is None or record.get("owner") != session["user_email"]:
        abort(404)

    if request.method == "POST":
        del roast_records[record_id]
        save_roast_records(roast_records)
        return redirect(url_for("view_roasts"))

    return render_template(
        "delete_roast_confirm.html", record=record, record_id=record_id
    )


@app.route("/profiles/<profile_id>/delete", methods=["GET", "POST"])
@login_required
def delete_profile(profile_id):
    profile = roast_profiles.get(profile_id)
    if profile is None or profile.get("owner") != session["user_email"]:
        abort(404)

    if request.method == "POST":
        del roast_profiles[profile_id]
        save_roast_profiles(roast_profiles)
        return redirect(url_for("list_profiles"))

    referencing_roast_count = sum(
        1
        for record in roast_records.values()
        if record.get("roast_profile_id") == profile_id
    )
    return render_template(
        "delete_profile_confirm.html",
        profile=profile,
        referencing_roast_count=referencing_roast_count,
    )


def main():
    app.run(debug=True, host="0.0.0.0")


if __name__ == "__main__":
    main()

import uuid

from flask import Flask, abort, redirect, render_template, request, url_for

import calculations as calc
from data_persistence import (
    load_roast_profiles,
    load_roast_records,
    save_roast_profiles,
    save_roast_records,
)
from validators import (
    validate_bean_name,
    validate_date,
    validate_finished_weight,
    validate_first_crack,
    validate_green_weight,
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
    "Roast Time (s)",
    "1st Crack (s)",
    "Weight Loss (%)",
    "Dev Time (s)",
    "Classification",
]

app = Flask(__name__)

roast_records = load_roast_records()
roast_profiles = load_roast_profiles()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/roasts")
def view_roasts():
    rows = []
    for record_id, record in roast_records.items():
        weight_loss = calc.calculate_weight_loss(
            record["green_weight"], record["finished_weight"]
        )
        development_time = calc.calculate_development_time(
            record["total_roast_time"], record["time_of_first_crack"]
        )
        profile = roast_profiles.get(record.get("roast_profile_id"))
        rows.append(
            {
                "id": record_id,
                "date": record["date"],
                "bean_name": record["bean_name"],
                "profile_name": profile["name"] if profile else "-",
                "green_weight": record["green_weight"],
                "finished_weight": record["finished_weight"],
                "total_roast_time": record["total_roast_time"],
                "time_of_first_crack": record["time_of_first_crack"],
                "weight_loss": weight_loss,
                "development_time": development_time,
                "classification": calc.classify_roast(weight_loss),
            }
        )
    return render_template("roasts.html", columns=ROAST_TABLE_COLUMNS, rows=rows)


@app.route("/roasts/<record_id>")
def roast_detail(record_id):
    record = roast_records.get(record_id)
    if record is None:
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
def select_profile():
    return render_template("select_profile.html", profiles=roast_profiles)


@app.route("/roasts/new/<profile_id>", methods=["GET", "POST"])
def add_roast(profile_id):
    profile = roast_profiles.get(profile_id)
    if profile is None:
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
def list_profiles():
    return render_template("profiles.html", profiles=roast_profiles)


@app.route("/profiles/new", methods=["GET", "POST"])
@app.route("/profiles/<profile_id>", methods=["GET", "POST"])
def add_edit_profile(profile_id=None):
    existing_profile = None
    if profile_id is not None:
        existing_profile = roast_profiles.get(profile_id)
        if existing_profile is None:
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
            roast_profiles[saved_profile_id] = {"name": name, "temps": temps}
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
def delete_roast(record_id):
    record = roast_records.get(record_id)
    if record is None:
        abort(404)

    if request.method == "POST":
        del roast_records[record_id]
        save_roast_records(roast_records)
        return redirect(url_for("view_roasts"))

    return render_template(
        "delete_roast_confirm.html", record=record, record_id=record_id
    )


@app.route("/profiles/<profile_id>/delete", methods=["GET", "POST"])
def delete_profile(profile_id):
    profile = roast_profiles.get(profile_id)
    if profile is None:
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
    app.run(debug=True)


if __name__ == "__main__":
    main()

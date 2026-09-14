from flask import Flask, abort, render_template

import calculations as calc
from data_persistence import load_roast_profiles, load_roast_records

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
        profile_name=profile["name"] if profile else "-",
        minutes=minutes,
        target_temps=target_temps,
        actual_temps=actual_temps,
    )


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()

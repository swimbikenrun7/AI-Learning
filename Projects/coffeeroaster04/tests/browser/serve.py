"""Test server for the browser check: the real app on fixture data, already logged in.

usage: python serve.py <port> <data_dir>

<data_dir> holds roast_profiles.json, roast_records.json and users.json for the run;
the app loads them through its normal code path (so the startup migration runs too), and
nothing here touches the project's real data/ files. roasters.json is the real one.
"""

import os
import pathlib
import sys

port = int(sys.argv[1])
data_dir = pathlib.Path(sys.argv[2])

os.environ["FLASK_SECRET_KEY"] = "browser-check-only"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import data_persistence

data_persistence.ROAST_RECORDS_PATH = data_dir / "roast_records.json"
data_persistence.ROAST_PROFILES_PATH = data_dir / "roast_profiles.json"
data_persistence.USERS_PATH = data_dir / "users.json"

import app

# Skip the login form: every request carries a signed session for the fixtures' owner.
serializer = app.app.session_interface.get_signing_serializer(app.app)
cookie = serializer.dumps({"user_email": "owner@example.com"})
wsgi_app = app.app.wsgi_app


def with_session(environ, start_response):
    environ["HTTP_COOKIE"] = f"session={cookie}"
    return wsgi_app(environ, start_response)


app.app.wsgi_app = with_session
app.app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)

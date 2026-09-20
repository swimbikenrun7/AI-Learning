# Deploying coffeeroaster04 to PythonAnywhere

Steps 1-8 happen on pythonanywhere.com under your own account — nothing here can be automated from this machine. Follow them in order.

## 1. Sign up

Create a free account at [pythonanywhere.com](https://www.pythonanywhere.com). No payment info needed for the free tier.

## 2. Open a Bash console

From the PythonAnywhere dashboard: **Consoles** tab → **Bash**.

## 3. Clone the repo

The deployment branch is `main`. Day-to-day mission work happens on a feature branch (`agent_lab`, or e.g. `roaster-selection` for the roaster-driven redesign) and gets merged into `main` before it's deployed — `main` is what PythonAnywhere should always be running:

```bash
git clone https://github.com/swimbikenrun7/AI-Learning.git
```

(GitHub is on PythonAnywhere's free-tier network allowlist, so this works without any extra configuration. If the repo is or becomes private, you'll need a [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) in place of a password when prompted.)

## 4. Create a virtualenv and install dependencies

Still in the Bash console:

```bash
mkvirtualenv --python=python3.10 coffeeroaster04-env
cd AI-Learning/Projects/coffeeroaster04
pip install -r requirements.txt
```

**About the Python version:** this project's `pyproject.toml` says `requires-python = ">=3.14"`, but that's just what `uv` defaulted to on the developer's machine — nothing in the actual code (`calculations.py`, `data_persistence.py`, `validators.py`, `app.py`) uses anything newer than standard Flask and `pathlib`. Use whatever the newest Python 3.x is in PythonAnywhere's own dropdown when you create the web app in step 5 (their free tier has historically lagged behind current Python releases — check their signup/new-web-app page for what's actually offered, and just match that same version here in `mkvirtualenv`).

`mkvirtualenv` activates the environment automatically. If you open a new console later, reactivate it with:

```bash
workon coffeeroaster04-env
```

## 5. Create the web app

**Web** tab → **Add a new web app** → choose **Manual configuration** (not the Flask wizard — that scaffolds its own app instead of using this one) → pick the same Python version you used in step 4.

## 6. Point the WSGI file at this app

The **Web** tab links to a WSGI configuration file (something like `/var/www/yourusername_pythonanywhere_com_wsgi.py`). Open it in their editor, delete the placeholder content, and replace it with:

```python
import os
import sys

path = '/home/yourusername/AI-Learning/Projects/coffeeroaster04'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['FLASK_SECRET_KEY'] = 'paste-a-real-generated-secret-here'
os.environ['GMAIL_ADDRESS'] = 'your-gmail-address@gmail.com'
os.environ['GMAIL_APP_PASSWORD'] = 'paste-a-real-gmail-app-password-here'

from app import app as application
```

Replace `yourusername` with your actual PythonAnywhere username (visible in the file's own default path, and in your dashboard URL).

The app's own JavaScript and CSS live in `static/` and are served by Flask at `/static/`, so no separate static-files mapping is needed on the **Web** tab.

Generate the secret in a PythonAnywhere Bash console (don't reuse this one, and don't commit it anywhere) and paste the output in place of `paste-a-real-generated-secret-here`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

This has to be a real, stable value set directly in the WSGI file — if it's left unset, the app falls back to a random key generated at process start (`app.py`'s own default), which means every reload would silently log everyone out.

**Gmail App Password** (for password-reset and verification emails): `GMAIL_ADDRESS`/`GMAIL_APP_PASSWORD` power `email_sender.py`, which sends over Gmail's SMTP server — the one outbound SMTP host PythonAnywhere's free tier allowlists. Use a dedicated Gmail account if you'd rather not send from a personal one. To generate the app password: on that Google account, turn on 2-Step Verification (Google Account → **Security**), then go to **Security → 2-Step Verification → App passwords**, create one (any name), and paste the 16-character result in place of `paste-a-real-gmail-app-password-here` — not your regular Gmail password, which won't work here. If these two env vars are left unset, `email_sender.py` falls back to printing the email to the server log instead of sending it, which is fine for local development but means real users on a live deployment would never receive their reset/verification links.

## 7. Set the virtualenv path

Still on the **Web** tab, find the **Virtualenv** section and enter:

```
/home/yourusername/.virtualenvs/coffeeroaster04-env
```

## 8. Reload

Hit the big green **Reload** button at the top of the **Web** tab. Your app is now live at `https://yourusername.pythonanywhere.com`.

## Updating after future changes

Work happens on a feature branch, gets merged into `main`, and `main` gets pushed. Once that's pushed, pull it on PythonAnywhere:

```bash
cd ~/AI-Learning
git pull
```

Then hit **Reload** on the Web tab again. That's the whole update cycle — no CI/CD is set up for this (a possible future phase, not this one).

**If `git pull` refuses with "local changes would be overwritten"**, it means a commit changed a path that PythonAnywhere's live data has since diverged from — most likely `data/roast_records.json` or `data/roast_profiles.json` before they were gitignored (see Data below). Never `git checkout`/`git reset` that path to force it through — that discards live user data. Instead untrack the path locally without touching the file, then pull:

```bash
git rm --cached <path/that/conflicted>
git pull
```

## Data

`data/roast_records.json`, `data/roast_profiles.json`, and `data/users.json` live inside the cloned repo on PythonAnywhere's own persistent filesystem. They are gitignored (not tracked in git), so `git pull` will never touch, merge, or overwrite them, no matter what changes upstream — this is a guarantee, not a matter of remembering not to commit changes to them. They survive reloads and future pulls indefinitely.

`data/roasters.json` and `data/release_notes.json` are the exceptions: they are reference data (the list of selectable roasters, and the release history behind the footer's version and the What's new page), not user data, so they **are** tracked in git and updates arrive with `git pull`. Don't add them to `.gitignore`.

**One-time migration on the first start after the roaster-driven-profiles update.** Any profile or roast record that has no roaster is assigned the Fresh Roast SR800, every record gets a `temp_unit`, and (from the profile-styles update) every profile gets `style: "drip"` and every record a `profile_style` (its profile's); `roast_profiles.json` and `roast_records.json` are rewritten once, only if something changed, and later starts change nothing. Because those data files are gitignored, `git pull` never touches them, so an update needs no backup step.

Because the three files above are gitignored, a fresh clone (a new deployment, or a fresh checkout for local dev) starts with no `data/` files at all. Per `SPEC.md`, the app treats a missing data file as an empty dataset and creates it on first write — so a new deployment simply starts empty rather than inheriting another deployment's seed/demo data. If you want to seed a specific deployment with sample data (e.g. for a demo), copy JSON files into `data/` by hand after cloning; that's a one-time local action, never something `git` does for you.

## Calibration report

`calibration_report.py` reads the live `data/roast_records.json` and prints how logged roasts compare with each roaster's stored values; it only reads, never writes, and does not touch the running app. On PythonAnywhere, in a Bash console with the virtualenv active: `cd ~/AI-Learning/Projects/coffeeroaster04 && python calibration_report.py`. It needs no extra packages.

## Accounts

Every roast record and profile belongs to the account that created it — nobody can view, add, or delete another account's data (see `SPEC.md`'s Phase 7). `data/users.json` lives alongside the other two data files and persists the same way across reloads. The first account ever created on a given deployment automatically inherits ownership of any pre-existing (pre-account) seed data in `roast_records.json`/`roast_profiles.json`.

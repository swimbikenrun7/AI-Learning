# Deploying coffeeroaster04 to PythonAnywhere

Steps 1-8 happen on pythonanywhere.com under your own account — nothing here can be automated from this machine. Follow them in order.

## 1. Sign up

Create a free account at [pythonanywhere.com](https://www.pythonanywhere.com). No payment info needed for the free tier.

## 2. Open a Bash console

From the PythonAnywhere dashboard: **Consoles** tab → **Bash**.

## 3. Clone the repo

`coffeeroaster04` lives on the `agent_lab` branch, not `main` — clone that branch specifically:

```bash
git clone -b agent_lab https://github.com/swimbikenrun7/AI-Learning.git
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
import sys

path = '/home/yourusername/AI-Learning/Projects/coffeeroaster04'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
```

Replace `yourusername` with your actual PythonAnywhere username (visible in the file's own default path, and in your dashboard URL).

## 7. Set the virtualenv path

Still on the **Web** tab, find the **Virtualenv** section and enter:

```
/home/yourusername/.virtualenvs/coffeeroaster04-env
```

## 8. Reload

Hit the big green **Reload** button at the top of the **Web** tab. Your app is now live at `https://yourusername.pythonanywhere.com`.

## Updating after future changes

From a Bash console:

```bash
cd ~/AI-Learning
git pull
```

Then hit **Reload** on the Web tab again. That's the whole update cycle — no CI/CD is set up for this (a possible future phase, not this one).

## Data

`data/roast_records.json` and `data/roast_profiles.json` live inside the cloned repo on PythonAnywhere's own persistent filesystem — they'll survive reloads and won't reset to the git-committed seed data on their own. A `git pull` only touches files that changed upstream; if you haven't modified those two files in the git history since cloning, your live data is untouched by future pulls. (If you ever *do* want to reset to the committed seed data, that's a manual `git checkout` of those two files — not something that happens by accident.)

## No login

This deployment has no authentication — anyone with the URL can view, add, or delete roasts and profiles. That's a deliberate choice for a personal, low-stakes tool (see `SPEC.md`), not an oversight. If that stops being true for you, a simple HTTP Basic Auth gate is a small, no-new-dependency addition — ask for it as a future phase if you want it.

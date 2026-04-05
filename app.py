"""
WebOS Product Activation Service
Flask web application providing a Windows OOBE-style setup wizard
with license key validation.
"""

import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
# Secret key for session signing – in production set via environment variable
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

# ---------------------------------------------------------------------------
# Valid product keys (format: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX)
# ---------------------------------------------------------------------------
VALID_KEYS = {
    "WEBOS-SETUP-ACTIV-ATION1-00001",
    "WEBOS-SETUP-ACTIV-ATION1-00002",
    "WEBOS-DEMO0-KEY00-TRIAL-000001",
    "ABCDE-FGHIJ-KLMNO-PQRST-UVWXY",
}

# Ordered list of wizard steps
STEPS = ["license", "region", "privacy", "user", "complete"]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    """Redirect root to the first setup step."""
    session.clear()
    return redirect(url_for("step_license"))


@app.route("/setup/license", methods=["GET", "POST"])
def step_license():
    error = None
    if request.method == "POST":
        key = request.form.get("license_key", "").strip().upper()
        if key in VALID_KEYS:
            session["license_validated"] = True
            session["license_key"] = key
            return redirect(url_for("step_region"))
        else:
            error = "The product key you entered is invalid. Please check the key and try again."
    return render_template("license.html",
                           step=0,
                           total=len(STEPS) - 1,
                           error=error)


@app.route("/setup/region", methods=["GET", "POST"])
def step_region():
    if not session.get("license_validated"):
        return redirect(url_for("step_license"))
    if request.method == "POST":
        session["region"] = request.form.get("region", "en-US")
        session["timezone"] = request.form.get("timezone", "UTC")
        return redirect(url_for("step_privacy"))
    return render_template("region.html", step=1, total=len(STEPS) - 1)


@app.route("/setup/privacy", methods=["GET", "POST"])
def step_privacy():
    if not session.get("license_validated"):
        return redirect(url_for("step_license"))
    if request.method == "POST":
        session["privacy_diagnostics"] = "diagnostics" in request.form
        session["privacy_location"] = "location" in request.form
        return redirect(url_for("step_user"))
    return render_template("privacy.html", step=2, total=len(STEPS) - 1)


@app.route("/setup/user", methods=["GET", "POST"])
def step_user():
    if not session.get("license_validated"):
        return redirect(url_for("step_license"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        avatar_color = request.form.get("avatar_color", "#0078d4")
        if not username:
            error = "Please enter a username."
        elif len(username) < 2:
            error = "Username must be at least 2 characters."
        elif not password:
            error = "Please enter a password."
        elif len(password) < 4:
            error = "Password must be at least 4 characters."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            session["username"] = username
            session["avatar_color"] = avatar_color
            return redirect(url_for("step_complete"))
    return render_template("user.html", step=3, total=len(STEPS) - 1, error=error)


@app.route("/setup/complete")
def step_complete():
    if not session.get("license_validated"):
        return redirect(url_for("step_license"))
    return render_template("complete.html", step=4, total=len(STEPS) - 1)


@app.route("/desktop")
def desktop():
    if not session.get("license_validated"):
        return redirect(url_for("step_license"))
    return render_template(
        "desktop.html",
        username=session.get("username", "User"),
        avatar_color=session.get("avatar_color", "#0078d4"),
        region=session.get("region", "en-US"),
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)

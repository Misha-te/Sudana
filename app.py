import os

from flask import Flask, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Where uploaded profile pictures are stored, and which file types we allow
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def find_profile_photo(username):
    """Return the saved profile-photo filename for a user, or None."""
    safe = secure_filename(username) or "user"
    folder = app.config["UPLOAD_FOLDER"]
    if os.path.isdir(folder):
        for filename in os.listdir(folder):
            if filename.rsplit(".", 1)[0] == safe:
                return filename
    return None


def photo_url_for(username):
    """Build the URL for a user's profile photo, or None if they have none."""
    photo = find_profile_photo(username)
    return url_for("static", filename=f"uploads/{photo}") if photo else None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # Grab what the user typed in the form
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        gender = request.form.get("gender", "")
        hometown = request.form.get("hometown", "").strip()
        country = request.form.get("country", "").strip()
        not_south_sudanese = request.form.get("not_south_sudanese") == "yes"
        dob = request.form.get("dob", "")

        # Server-side checks (never trust the browser alone)
        errors = []
        if not email:
            errors.append("Please enter your email.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if not gender:
            errors.append("Please select your gender.")
        if not_south_sudanese:
            if not country:
                errors.append("Please enter your country.")
        elif not hometown:
            errors.append("Please tell us your hometown.")
        if not dob:
            errors.append("Please enter your date of birth.")

        if errors:
            # Send them back to the form with the errors and what they typed
            return render_template(
                "signup.html",
                errors=errors,
                email=email,
                gender=gender,
                hometown=hometown,
                country=country,
                not_south_sudanese=not_south_sudanese,
                dob=dob,
            )

        # Success! (In a real app you'd save this to a database here.)
        return render_template("success.html", email=email)

    # GET request — just show the empty form
    return render_template("signup.html", errors=[])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        errors = []
        if not email:
            errors.append("Please enter your email.")
        if not password:
            errors.append("Please enter your password.")

        if errors:
            return render_template("login.html", errors=errors, email=email)

        # In a real app you'd check these credentials against a database here.
        # Use the part of the email before "@" as a friendly display name.
        username = email.split("@")[0]
        return render_template(
            "dashboard.html", username=username, photo_url=photo_url_for(username)
        )

    return render_template("login.html", errors=[])


@app.route("/profile")
def profile():
    # Name is passed along in the link from the dashboard.
    username = request.args.get("name", "Friend")
    return render_template(
        "profile.html", username=username, photo_url=photo_url_for(username)
    )


@app.route("/upload-photo", methods=["POST"])
def upload_photo():
    username = request.form.get("name", "Friend")
    file = request.files.get("photo")

    if file and file.filename and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[1].lower()
        if ext in ALLOWED_EXTENSIONS:
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            safe = secure_filename(username) or "user"

            # Remove any previous photo for this user (e.g. an old .jpg)
            old = find_profile_photo(username)
            if old:
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], old))

            file.save(os.path.join(app.config["UPLOAD_FOLDER"], f"{safe}.{ext}"))

    return redirect(url_for("profile", name=username))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            return render_template("forgot_password.html", errors=["Please enter your email."])
        # In a real app you'd email a reset link here.
        return render_template("forgot_password.html", sent=True, email=email)

    return render_template("forgot_password.html", errors=[])


if __name__ == "__main__":
    app.run(debug=True, port=5001)

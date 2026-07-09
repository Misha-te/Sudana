import json
import os
import re
from datetime import date

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Needed to keep users logged in. For a real deployment use a random secret.
app.secret_key = "sudana-dev-secret-key"

# Where uploaded profile pictures are stored, and which file types we allow
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Simple JSON "database" of user accounts, keyed by username
USERS_FILE = os.path.join("data", "users.json")

# Maximum number of words allowed in a bio
BIO_WORD_LIMIT = 105

# Gender options a user can pick
GENDERS = ["Male", "Female", "Other","Prefer not to say"]

# Categories a user can pick for their profile
CATEGORIES = [
    "Student",
    "Artist",
    "Musician",
    "Entrepreneur",
    "Athlete",
    "Writer",
    "Content Creator",
    "Other",
]

# Names may only contain letters and spaces (no numbers or dashes)
NAME_PATTERN = re.compile(r"^[A-Za-z ]+$")


# ---------- User "database" helpers ----------

def load_users():
    try:
        with open(USERS_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_users(users):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def find_user_by_email(email):
    for user in load_users().values():
        if user["email"].lower() == email.lower():
            return user
    return None


def current_user():
    """The logged-in user's record, or None."""
    username = session.get("username")
    if username:
        return load_users().get(username)
    return None


# ---------- Profile photo helpers ----------

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


# ---------- Routes ----------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # Grab what the user typed in the form
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        gender = request.form.get("gender", "")
        hometown = request.form.get("hometown", "").strip()
        country = request.form.get("country", "").strip()
        not_south_sudanese = request.form.get("not_south_sudanese") == "yes"
        dob = request.form.get("dob", "")

        users = load_users()

        # Server-side checks (never trust the browser alone)
        errors = []
        if not first_name:
            errors.append("Please enter your first name.")
        elif not NAME_PATTERN.match(first_name):
            errors.append("First name can only contain letters (no numbers or dashes).")
        if not last_name:
            errors.append("Please enter your last name.")
        elif not NAME_PATTERN.match(last_name):
            errors.append("Last name can only contain letters (no numbers or dashes).")

        if not username:
            errors.append("Please choose a username.")
        elif " " in username:
            errors.append("Username cannot contain spaces.")
        elif username in users:
            errors.append("That username is already taken.")

        if not email:
            errors.append("Please enter your email.")
        elif find_user_by_email(email):
            errors.append("An account with that email already exists.")

        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if not gender:
            errors.append("Please select your gender.")
        if not_south_sudanese:
            if not country:
                errors.append("Please enter your country.")
        elif not hometown:
            errors.append("Please tell us your hometown.")

        # Date of birth must be present, valid, and at least 16 years old
        if not dob:
            errors.append("Please enter your date of birth.")
        else:
            try:
                birth = date.fromisoformat(dob)
                today = date.today()
                age = today.year - birth.year - (
                    (today.month, today.day) < (birth.month, birth.day)
                )
                if age < 16:
                    errors.append(
                        "Sorry, you must be at least 16 years old. "
                        "You cannot open an account right now."
                    )
            except ValueError:
                errors.append("Please enter a valid date of birth.")

        if errors:
            # Send them back to the form with the errors and what they typed
            return render_template(
                "signup.html",
                errors=errors,
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email,
                gender=gender,
                hometown=hometown,
                country=country,
                not_south_sudanese=not_south_sudanese,
                dob=dob,
            )

        # Save the new account
        users[username] = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "email": email,
            "password_hash": generate_password_hash(password),
            "gender": gender,
            "dob": dob,
            "hometown": country if not_south_sudanese else hometown,
            "bio": "",
            "category": "",
            "geez": [],          # accepted MyGeez connections (usernames)
            "pending_sent": [],  # MyGeez requests you've sent, still pending
            "posts": [],
            "photo_permission": False,
        }
        save_users(users)

        # Log them in and take them to their home feed
        session["username"] = username
        return redirect(url_for("dashboard"))

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

        if not errors:
            user = find_user_by_email(email)
            if user and check_password_hash(user["password_hash"], password):
                session["username"] = user["username"]
                return redirect(url_for("dashboard"))
            errors.append("Incorrect email or password.")

        return render_template("login.html", errors=errors, email=email)

    return render_template("login.html", errors=[])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template(
        "dashboard.html",
        username=user["username"],
        photo_url=photo_url_for(user["username"]),
    )


@app.route("/profile")
def profile():
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))

    # Whose profile are we looking at? Defaults to your own.
    target_name = request.args.get("name", viewer["username"])
    user = load_users().get(target_name)
    if not user:
        user = viewer  # fall back to your own profile

    is_owner = user["username"] == viewer["username"]
    return render_template(
        "profile.html",
        user=user,
        is_owner=is_owner,
        photo_url=photo_url_for(user["username"]),
        categories=CATEGORIES,
        geez_count=len(user.get("geez", [])),
        pending_count=len(user.get("pending_sent", [])),
        photo_permission=user.get("photo_permission", False),
    )


@app.route("/grant-photo-permission", methods=["POST"])
def grant_photo_permission():
    user = current_user()
    if user:
        users = load_users()
        users[user["username"]]["photo_permission"] = True
        save_users(users)
    return ("", 204)


@app.route("/edit-profile")
def edit_profile():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template(
        "edit_profile.html",
        user=user,
        categories=CATEGORIES,
        genders=GENDERS,
        bio_word_limit=BIO_WORD_LIMIT,
        errors=[],
    )


@app.route("/update-profile", methods=["POST"])
def update_profile():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    bio = request.form.get("bio", "").strip()
    category = request.form.get("category", "")
    gender = request.form.get("gender", "")
    hometown = request.form.get("hometown", "").strip()

    errors = []
    if len(bio.split()) > BIO_WORD_LIMIT:
        errors.append(f"Your bio must be {BIO_WORD_LIMIT} words or fewer.")

    if errors:
        # Keep what they typed and send them back to the edit page
        edited = dict(user)
        edited.update(bio=bio, category=category, gender=gender, hometown=hometown)
        return render_template(
            "edit_profile.html",
            user=edited,
            categories=CATEGORIES,
            genders=GENDERS,
            bio_word_limit=BIO_WORD_LIMIT,
            errors=errors,
        )

    users = load_users()
    record = users[user["username"]]
    record["bio"] = bio
    record["category"] = category if category in CATEGORIES else ""
    if gender in GENDERS:
        record["gender"] = gender
    record["hometown"] = hometown
    save_users(users)

    return redirect(url_for("profile"))


@app.route("/upload-photo", methods=["POST"])
def upload_photo():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    username = user["username"]
    file = request.files.get("photo")

    # Uploading a photo means permission was granted — remember it.
    users = load_users()
    users[username]["photo_permission"] = True
    save_users(users)

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

    return redirect(url_for("profile"))


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

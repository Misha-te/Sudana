import json
import os
import re
import sqlite3
import uuid
from datetime import date, datetime, timedelta

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from markupsafe import Markup, escape

app = Flask(__name__)
# Needed to keep users logged in. For a real deployment use a random secret.
app.secret_key = os.environ.get("SECRET_KEY", "sudana-dev-secret-key")

# Where uploaded profile pictures are stored, and which file types we allow
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Post attachments are kept separate from profile photos.
POST_UPLOAD_FOLDER = os.path.join("static", "uploads", "posts")
UPDATE_UPLOAD_FOLDER = os.path.join("static", "uploads", "updates")
POST_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
POST_VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}
app.config["POST_UPLOAD_FOLDER"] = POST_UPLOAD_FOLDER
app.config["UPDATE_UPLOAD_FOLDER"] = UPDATE_UPLOAD_FOLDER

# Simple JSON "database" of user accounts, keyed by username
USERS_FILE = os.path.join("data", "users.json")
DATABASE_FILE = os.environ.get("SUDANA_DATABASE", os.path.join("data", "sudana.db"))

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

# Reactions allowed on a post.
REACTIONS = {
    "like": "👍",
    "love": "❤️",
    "joy": "😂",
    "wow": "😮",
    "sad": "😢",
    "pray": "🙏",
}

# Names may only contain letters and spaces (no numbers or dashes)
NAME_PATTERN = re.compile(r"^[A-Za-z ]+$")


# ---------- User "database" helpers ----------

def database():
    os.makedirs(os.path.dirname(DATABASE_FILE) or ".", exist_ok=True)
    connection = sqlite3.connect(DATABASE_FILE, timeout=10)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, data TEXT NOT NULL)")
    return connection


def load_users():
    """Load user records from SQLite, importing the legacy JSON file once."""
    with database() as connection:
        rows = connection.execute("SELECT username, data FROM users").fetchall()
        if not rows and os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE) as source:
                    legacy = json.load(source)
                connection.executemany(
                    "INSERT OR REPLACE INTO users(username, data) VALUES (?, ?)",
                    [(name, json.dumps(record)) for name, record in legacy.items()],
                )
                rows = connection.execute("SELECT username, data FROM users").fetchall()
            except (OSError, json.JSONDecodeError):
                pass
    return {username: json.loads(data) for username, data in rows}


def save_users(users):
    """Upsert records without deleting database users absent from this snapshot."""
    with database() as connection:
        connection.executemany(
            "INSERT OR REPLACE INTO users(username, data) VALUES (?, ?)",
            [(name, json.dumps(record)) for name, record in users.items()],
        )


def find_user_by_email(email):
    for user in load_users().values():
        if user["email"].lower() == email.lower():
            return user
    return None


def normalize_phone(phone):
    value = re.sub(r"[^\d+]", "", phone or "")
    return value if re.fullmatch(r"\+?\d{7,15}", value) else ""


def find_user_by_login(identifier):
    needle = identifier.strip().lower()
    phone = normalize_phone(identifier)
    for user in load_users().values():
        if (user.get("email") or "").lower() == needle or user["username"].lower() == needle:
            return user
        if phone and user.get("phone") == phone:
            return user
    return None


def current_user():
    """The logged-in user's record, or None."""
    username = session.get("username")
    if username:
        return load_users().get(username)
    return None


@app.context_processor
def inject_notification_count():
    """Make the current notification total available to every page."""
    user = current_user()
    unread_count = 0
    if user:
        unread_count = sum(
            1 for notice in user.get("notifications", []) if not notice.get("read", False)
        )
    message_count = 0
    if user:
        message_count = len({message.get("sender") for message in user.get("messages", []) if not message.get("read")})
    return {"notification_count": unread_count, "message_count": message_count}


BAD_WORDS = {
    "bitch", "fuck", "fucked", "fucker", "fucking", "motherfucker", "shit", "shitty", "asshole",
    "nigger", "nigga", "kike", "chink", "faggot", "wetback", "spic",
}


def moderate_text(text):
    pattern = re.compile(r"\b(" + "|".join(re.escape(word) for word in BAD_WORDS) + r")\b", re.I)
    cleaned, count = pattern.subn("[removed]", text)
    return cleaned, count > 0


def display_name(user):
    return user.get("display_name") or " ".join(
        part for part in (user.get("first_name"), user.get("middle_name"), user.get("last_name")) if part
    )


app.jinja_env.globals["display_name"] = display_name


def active_blocked_usernames(user):
    """Return active blocks while remaining compatible with older string entries."""
    now = datetime.now()
    active = []
    for block in user.get("blocked", []):
        if isinstance(block, str):
            active.append(block)
            continue
        try:
            expires = datetime.fromisoformat(block.get("expires_at", ""))
        except (TypeError, ValueError):
            continue
        if expires > now:
            active.append(block.get("username"))
    return [username for username in active if username]


MESSAGE_STATUS_ORDER = {"sent": 0, "delivered": 1, "read": 2}


def message_status(users, message_id, status):
    """Synchronize a message status across sender and recipient copies."""
    for record in users.values():
        for message in record.get("messages", []):
            if message.get("id") == message_id and MESSAGE_STATUS_ORDER.get(status, 0) > MESSAGE_STATUS_ORDER.get(message.get("status", "sent"), 0):
                message["status"] = status
                if status == "read":
                    message["read"] = True


def conversation_is_accepted(user, peer_username):
    return peer_username in user.get("geez", []) or peer_username in user.get("message_contacts", [])


def message_time_parts(value):
    try:
        sent_at = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return {"date_label": "", "time_label": ""}
    today = date.today()
    if sent_at.date() == today:
        label = "Today"
    elif sent_at.date() == today - timedelta(days=1):
        label = "Yesterday"
    else:
        label = sent_at.strftime("%B %-d, %Y")
    return {"date_label": label, "time_label": sent_at.strftime("%-I:%M %p")}


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


def post_is_visible(post, viewer_username, author_username):
    """Return whether a post can be shown to the current viewer."""
    if author_username == viewer_username:
        return True
    visibility = post.get("visibility", "public")
    if visibility == "public":
        return True
    if visibility == "geez":
        return viewer_username in post.get("shared_with", [])
    return False  # private posts are visible only to their author


def ensure_post_ids(users):
    """Give older saved posts IDs and public visibility so they remain usable."""
    changed = False
    for user in users.values():
        for post in user.get("posts", []):
            if not isinstance(post, dict):
                continue
            if not post.get("id"):
                post["id"] = uuid.uuid4().hex
                changed = True
            if not post.get("visibility"):
                post["visibility"] = "public"
                changed = True
            post.setdefault("shared_with", [])
            post.setdefault("likes", [])
            post.setdefault("reactions", {})
    if changed:
        save_users(users)


def linkify(text):
    """Escape post text and turn http(s)/www links into safe clickable links."""
    url_pattern = re.compile(r"(?<![\w@])(https?://[^\s<]+|www\.[^\s<]+)")
    parts = []
    last = 0
    for match in url_pattern.finditer(text):
        parts.append(escape(text[last:match.start()]))
        displayed_url = match.group(0)
        href = displayed_url if displayed_url.startswith(("http://", "https://")) else f"https://{displayed_url}"
        # Keep trailing sentence punctuation outside the link.
        trailing = ""
        while displayed_url and displayed_url[-1] in ".,!?;:":
            trailing = displayed_url[-1] + trailing
            displayed_url = displayed_url[:-1]
            href = href[:-1]
        parts.append(Markup(f'<a href="{escape(href)}" target="_blank" rel="noopener noreferrer">{escape(displayed_url)}</a>'))
        parts.append(escape(trailing))
        last = match.end()
    parts.append(escape(text[last:]))
    return Markup("".join(str(part) for part in parts))


app.jinja_env.filters["linkify"] = linkify


@app.after_request
def inject_global_theme(response):
    """Load the persisted browser theme on every rendered HTML screen."""
    if response.content_type.startswith("text/html"):
        html = response.get_data(as_text=True)
        theme_tag = '<script src="/static/theme.js"></script>'
        if "theme.js" not in html and "</head>" in html:
            response.set_data(html.replace("</head>", f"{theme_tag}</head>", 1))
    return response


def build_feed_posts(users, viewer_username):
    """Return saved posts newest-first with author details for the dashboard."""
    posts = []
    for user in users.values():
        for post in user.get("posts", []):
            if isinstance(post, dict):
                if not post_is_visible(post, viewer_username, user["username"]):
                    continue
                media_filename = post.get("media_filename")
                reactions = dict(post.get("reactions", {}))
                for username in post.get("likes", []):
                    reactions.setdefault(username, "like")
                reaction_counts = {}
                for reaction_type in reactions.values():
                    if reaction_type in REACTIONS:
                        reaction_counts[reaction_type] = reaction_counts.get(reaction_type, 0) + 1
                reaction_summary = [
                    {"type": key, "emoji": REACTIONS[key], "count": count}
                    for key, count in reaction_counts.items()
                ]
                posts.append(
                    {
                        "id": post.get("id"),
                        "text": post.get("text", ""),
                        "created_at": post.get("created_at", ""),
                        "created_label": post.get("created_label", "Just now"),
                        "author_name": display_name(user),
                        "author_username": user["username"],
                        "author_initial": user["first_name"][0].upper(),
                        "author_photo_url": photo_url_for(user["username"]),
                        "visibility": post.get("visibility", "public"),
                        "media_url": url_for("static", filename=f"uploads/posts/{media_filename}") if media_filename else None,
                        "media_type": post.get("media_type"),
                        "shared_with": post.get("shared_with", []),
                        "is_owner": user["username"] == viewer_username,
                        "reaction_summary": reaction_summary,
                        "current_user_reaction": reactions.get(viewer_username),
                        "comments": post.get("comments", []),
                    }
                )
            else:
                posts.append(
                    {
                        "text": str(post),
                        "created_at": "",
                        "created_label": "Earlier",
                        "author_name": display_name(user),
                        "author_username": user["username"],
                        "author_initial": user["first_name"][0].upper(),
                        "author_photo_url": photo_url_for(user["username"]),
                        "visibility": "public",
                        "media_url": None,
                        "media_type": None,
                        "shared_with": [],
                        "is_owner": user["username"] == viewer_username,
                        "likes_count": 0,
                        "liked_by_current_user": False,
                    }
                )
    return sorted(posts, key=lambda post: post["created_at"], reverse=True)


def seed_trial_accounts():
    """Create repeatable trial accounts and their sample requests/messages."""
    users = load_users()
    target = "Misha_Awan" if "Misha_Awan" in users else next((u for u in users if not u.startswith("trial")), None)
    profiles = [
        ("trial_amina", "Amina", "Deng", "Kenya"),
        ("trial_bol", "Bol", "Ajak", ""),
        ("trial_nyandeng", "Nyandeng", "Majok", "Uganda"),
        ("trial_david", "David", "Lado", "United States"),
        ("trial_achol", "Achol", "Garang", ""),
    ]
    changed = False
    for index, (username, first, last, country) in enumerate(profiles, 1):
        if username not in users:
            users[username] = {
                "first_name": first, "last_name": last, "username": username,
                "email": f"{username}@sudana.test", "phone": f"+2119200000{index}",
                "password_hash": generate_password_hash("Trial123!"), "gender": "Other",
                "dob": "1998-01-01", "hometown": "" if country else "Juba",
                "home_country": country, "is_south_sudanese": not bool(country),
                "bio": "Trial community account", "category": "Student", "geez": [],
                "pending_sent": [target] if target else [], "notifications": [], "messages": [],
                "blocked": [], "posts": [], "photo_permission": False,
            }
            changed = True
        if target and target in users:
            message_id = f"trial-message-{index}"
            inbox = users[target].setdefault("messages", [])
            if not any(message.get("id") == message_id for message in inbox):
                inbox.append({"id": message_id, "sender": username, "recipient": target,
                              "text": f"Hi! I’m {first}. I’d like to connect with you on Sudana.",
                              "created_at": datetime.now().isoformat(timespec="seconds"),
                              "read": False, "request": True})
                changed = True
            notices = users[target].setdefault("notifications", [])
            notice_id = f"trial-request-{index}"
            if not any(notice.get("id") == notice_id for notice in notices):
                notices.append({"id": notice_id, "type": "geez_request", "actor_username": username,
                                "created_at": datetime.now().isoformat(timespec="seconds"),
                                "created_label": datetime.now().strftime("%b %d, %Y at %-I:%M %p"), "read": False})
                changed = True
    if changed:
        save_users(users)


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
        phone = normalize_phone(request.form.get("phone", ""))
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

        if not email and not phone:
            errors.append("Please enter an email address or phone number.")
        elif email and find_user_by_email(email):
            errors.append("An account with that email already exists.")
        if phone and any(item.get("phone") == phone for item in users.values()):
            errors.append("An account with that phone number already exists.")

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
                phone=request.form.get("phone", "").strip(),
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
            "phone": phone,
            "password_hash": generate_password_hash(password),
            "gender": gender,
            "dob": dob,
            "hometown": hometown if not_south_sudanese is False else "",
            "home_country": country if not_south_sudanese else "",
            "is_south_sudanese": not not_south_sudanese,
            "bio": "",
            "category": "",
            "geez": [],          # accepted MyGeez connections (usernames)
            "pending_sent": [],  # MyGeez requests you've sent, still pending
            "notifications": [], # MyGeez requests and acceptance updates
            "messages": [],
            "blocked": [],
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
            user = find_user_by_login(email)
            if user and check_password_hash(user["password_hash"], password):
                session["username"] = user["username"]
                return redirect(url_for("dashboard"))
            errors.append("Incorrect username, email, phone number, or password.")

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
    users = load_users()
    ensure_post_ids(users)
    geez_contacts = [
        {"username": name, "name": display_name(users[name])}
        for name in user.get("geez", [])
        if name in users
    ]
    updates = []
    for name in [user["username"], *user.get("geez", [])]:
        owner = users.get(name)
        if not owner or not owner.get("updates"):
            continue
        latest = owner["updates"][-1]
        updates.append({"username": name, "name": "Your Update" if name == user["username"] else f"{owner['first_name']}'s Update",
                        "initial": owner["first_name"][0].upper(), "photo_url": photo_url_for(name), "update_id": latest["id"]})
    return render_template(
        "dashboard.html",
        username=user["username"],
        photo_url=photo_url_for(user["username"]),
        posts=build_feed_posts(users, user["username"]),
        geez_contacts=geez_contacts,
        reactions=REACTIONS,
        updates=updates,
    )


@app.route("/updates/create", methods=["POST"])
def create_update():
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    text, flagged = moderate_text(request.form.get("text", "").strip())
    image = request.files.get("image")
    if flagged:
        flash("Your update was not posted because it violates Sudana's community guidelines.", "comment-error")
        return redirect(url_for("dashboard"))
    filename = None
    if image and image.filename and "." in image.filename:
        extension = image.filename.rsplit(".", 1)[1].lower()
        if extension in POST_IMAGE_EXTENSIONS:
            os.makedirs(app.config["UPDATE_UPLOAD_FOLDER"], exist_ok=True)
            filename = f"{uuid.uuid4().hex}.{extension}"
            image.save(os.path.join(app.config["UPDATE_UPLOAD_FOLDER"], filename))
    if text or filename:
        users = load_users()
        users[viewer["username"]].setdefault("updates", []).append({
            "id": uuid.uuid4().hex, "text": text, "image_filename": filename,
            "created_at": datetime.now().isoformat(timespec="seconds")
        })
        save_users(users)
    return redirect(url_for("dashboard"))


@app.route("/updates/<username>/<update_id>")
def view_update(username, update_id):
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    users = load_users()
    owner = users.get(username)
    if not owner or (username != viewer["username"] and username not in viewer.get("geez", [])):
        return redirect(url_for("dashboard"))
    update = next((item for item in owner.get("updates", []) if item.get("id") == update_id), None)
    if not update:
        return redirect(url_for("dashboard"))
    image_url = url_for("static", filename=f"uploads/updates/{update['image_filename']}") if update.get("image_filename") else None
    return render_template("update_view.html", owner=owner, owner_name=display_name(owner), update=update, image_url=image_url)


@app.route("/create-post", methods=["POST"])
def create_post():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    text, _ = moderate_text(request.form.get("post_text", "").strip())
    media = request.files.get("media")
    visibility = request.form.get("visibility", "public")
    if visibility not in {"public", "private", "geez"}:
        visibility = "public"

    media_filename = None
    media_type = None
    if media and media.filename and "." in media.filename:
        extension = media.filename.rsplit(".", 1)[1].lower()
        if extension in POST_IMAGE_EXTENSIONS | POST_VIDEO_EXTENSIONS:
            os.makedirs(app.config["POST_UPLOAD_FOLDER"], exist_ok=True)
            media_filename = f"{uuid.uuid4().hex}.{extension}"
            media.save(os.path.join(app.config["POST_UPLOAD_FOLDER"], media_filename))
            media_type = "image" if extension in POST_IMAGE_EXTENSIONS else "video"

    if text or media_filename:
        users = load_users()
        record = users[user["username"]]
        record.setdefault("posts", [])
        shared_with = []
        if visibility == "geez":
            allowed_geez = set(record.get("geez", []))
            shared_with = [name for name in request.form.getlist("shared_with") if name in allowed_geez]
        now = datetime.now()
        record["posts"].append(
            {
                "id": uuid.uuid4().hex,
                "text": text,
                "created_at": now.isoformat(timespec="seconds"),
                "created_label": now.strftime("%b %d, %Y at %-I:%M %p"),
                "visibility": visibility,
                "shared_with": shared_with,
                "media_filename": media_filename,
                "media_type": media_type,
                "likes": [],
                "reactions": {},
            }
        )
        save_users(users)

    return redirect(url_for("dashboard"))


@app.route("/comment-post/<post_id>", methods=["POST"])
def comment_post(post_id):
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    text, flagged = moderate_text(request.form.get("comment", "").strip())
    if flagged:
        flash("Your comment was not posted because it violates Sudana's community guidelines.", "comment-error")
        return redirect(request.referrer or url_for("dashboard"))
    if text:
        users = load_users()
        for author in users.values():
            for post in author.get("posts", []):
                if isinstance(post, dict) and post.get("id") == post_id and post_is_visible(post, viewer["username"], author["username"]):
                    comment_id = uuid.uuid4().hex
                    post.setdefault("comments", []).append({
                        "id": comment_id, "username": viewer["username"], "text": text,
                        "flagged": False, "created_at": datetime.now().isoformat(timespec="seconds")
                    })
                    if author["username"] != viewer["username"]:
                        now = datetime.now()
                        author.setdefault("notifications", []).append({
                            "id": uuid.uuid4().hex, "type": "post_comment",
                            "actor_username": viewer["username"], "post_id": post_id,
                            "comment_id": comment_id, "created_at": now.isoformat(timespec="seconds"),
                            "created_label": now.strftime("%b %d, %Y at %-I:%M %p"), "read": False,
                        })
                    save_users(users)
                    return redirect(request.referrer or url_for("dashboard"))
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/delete-post/<post_id>", methods=["POST"])
def delete_post(post_id):
    """Delete a post only when it belongs to the logged-in user."""
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    users = load_users()
    record = users.get(user["username"])
    if not record:
        return redirect(url_for("dashboard"))

    for index, post in enumerate(record.get("posts", [])):
        if isinstance(post, dict) and post.get("id") == post_id:
            removed = record["posts"].pop(index)
            media_filename = removed.get("media_filename")
            if media_filename:
                media_path = os.path.join(app.config["POST_UPLOAD_FOLDER"], secure_filename(media_filename))
                if os.path.isfile(media_path):
                    os.remove(media_path)
            save_users(users)
            break

    return redirect(url_for("dashboard"))


@app.route("/update-post/<post_id>", methods=["POST"])
def update_post(post_id):
    """Update text and privacy only for a post owned by the current user."""
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    users = load_users()
    record = users.get(user["username"])
    if not record:
        return redirect(url_for("dashboard"))

    for post in record.get("posts", []):
        if not isinstance(post, dict) or post.get("id") != post_id:
            continue
        text = request.form.get("post_text", "").strip()
        # Do not turn a text-only post into an empty post.
        if text or post.get("media_filename"):
            post["text"] = text
        visibility = request.form.get("visibility", "public")
        post["visibility"] = visibility if visibility in {"public", "private", "geez"} else "public"
        if post["visibility"] == "geez":
            allowed_geez = set(record.get("geez", []))
            post["shared_with"] = [
                name for name in request.form.getlist("shared_with") if name in allowed_geez
            ]
        else:
            post["shared_with"] = []
        save_users(users)
        break

    return redirect(url_for("dashboard"))


@app.route("/like-post/<post_id>", methods=["POST"])
def like_post(post_id):
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    users = load_users()
    for author in users.values():
        for post in author.get("posts", []):
            if isinstance(post, dict) and post.get("id") == post_id:
                if not post_is_visible(post, user["username"], author["username"]):
                    return redirect(url_for("dashboard"))
                likes = post.setdefault("likes", [])
                if user["username"] in likes:
                    likes.remove(user["username"])
                else:
                    likes.append(user["username"])
                save_users(users)
                return redirect(request.referrer or url_for("dashboard"))

    return redirect(url_for("dashboard"))


@app.route("/react-post/<post_id>", methods=["POST"])
def react_post(post_id):
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    reaction = request.form.get("reaction")
    if reaction not in REACTIONS:
        return redirect(request.referrer or url_for("dashboard"))

    users = load_users()
    for author in users.values():
        for post in author.get("posts", []):
            if isinstance(post, dict) and post.get("id") == post_id:
                if not post_is_visible(post, user["username"], author["username"]):
                    return redirect(url_for("dashboard"))

                reactions = post.setdefault("reactions", {})
                current = reactions.get(user["username"])
                if current == reaction:
                    reactions.pop(user["username"], None)
                else:
                    reactions[user["username"]] = reaction
                save_users(users)
                return redirect(request.referrer or url_for("dashboard"))

    return redirect(url_for("dashboard"))


@app.route("/search")
def search():
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))

    query = request.args.get("q", "").strip()
    results = []
    if query:
        needle = query.lower()
        for user in load_users().values():
            if user["username"] == viewer["username"]:
                continue  # don't show yourself in results
            full_name = display_name(user).lower()
            if (
                needle in user["username"].lower()
                or needle in user["first_name"].lower()
                or needle in user["last_name"].lower()
                or needle in full_name
            ):
                results.append(
                    {
                        "username": user["username"],
                        "name": display_name(user),
                        "category": user.get("category", ""),
                        "initial": user["first_name"][0].upper(),
                        "photo_url": photo_url_for(user["username"]),
                    }
                )

    return render_template("search.html", q=query, results=results)


@app.route("/my-geez")
def my_geez():
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))

    users = load_users()
    viewer_username = viewer["username"]

    def person_card(username):
        person = users.get(username)
        if not person:
            return None
        return {
            "username": username,
            "name": display_name(person),
            "category": person.get("category", ""),
            "initial": person["first_name"][0].upper(),
            "photo_url": photo_url_for(username),
        }

    contacts = []
    for username in viewer.get("geez", []):
        card = person_card(username)
        if card:
            contacts.append(card)

    sent_requests = []
    for username in viewer.get("pending_sent", []):
        card = person_card(username)
        if card:
            sent_requests.append(card)

    received_requests = []
    for username, person in users.items():
        if viewer_username in person.get("pending_sent", []):
            card = person_card(username)
            if card:
                received_requests.append(card)

    return render_template(
        "my_geez.html",
        user=viewer,
        contacts=contacts,
        sent_requests=sent_requests,
        received_requests=received_requests,
        photo_url=photo_url_for(viewer["username"]),
    )


@app.route("/add-geez/<username>", methods=["POST"])
def add_geez(username):
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))

    users = load_users()
    viewer_username = viewer["username"]
    if username in users and username != viewer_username:
        viewer_record = users[viewer_username]
        already_connected = username in viewer_record.setdefault("geez", [])
        has_incoming_request = viewer_username in users[username].get("pending_sent", [])
        pending_sent = viewer_record.setdefault("pending_sent", [])
        if not already_connected and not has_incoming_request and username not in pending_sent:
            pending_sent.append(username)
            now = datetime.now()
            users[username].setdefault("notifications", []).append(
                {
                    "id": uuid.uuid4().hex,
                    "type": "geez_request",
                    "actor_username": viewer_username,
                    "created_at": now.isoformat(),
                    "created_label": now.strftime("%b %d, %Y at %-I:%M %p"),
                    "read": False,
                }
            )
            save_users(users)

    return redirect(request.referrer or url_for("my_geez"))


@app.route("/accept-geez/<username>", methods=["POST"])
def accept_geez(username):
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))

    users = load_users()
    viewer_username = viewer["username"]
    requester = users.get(username)
    if requester and viewer_username in requester.get("pending_sent", []):
        requester["pending_sent"].remove(viewer_username)
        viewer_geez = users[viewer_username].setdefault("geez", [])
        requester_geez = requester.setdefault("geez", [])
        if username not in viewer_geez:
            viewer_geez.append(username)
        if viewer_username not in requester_geez:
            requester_geez.append(viewer_username)
        # The request is resolved, so replace it with an acceptance notice for
        # the sender. Rejections intentionally create no notification.
        users[viewer_username]["notifications"] = [
            notice
            for notice in users[viewer_username].get("notifications", [])
            if not (
                notice.get("type") == "geez_request"
                and notice.get("actor_username") == username
            )
        ]
        now = datetime.now()
        requester.setdefault("notifications", []).append(
            {
                "id": uuid.uuid4().hex,
                "type": "geez_accepted",
                "actor_username": viewer_username,
                "created_at": now.isoformat(),
                "created_label": now.strftime("%b %d, %Y at %-I:%M %p"),
                "read": False,
            }
        )
        save_users(users)

    return redirect(url_for("my_geez"))


@app.route("/reject-geez/<username>", methods=["POST"])
def reject_geez(username):
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))

    users = load_users()
    requester = users.get(username)
    if requester and viewer["username"] in requester.get("pending_sent", []):
        requester["pending_sent"].remove(viewer["username"])
        users[viewer["username"]]["notifications"] = [
            notice
            for notice in users[viewer["username"]].get("notifications", [])
            if not (
                notice.get("type") == "geez_request"
                and notice.get("actor_username") == username
            )
        ]
        save_users(users)

    return redirect(url_for("my_geez"))


@app.route("/notifications")
def notifications():
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))

    users = load_users()
    notices = []
    for notice in reversed(viewer.get("notifications", [])):
        actor = users.get(notice.get("actor_username"))
        if not actor:
            continue
        notices.append(
            {
                **notice,
                "actor_name": display_name(actor),
                "actor_initial": actor["first_name"][0].upper(),
                "actor_photo_url": photo_url_for(actor["username"]),
                "is_pending": (
                    notice.get("type") == "geez_request"
                    and viewer["username"] in actor.get("pending_sent", [])
                ),
            }
        )

    return render_template(
        "notifications.html",
        user=viewer,
        notices=notices,
        photo_url=photo_url_for(viewer["username"]),
    )


@app.route("/notifications/open/<notice_id>")
def open_notification(notice_id):
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    users = load_users()
    notice = next((item for item in users[viewer["username"]].get("notifications", [])
                   if item.get("id") == notice_id), None)
    if not notice:
        return redirect(url_for("notifications"))
    notice["read"] = True
    save_users(users)
    if notice.get("type") == "post_comment":
        return redirect(url_for("dashboard", _anchor=f"comment-{notice.get('comment_id')}"))
    if notice.get("type") == "geez_request":
        return redirect(url_for("my_geez", _anchor="received-requests"))
    return redirect(url_for("profile", name=notice.get("actor_username")))


@app.route("/notifications/delete/<notice_id>", methods=["POST"])
def delete_notification(notice_id):
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    users = load_users()
    record = users[viewer["username"]]
    record["notifications"] = [notice for notice in record.get("notifications", []) if notice.get("id") != notice_id]
    save_users(users)
    return redirect(url_for("notifications"))


@app.route("/notifications/mark-all-read", methods=["POST"])
def mark_all_notifications_read():
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))

    users = load_users()
    changed = False
    for notice in users[viewer["username"]].get("notifications", []):
        if not notice.get("read", False):
            notice["read"] = True
            changed = True
    if changed:
        save_users(users)

    return redirect(url_for("notifications"))


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

    # Make sure older posts have IDs and visibility set
    users = load_users()
    ensure_post_ids(users)

    is_owner = user["username"] == viewer["username"]
    visible_posts = []
    for post in user.get("posts", []):
        if isinstance(post, dict):
            if not post_is_visible(post, viewer["username"], user["username"]):
                continue
            reactions = dict(post.get("reactions", {}))
            for username in post.get("likes", []):
                reactions.setdefault(username, "like")
            reaction_counts = {}
            for reaction_type in reactions.values():
                if reaction_type in REACTIONS:
                    reaction_counts[reaction_type] = reaction_counts.get(reaction_type, 0) + 1
            visible_posts.append({
                **post,
                "reaction_summary": [
                    {"type": key, "emoji": REACTIONS[key], "count": count}
                    for key, count in reaction_counts.items()
                ],
                "current_user_reaction": reactions.get(viewer["username"]),
            })
        else:
            visible_posts.append(post)
    

    # If you're viewing your own profile, expose your MyGeez contacts so
    # the post editor can offer the same privacy/sharing UI as on the feed.
    geez_contacts = []
    if is_owner:
        geez_contacts = [
            {"username": name, "name": display_name(users[name])}
            for name in viewer.get("geez", [])
            if name in users
        ]

    return render_template(
        "profile.html",
        user=user,
        is_owner=is_owner,
        photo_url=photo_url_for(user["username"]),
        categories=CATEGORIES,
        geez_count=len(user.get("geez", [])),
        pending_count=len(user.get("pending_sent", [])),
        photo_permission=user.get("photo_permission", False),
        visible_posts=visible_posts,
        geez_contacts=geez_contacts,
        is_geez=user["username"] in viewer.get("geez", []),
        geez_request_sent=user["username"] in viewer.get("pending_sent", []),
        geez_request_received=viewer["username"] in user.get("pending_sent", []),
        reactions=REACTIONS,
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


@app.route("/messages")
def messages():
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    tab = request.args.get("tab", "all")
    users = load_users()
    record = users[viewer["username"]]
    changed = False
    for message in record.get("messages", []):
        if message.get("recipient") == viewer["username"] and message.get("sender") != viewer["username"]:
            before = message.get("status", "sent")
            message_status(users, message.get("id"), "delivered")
            changed = changed or before == "sent"
    if changed:
        save_users(users)
        viewer = users[viewer["username"]]
    conversations = {}
    for message in viewer.get("messages", []):
        peer = message.get("sender") if message.get("sender") != viewer["username"] else message.get("recipient")
        if not peer or peer not in users:
            continue
        conversation = conversations.setdefault(peer, {"username": peer, "unread_count": 0,
                                                         "request": not conversation_is_accepted(viewer, peer), "latest": ""})
        if message.get("sender") == peer and not message.get("read"):
            conversation["unread_count"] += 1
        conversation["latest"] = max(conversation["latest"], message.get("created_at", ""))
    rows = sorted(conversations.values(), key=lambda item: item["latest"], reverse=True)
    if tab == "all":
        rows = [item for item in rows if not item["request"]]
    elif tab == "unread":
        rows = [item for item in rows if item["unread_count"] and not item["request"]]
    elif tab == "requests":
        rows = [item for item in rows if item["request"]]
    return render_template("messages.html", user=viewer, conversations=rows, tab=tab)


@app.route("/messages/conversation/<username>")
def conversation(username):
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    users = load_users()
    peer = users.get(username)
    if not peer:
        return redirect(url_for("messages"))
    record = users[viewer["username"]]
    thread = []
    changed = False
    for message in record.get("messages", []):
        participants = {message.get("sender"), message.get("recipient")}
        if participants == {viewer["username"], username}:
            thread.append(message)
            if message.get("sender") == username and not message.get("read"):
                message["read"] = True
                message_status(users, message.get("id"), "read")
                changed = True
    if changed:
        save_users(users)
    for message in thread:
        message.update(message_time_parts(message.get("created_at")))
        message.setdefault("status", "read" if message.get("read") else "delivered")
    request_mode = not conversation_is_accepted(record, username) and any(
        message.get("sender") == username for message in thread
    )
    return render_template("conversation.html", user=record, peer=peer, peer_name=display_name(peer),
                           thread=thread, request_mode=request_mode)


@app.route("/messages/send/<username>", methods=["POST"])
def send_message(username):
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    users = load_users()
    recipient = users.get(username)
    text, flagged = moderate_text(request.form.get("message", "").strip())
    if recipient and text and username != viewer["username"]:
        if viewer["username"] not in active_blocked_usernames(recipient) and username not in active_blocked_usernames(viewer):
            if viewer["username"] in recipient.get("declined_message_requests", []) and not conversation_is_accepted(recipient, viewer["username"]):
                flash("This person is not accepting new message requests from you.", "comment-error")
                return redirect(url_for("conversation", username=username))
            message = {
                "id": uuid.uuid4().hex, "sender": viewer["username"], "recipient": username,
                "text": text, "flagged": flagged, "created_at": datetime.now().isoformat(timespec="seconds"),
                "read": False, "request": not conversation_is_accepted(recipient, viewer["username"]), "status": "sent",
            }
            recipient.setdefault("messages", []).append(message)
            sender_copy = dict(message, read=True, request=False, status="sent")
            users[viewer["username"]].setdefault("messages", []).append(sender_copy)
            save_users(users)
    return redirect(url_for("conversation", username=username))


@app.route("/messages/request/<username>/accept", methods=["POST"])
def accept_message_request(username):
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    users = load_users()
    if username in users:
        for left, right in ((viewer["username"], username), (username, viewer["username"])):
            contacts = users[left].setdefault("message_contacts", [])
            if right not in contacts:
                contacts.append(right)
        users[viewer["username"]].setdefault("declined_message_requests", [])
        if username in users[viewer["username"]]["declined_message_requests"]:
            users[viewer["username"]]["declined_message_requests"].remove(username)
        save_users(users)
    return redirect(url_for("conversation", username=username))


@app.route("/messages/request/<username>/decline", methods=["POST"])
def decline_message_request(username):
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    users = load_users()
    record = users[viewer["username"]]
    record["messages"] = [message for message in record.get("messages", [])
                          if {message.get("sender"), message.get("recipient")} != {viewer["username"], username}]
    declined = record.setdefault("declined_message_requests", [])
    if username not in declined:
        declined.append(username)
    save_users(users)
    return redirect(url_for("messages", tab="requests"))


@app.route("/messages/typing/<username>", methods=["POST"])
def set_typing(username):
    viewer = current_user()
    if not viewer:
        return jsonify(ok=False), 401
    users = load_users()
    active = bool((request.get_json(silent=True) or {}).get("typing", False))
    typing = users[viewer["username"]].setdefault("typing", {})
    if active:
        typing[username] = (datetime.now() + timedelta(seconds=5)).isoformat(timespec="seconds")
    else:
        typing.pop(username, None)
    save_users(users)
    return jsonify(ok=True)


@app.route("/messages/typing-status/<username>")
def typing_status(username):
    viewer = current_user()
    if not viewer:
        return jsonify(typing=False), 401
    peer = load_users().get(username, {})
    try:
        active = datetime.fromisoformat(peer.get("typing", {}).get(viewer["username"], "")) > datetime.now()
    except ValueError:
        active = False
    return jsonify(typing=active, name=peer.get("first_name", username))


@app.route("/messages/status/<username>")
def conversation_status(username):
    viewer = current_user()
    if not viewer:
        return jsonify(messages=[]), 401
    statuses = []
    for message in viewer.get("messages", []):
        if {message.get("sender"), message.get("recipient")} == {viewer["username"], username}:
            statuses.append({"id": message.get("id"), "status": message.get("status", "sent")})
    return jsonify(messages=statuses)


@app.route("/dating")
def dating():
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    people = [user for user in load_users().values() if user["username"] != viewer["username"] and user["username"] not in active_blocked_usernames(viewer)]
    return render_template("dating.html", user=viewer, people=people)


@app.route("/settings")
def settings():
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    return render_template("settings.html", user=viewer)


@app.route("/settings/name", methods=["GET", "POST"])
def change_name():
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    step = int(request.form.get("step", request.args.get("step", 1)))
    errors = []
    if request.method == "POST" and step == 1:
        first = request.form.get("first_name", "").strip()
        middle = request.form.get("middle_name", "").strip()
        last = request.form.get("last_name", "").strip()
        if not first or not last or any(value and not NAME_PATTERN.match(value) for value in (first, middle, last)):
            errors.append("First and last names are required, and names may only contain letters and spaces.")
        else:
            session["pending_name"] = {"first_name": first, "middle_name": middle, "last_name": last}
            step = 2
    elif request.method == "POST" and step == 2:
        pending = session.get("pending_name")
        selected = request.form.get("display_name", "")
        if not pending or selected not in name_suggestions(pending):
            errors.append("Please select one of the suggested display names.")
        else:
            pending["display_name"] = selected
            session["pending_name"] = pending
            step = 3
    elif request.method == "POST" and step == 3:
        pending = session.get("pending_name")
        if not pending:
            return redirect(url_for("change_name"))
        if not check_password_hash(viewer["password_hash"], request.form.get("current_password", "")):
            errors.append("The current password is incorrect.")
        else:
            users = load_users()
            users[viewer["username"]].update(pending)
            users[viewer["username"]]["name_changed_at"] = datetime.now().isoformat(timespec="seconds")
            save_users(users)
            session.pop("pending_name", None)
            return render_template("settings_result.html", title="Name changed", message="Your new display name has been saved.")
    pending = session.get("pending_name", {"first_name": viewer["first_name"], "middle_name": viewer.get("middle_name", ""), "last_name": viewer["last_name"]})
    return render_template("change_name.html", user=viewer, step=step, pending=pending,
                           suggestions=name_suggestions(pending), errors=errors)


def name_suggestions(parts):
    first, middle, last = parts.get("first_name", ""), parts.get("middle_name", ""), parts.get("last_name", "")
    suggestions = [f"{first} {last}"]
    if middle:
        initial = middle[0].upper()
        suggestions.extend([f"{first} {initial}. {last}", f"{first} {initial} {last}", f"{first} {middle} {last}"])
    return list(dict.fromkeys(suggestions))


@app.route("/settings/password", methods=["GET", "POST"])
def change_password():
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    step = int(request.form.get("step", request.args.get("step", 1)))
    errors = []
    if request.method == "POST" and step == 1:
        if check_password_hash(viewer["password_hash"], request.form.get("current_password", "")):
            session["password_change_verified"] = True
            step = 2
        else:
            errors.append("The current password is incorrect.")
    elif request.method == "POST" and step == 2:
        if not session.get("password_change_verified"):
            return redirect(url_for("change_password"))
        new_password, confirmation = request.form.get("new_password", ""), request.form.get("confirm_password", "")
        if len(new_password) < 8:
            errors.append("The new password must be at least 8 characters.")
        elif new_password != confirmation:
            errors.append("The new passwords do not match.")
        else:
            users = load_users()
            users[viewer["username"]]["password_hash"] = generate_password_hash(new_password)
            save_users(users)
            session.pop("password_change_verified", None)
            return render_template("settings_result.html", title="Password changed", message="Your password was updated successfully.")
    return render_template("change_password.html", user=viewer, step=step, errors=errors)


@app.route("/settings/location", methods=["GET", "POST"])
def change_location():
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    success = ""
    if request.method == "POST":
        users = load_users()
        record = users[viewer["username"]]
        if record.get("is_south_sudanese", True):
            record["hometown"] = request.form.get("hometown", "").strip()
        else:
            record["home_country"] = request.form.get("home_country", "").strip()
        save_users(users)
        viewer, success = record, "Location saved."
    return render_template("change_location.html", user=viewer, success=success)


@app.route("/settings/blocks", methods=["GET", "POST"])
def block_people():
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    users = load_users()
    if request.method == "POST":
        username = request.form.get("username", "")
        record = users[viewer["username"]]
        record["blocked"] = [block for block in record.get("blocked", [])
                             if (block if isinstance(block, str) else block.get("username")) != username]
        save_users(users)
        viewer = record
    blocks = []
    for entry in viewer.get("blocked", []):
        username = entry if isinstance(entry, str) else entry.get("username")
        if username in active_blocked_usernames(viewer):
            blocks.append({"username": username, "expires_at": entry.get("expires_at") if isinstance(entry, dict) else None})
    return render_template("block_people.html", user=viewer, blocks=blocks)


@app.route("/settings/blocks/search")
def block_search():
    viewer = current_user()
    if not viewer:
        return redirect(url_for("login"))
    query = request.args.get("q", "").strip().lower()
    results = []
    if query:
        results = [user for user in load_users().values() if user["username"] != viewer["username"]
                   and (query in user["username"].lower() or query in display_name(user).lower())]
    return render_template("block_search.html", user=viewer, results=results, q=query)


@app.route("/settings/blocks/<username>", methods=["GET", "POST"])
def block_duration(username):
    viewer = current_user()
    users = load_users()
    if not viewer:
        return redirect(url_for("login"))
    if username not in users or username == viewer["username"]:
        return redirect(url_for("block_search"))
    error = ""
    if request.method == "POST":
        duration = request.form.get("duration")
        hours = {"24": 24, "48": 48, "168": 168}.get(duration)
        if duration == "custom":
            try:
                expires = datetime.fromisoformat(request.form.get("custom_until", ""))
                if expires <= datetime.now():
                    raise ValueError
            except ValueError:
                error = "Choose a custom time in the future."
        elif hours:
            expires = datetime.now() + timedelta(hours=hours)
        else:
            error = "Choose a block duration."
        if not error:
            record = users[viewer["username"]]
            record["blocked"] = [block for block in record.get("blocked", [])
                                 if (block if isinstance(block, str) else block.get("username")) != username]
            record["blocked"].append({"username": username, "expires_at": expires.isoformat(timespec="minutes")})
            save_users(users)
            return redirect(url_for("block_people"))
    return render_template("block_duration.html", user=viewer, person=users[username], error=error)


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
    seed_trial_accounts()
    app.run(debug=True, port=5001)

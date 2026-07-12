import json
import os
import re
import uuid
from datetime import date, datetime

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
from markupsafe import Markup, escape

app = Flask(__name__)
# Needed to keep users logged in. For a real deployment use a random secret.
app.secret_key = "sudana-dev-secret-key"

# Where uploaded profile pictures are stored, and which file types we allow
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Post attachments are kept separate from profile photos.
POST_UPLOAD_FOLDER = os.path.join("static", "uploads", "posts")
POST_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
POST_VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}
app.config["POST_UPLOAD_FOLDER"] = POST_UPLOAD_FOLDER

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


@app.context_processor
def inject_notification_count():
    """Make the current notification total available to every page."""
    user = current_user()
    return {"notification_count": len(user.get("notifications", [])) if user else 0}


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
                        "author_name": f"{user['first_name']} {user['last_name']}",
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
                    }
                )
            else:
                posts.append(
                    {
                        "text": str(post),
                        "created_at": "",
                        "created_label": "Earlier",
                        "author_name": f"{user['first_name']} {user['last_name']}",
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
            "notifications": [], # MyGeez requests and acceptance updates
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
    users = load_users()
    ensure_post_ids(users)
    geez_contacts = [
        {"username": name, "name": f"{users[name]['first_name']} {users[name]['last_name']}"}
        for name in user.get("geez", [])
        if name in users
    ]
    return render_template(
        "dashboard.html",
        username=user["username"],
        photo_url=photo_url_for(user["username"]),
        posts=build_feed_posts(users, user["username"]),
        geez_contacts=geez_contacts,
        reactions=REACTIONS,
    )


@app.route("/create-post", methods=["POST"])
def create_post():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    text = request.form.get("post_text", "").strip()
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
            full_name = f"{user['first_name']} {user['last_name']}".lower()
            if (
                needle in user["username"].lower()
                or needle in user["first_name"].lower()
                or needle in user["last_name"].lower()
                or needle in full_name
            ):
                results.append(
                    {
                        "username": user["username"],
                        "name": f"{user['first_name']} {user['last_name']}",
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
            "name": f"{person['first_name']} {person['last_name']}",
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
                "actor_name": f"{actor['first_name']} {actor['last_name']}",
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
            {"username": name, "name": f"{users[name]['first_name']} {users[name]['last_name']}"}
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

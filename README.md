# Sudana

Sudana is a small Flask web app for a South Sudanese social community. It lets
people create an account, log in, search for other users, view profiles, edit
basic profile details, and upload a profile photo. The interface uses colors
inspired by the South Sudan flag.

This is an early personal-project version of the app, so it uses a simple JSON
file for storage instead of a full database.

## Features

- Public welcome page with links to sign up and log in
- Account creation with server-side validation:
  - first and last names can only contain letters and spaces
  - usernames must be unique and cannot contain spaces
  - emails must be unique
  - passwords must be at least 8 characters
  - users must be at least 16 years old
  - users can enter a South Sudan hometown or choose another country
- Password hashing with Werkzeug
- Login, logout, and session-based access to private pages
- Account menu beside the Sudana logo with placeholders for Settings & Privacy,
  Support from our team, Dark mode, and Premium modes
 # Sudana

 Sudana is a small Flask web app for a South Sudanese social community. It
 supports account creation, login, profile editing, profile photo uploads,
 a home feed with posts (text + optional photo/video), and simple privacy
 controls (Public / Private / Certain MyGeez).

 This project uses a JSON file for storage (`data/users.json`) and is intended
 for learning and prototyping — not production.

 ## Quick Start

 macOS (recommended):

 ```bash
 cd "/Users/misha/Documents/Spring 2026/Comp-127/Sudana"
 python3 -m venv .venv
 source .venv/bin/activate
 pip install flask
 python app.py
 ```

 Then open http://127.0.0.1:5001 in your browser.

 Note: the app runs on port `5001` by default to avoid conflicts on macOS.

 ## Key Routes & Pages

 - `GET /` — Welcome page (`templates/index.html`)
 - `GET|POST /signup` — Create account
 - `GET|POST /login` — Sign in
 - `GET /dashboard` — Home feed (`templates/dashboard.html`)
 - `POST /create-post` — Create a post (form on dashboard)
 - `POST /update-post/<post_id>` — Update a post (edit dialog)
 - `POST /delete-post/<post_id>` — Delete a post (owner-only)
 - `GET /profile` — View a profile (`templates/profile.html`)

 ## Recent Changes (post/profile parity)

 - Posts on the profile page now render similarly to the home feed so the
   experience is consistent between `dashboard` and `profile`.
 - Owners can now edit post text, change privacy (Public / Private / Certain
   MyGeez), and delete posts from their `profile` page — the same controls
   that were previously available only on the home feed.
 - The profile route now exposes `geez_contacts` to the template so the
   post editor can offer the same MyGeez sharing UI as on the dashboard.

 Files changed: [app.py](app.py), [templates/profile.html](templates/profile.html)

 ## Features (summary)

 - Signup/login with server-side validation and password hashing (Werkzeug)
 - Profile editing: category, bio (105-word limit), gender, hometown, photo
 - Post composer with optional image/video upload and visibility controls
 - Post edit & delete for post owners (available on both feed and profile)
 - Simple search for people by name or username

 ## Data & Uploads

 - Accounts: `data/users.json`
 - Profile photos: `static/uploads/` (one per user; new upload replaces old)
 - Post media: `static/uploads/posts/`

 ## Limitations

 - The app uses a JSON file for persistence — use a real database in production.
 - Email reset flow is a non-functional placeholder.
 - Some features (Messages, Notifications, MyGeez requests) are placeholders.

 ## Next Steps (suggested)

 - Add tests for auth, profile edits, and post actions.
 - Add a database (SQLite/Postgres) and migrations.
 - Improve frontend styling for the post editor on profile pages.

 ## Questions / Help

 If you want, I can:
 - Run the app and verify UI flows in a browser.
 - Add automated smoke tests for the post create/edit/delete flow.
 - Tweak CSS so the profile post editor visually matches the dashboard.

 ---

 Updated: July 10, 2026

# Sudana ★

A simple website celebrating the colors and spirit of **South Sudan**. Built with
Python and [Flask](https://flask.palletsprojects.com/), it has a welcome page,
sign-up, login, and forgot-password pages — all styled in the South Sudan flag
palette (black, red, green, blue, and gold).

## Features

- **Welcome page** with a hero banner and **Get Started** / **Login** buttons
- **Sign-up page** collecting first & last name, username, email, password,
  gender, hometown, and date of birth
  - First/last names may only contain **letters** (no numbers or dashes)
  - **Username** must be unique and space-free
  - Password must be at least **8 characters** (checked in the browser *and* on the server)
  - You must be at least **16 years old** to open an account
  - Hometown suggests South Sudan states and major towns
- **Real accounts** — sign-ups are saved and passwords are securely **hashed**
- **Login** with session-based sign-in and a **Forgot password?** link
- **Forgot-password page** to request a reset link
- **Home dashboard** (after login) styled like a social feed:
  - `sudana` top bar with search and messages icons
  - **My Updates** row of story circles
  - A **"What is in your mind?"** post composer
  - **My Geez Posts** feed — posts with avatar, text, image, reaction and comment
    counts, and Like / Comment / Share buttons
  - A **bottom navigation bar**: Home, 🤝 MyGeez, ❤️ Dating, 🔔 Notifications,
    and a **Profile** avatar
- **Profile page** showing:
  - Profile picture with a **change-photo** button (owner only). Asks for
    photo-access permission the first time (phone-style prompt), then opens your
    device's photo library/camera. The choice is remembered on the server.
  - Full name and **@username**
  - **Category** badge (Student, Artist, Musician, …) and **bio** — both editable
  - **Gender**
  - **MyGeez count** (public) and **pending MyGeez sent** (visible to you only)
  - **My Posts**

## Requirements

- Python 3
- Flask

## Setup

Install Flask (only needed once):

```bash
pip3 install flask
```

## Running the site

From the project folder, start the server:

```bash
python3 app.py
```

Then open your browser to:

```
http://127.0.0.1:5001
```

To stop the server, press `Ctrl + C` in the terminal.

> **Note:** The site runs on port **5001** because macOS uses port 5000 for its
> AirPlay Receiver. If you see "Address already in use," the app is probably
> already running in another terminal — stop it there first.

## Project structure

```
Sudana/
├── app.py                      # Flask server and page routes
├── templates/                  # HTML pages
│   ├── index.html              # welcome page
│   ├── signup.html             # sign-up form
│   ├── login.html              # login form
│   ├── forgot_password.html    # password reset request
│   ├── dashboard.html          # home page (feed) after login
│   └── profile.html            # user profile page
├── static/
│   ├── style.css               # styling (South Sudan flag colors)
│   └── uploads/                # uploaded profile pictures (created on first upload)
├── data/
│   └── users.json              # saved user accounts (auto-created)
└── README.md
```

> Accounts are stored in `data/users.json` (a simple file-based store).
> `werkzeug`, which handles the password hashing, is installed automatically
> with Flask.

## Notes / next steps

Accounts are now saved to a JSON file and passwords are hashed, but this is still
an early version. The **MyGeez**, **Dating**, and **Notifications** sections are
placeholders, and the dashboard feed shows sample posts (the composer doesn't
create real posts yet). Planned next steps:

- Let the "What is in your mind?" composer create real posts
- Build out the MyGeez (connections), Dating, and Notifications sections
- Move from the JSON file to a real database
- Send real password-reset emails

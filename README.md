# Sudana ★

A simple website celebrating the colors and spirit of **South Sudan**. Built with
Python and [Flask](https://flask.palletsprojects.com/), it has a welcome page,
sign-up, login, and forgot-password pages — all styled in the South Sudan flag
palette (black, red, green, blue, and gold).

## Features

- **Welcome page** with a hero banner and **Get Started** / **Login** buttons
- **Sign-up page** collecting email, password, gender, hometown, and date of birth
  - Password must be at least **8 characters** (checked in the browser *and* on the server)
  - Hometown suggests South Sudan states and major towns
- **Login page** with a **Forgot password?** link
- **Forgot-password page** to request a reset link
- **Home dashboard** (after login) styled like a social feed:
  - `sudana` top bar with search and messages icons
  - **My Updates** row of story circles
  - A **"What is in your mind?"** post composer
  - **My Geez Posts** feed — posts with avatar, text, image, reaction and comment
    counts, and Like / Comment / Share buttons
  - A **bottom navigation bar**: Home, 🤝 MyGeez, ❤️ Dating, 🔔 Notifications,
    and a **Profile** avatar
- **Profile page** showing the user's name and avatar
  - **Change your profile picture** — asks for photo-access permission the first
    time (phone-style prompt), then opens your device's photo library/camera,
    uploads the image, and shows it everywhere (profile + dashboard avatars)
  - The permission choice is **remembered on the server**, so it only asks once

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
│   ├── dashboard.html          # home page after login
│   ├── profile.html            # user profile page
│   └── success.html            # sign-up confirmation page
├── static/
│   ├── style.css               # styling (South Sudan flag colors)
│   └── uploads/                # uploaded profile pictures (created on first upload)
├── data/
│   └── permissions.json        # remembers photo-access permission (auto-created)
└── README.md
```

## Notes / next steps

This is an early version. User information **is not saved** yet — the forms
validate input and show confirmation pages, but there is no database and no real
authentication. The **MyGeez**, **Dating**, and **News & Entertainment** icons on
the dashboard are placeholders and don't open anything yet. Planned next steps:

- Build out the MyGeez, Dating, and News & Entertainment sections
- Store accounts in a database
- Securely hash passwords (never store them as plain text)
- Send real password-reset emails

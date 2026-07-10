# Sudana

Sudana is a small Flask web app for a South Sudanese social community. It lets
people create an account, log in, search for other users, view profiles, edit
basic profile details, and upload a profile photo. The interface uses colors
inspired by the South Sudan flag.

This is an early class-project version of the app, so it uses a simple JSON file
for storage instead of a full database.

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
- Forgot-password page that shows a reset-link confirmation message
- Home dashboard styled like a social feed
- Search page for finding people by name or username
- Profile pages for the logged-in user and other users
- Editable profile fields:
  - category
  - bio, limited to 105 words
  - gender
  - hometown
- Profile photo uploads saved in `static/uploads/`
- Local photo-access prompt that remembers when a user has allowed uploads

## Requirements

- Python 3
- Flask

Werkzeug is installed automatically with Flask and is used for password hashing.

## Setup

Install Flask:

```bash
pip3 install flask
```

## Run The App

From the project folder, start the Flask server:

```bash
python3 app.py
```

Then open:

```text
http://127.0.0.1:5001
```

To stop the server, press `Ctrl + C`.

The app runs on port `5001` because macOS often uses port `5000` for AirPlay
Receiver. If you see an "Address already in use" message, the app may already be
running in another terminal.

## Project Structure

```text
Sudana/
├── app.py
├── README.md
├── data/
│   └── users.json
├── static/
│   ├── style.css
│   └── uploads/
│       └── uploaded profile photos
└── templates/
    ├── dashboard.html
    ├── edit_profile.html
    ├── forgot_password.html
    ├── index.html
    ├── login.html
    ├── profile.html
    ├── search.html
    └── signup.html
```

## Data Storage

User accounts are saved in `data/users.json`. Each user record stores profile
details, hashed password data, connection placeholders, post placeholders, and
whether the user has granted photo-upload permission.

Uploaded profile photos are saved in `static/uploads/`. Each user can have one
current profile photo; uploading a new one replaces the old file for that user.

## Current Limitations

- The dashboard feed uses sample posts.
- The post composer does not create real posts yet.
- MyGeez connections, Dating, Notifications, and Messages are placeholders.
- The forgot-password page does not send real email.
- The JSON file works for development, but a real deployment should use a
  database and a secure secret key.

## Possible Next Steps

- Let users create, edit, and delete posts
- Build the MyGeez connection request flow
- Add real notifications and messaging
- Send password-reset emails
- Move account data from `users.json` into a database
- Add automated tests for signup, login, profile editing, and uploads

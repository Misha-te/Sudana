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
│   └── success.html            # confirmation page
├── static/
│   └── style.css               # styling (South Sudan flag colors)
└── README.md
```

## Notes / next steps

This is an early version. User information **is not saved** yet — the forms
validate input and show confirmation pages, but there is no database and no real
authentication. Planned next steps:

- Store accounts in a database
- Securely hash passwords (never store them as plain text)
- Send real password-reset emails

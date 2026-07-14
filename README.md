# 🇸🇸 Sudana

Sudana is a Flask-based social networking platform designed for the South Sudanese community. The goal of the project is to create a digital space where South Sudanese people can connect, share updates, discover opportunities, build relationships, and stay informed about their communities both at home and across the diaspora.

This project is currently in active development and serves as both a learning experience in full-stack web development and a long-term vision for a community-centered social platform.

---

## 🚀 Live Demo

**Status:** Live & Actively Developed

- **Primary:** https://sudana.onrender.com/
- **Mirror:** https://sudana-ssd.vercel.app/

Try the platform now! If one link is unavailable, try the other.

### Trial Accounts

Want to test the app without creating an account? Use one of these:

| Username | Email | Password |
|----------|-------|----------|
| `demo` | `demo@sudana.test` | `demo123456` |
| `test` | `test@sudana.test` | `test123456` |
| `visitor` | `visitor@sudana.test` | `visitor123456` |
| `trial_amina` | `trial_amina@sudana.test` | `Trial123!` |
| `trial_bol` | `trial_bol@sudana.test` | `Trial123!` |
| `trial_nyandeng` | `trial_nyandeng@sudana.test` | `Trial123!` |
| `trial_david` | `trial_david@sudana.test` | `Trial123!` |
| `trial_achol` | `trial_achol@sudana.test` | `Trial123!` |

You can log in with a username, email address, or phone number.

---

## ✨ Features

### 👤 User Accounts

* Registration and login with username, email, or phone number
* Secure password hashing with Werkzeug
* Session-based authentication
* Server-side validation

### 📝 Profiles

* Custom profile information
* Bio and personal details
* Profile photo uploads
* Hometown selection
* Home-country display for people who are not South Sudanese
* Gender and category settings

### 📢 Posts & Sharing

* Create text posts
* Upload images and videos
* Edit existing posts
* Delete posts
* Privacy controls:

  * Public
  * Private
  * Certain MyGeez

### 🔍 Social Discovery

* Search users by name
* Search users by username
* View public profiles
* Send MyGeez connection requests from a user's profile
* Review incoming and outgoing requests in MyGeez
* Accept or reject incoming requests
* Create mutual MyGeez connections after acceptance

### 🔔 Notifications

* Receive timestamped notifications for new MyGeez requests
* Accept or reject requests directly from notifications
* Notify the sender when a request is accepted
* Keep rejected requests private without notifying the sender
* Display the current notification count on the navigation bell

### 💬 Messaging and Safety

* Persistent messages with All, Unread, and Requests inbox tabs
* Message count badge and profile-to-profile messaging
* Messages outside MyGeez automatically enter Requests
* Post comments with server-side slur and profanity filtering
* User blocking and password-approved account changes
* Dating discovery page

### 🎨 User Experience

* South Sudan-inspired color scheme
* Responsive navigation
* Account management menu
* Foundation for future premium features

---

## 🛠️ Tech Stack

| Technology | Purpose                           |
| ---------- | --------------------------------- |
| Python     | Backend development               |
| Flask      | Web framework                     |
| HTML/CSS   | Frontend                          |
| Jinja2     | Template rendering                |
| Werkzeug   | Authentication & password hashing |
| SQLite     | Persistent database               |
| JavaScript | Interactive UI components         |

---

## 📂 Project Structure

```text
Sudana/
│
├── app.py
├── data/
│   ├── sudana.db
│   └── users.json  # one-time legacy import
│
├── static/
│   ├── uploads/
│   └── uploads/posts/
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   └── profile.html
│
└── README.md
```

---

## 🚀 Getting Started

### Clone the Repository

```bash
git clone https://github.com/misha-te/sudana.git
cd sudana
```

### Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install flask
```

### Run the Application

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5001
```

in your browser.

---

## 📸 Current Functionality

* Create an account
* Log in and log out
* Edit profile information
* Upload profile photos
* Create posts
* Upload media
* Control post visibility
* Search for users
* View profiles
* Send, accept, and reject MyGeez requests
* View accepted MyGeez connections
* Receive MyGeez request and acceptance notifications
* See a live notification count on the bell

---

## 🔒 Data Storage

Sudana stores account and social data in SQLite:

```text
data/sudana.db
```

Uploaded files are stored in:

```text
static/uploads/
static/uploads/posts/
```

Existing `data/users.json` accounts are imported automatically the first time the database is created. Set `SUDANA_DATABASE` to choose another path. For production, put that path on a persistent disk so accounts, requests, messages, and settings survive deployments.

---

## ⚠️ Current Limitations

* Messaging refreshes on page load rather than using WebSockets
* Password reset is not implemented
* Notifications update when a page is loaded rather than in real time

---

## 🔮 Future Roadmap

### Community Features

* MyGeez request cancellation and connection removal
* Direct messaging
* Group discussions
* Community forums

### Content Features

* News feeds
* South Sudan news section
* Sports updates
* Educational resources

### Platform Improvements

* SQLite/PostgreSQL integration
* REST API
* Mobile responsiveness
* Notifications system
* Improved security
* Cloud deployment
* User analytics dashboard for profile views, post/video engagement, and account performance

---

## 🎯 Vision

Sudana aims to become a digital hub for South Sudanese people worldwide—a place to connect, learn, share ideas, discuss current events, build relationships, and strengthen community ties across borders.

---

## 👨‍💻 Author

**Misha Awan**

Computer Science & Statistics Student
Macalester College

---

## 📅 Project Status

🚧 Active Development

Last Updated: July 2026

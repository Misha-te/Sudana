# 🇸🇸 Sudana

Sudana is a Flask-based social networking platform designed for South Sudanese communities at home and across the wider diaspora. It provides a digital space where people can create profiles, connect through MyGs, publish and share posts, share temporary Updates, communicate privately, search for community members, receive notifications, and request help from the Sudana team.

This project is currently in active development and serves as both a learning experience in full-stack web development and a long-term vision for a community-centered social platform.

---

## Current status

**Working:** accounts and profiles, email-or-phone authentication flows, MyGs, posts, reactions, comments, post sharing, Updates, private Update viewer tracking, persistent messaging, typing indicators, notifications, search, settings, themes, and support reports.

**Under development:** production email/SMS provider configuration, real-device deployment verification, cloud media storage, push-style notifications, and continued migration from PostgreSQL compatibility records to fully normalized tables.

**Coming soon:** Premium. Dating is temporarily disabled and is not part of the currently available application.

---

## 🚀 Live Demo

**Status:** Live and Actively Developed

- **Live application:** https://sudana.onrender.com/

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

* Register and log in with a username, email address, or phone number
* Secure password hashing with Werkzeug
* Session-based authentication
* Server-side validation
* Persistent account and social data
* Light and dark theme preferences saved across sessions
* Optional usernames with name-based identity fallback
* Email-or-phone signup with six-digit account verification
* Expiring, attempt-limited verification and password-reset codes
* Complete password-reset flow; passwords remain securely hashed

### 📝 Profiles

* Custom profile information
* Bio and personal details
* Profile photo uploads
* Hometown selection
* Home-country display for people who are not South Sudanese
* Gender and category settings
* MyGeez connection counts and public profile viewing
* Dedicated Message button on other users' profiles

### 📢 Posts & Sharing

* Create text posts
* Upload images and videos
* Edit existing posts
* Delete posts
* Privacy controls:

  * Public
  * Private
  * Certain MyGeez

Posts can be shared privately to one or more MyGeez through Sudana messages, opened in WhatsApp with an author/preview/link, or reposted to the user's timeline with optional commentary. Timeline shares reference the original post instead of duplicating it, and unavailable originals display a safe placeholder.

### ⏱️ Updates (Stories)

* Publish text-only Updates
* Upload an image with an Update
* Open your latest Update from the dashboard
* View Updates shared by MyGeez contacts beside your own
* Keep new Updates available for 24 hours
* Count each authenticated viewer once, even when they reopen an Update
* Let only an Update owner open the private viewer list
* Show a viewer's profile image and username, or first and last name when no username exists
* Refresh an owner's visible view count while the Update remains open

### 🔍 Social Discovery

* Search users by name
* Search users by username
* View public profiles
* Send MyGeez connection requests from a user's profile
* Review incoming and outgoing requests in MyGeez
* Accept or reject incoming requests
* Create mutual MyGeez connections after acceptance

### 🔔 Notifications

* Receive persistent, timestamped notifications for new MyGeez requests
* Open a MyG notification directly into the relevant request
* Accept or reject requests directly from notifications
* Notify the sender when a request is accepted
* Keep rejected requests private without notifying the sender
* Display the current notification count on the navigation bell
* Receive clickable notifications when another user comments on a post
* Open comment notifications at the relevant comment
* Delete individual notifications without deleting their related post or comment

### 💬 Messaging and Safety

* Conversation-based All Messages, Unread, and Requests tabs
* Conversation lists show usernames and per-conversation unread counts without message previews
* Opening a conversation automatically marks its incoming messages as read and updates badges
* All Messages and Unread contain accepted MyGs and accepted message conversations only
* Messages outside MyGeez remain separated in Requests until accepted
* Accept a request without losing its original messages, or decline it to prevent immediate repeat requests
* Full conversation screens show names and message history
* Message bubbles display Today, Yesterday, or a full date plus the sent time
* One gray check represents sent, two gray checks represent delivered, and two blue checks represent read
* Short-lived typing indicators update through background polling and automatically expire
* Insert a saved message immediately for the sender and deliver it to the recipient's open conversation through 1.2-second short polling
* Use stable message IDs to prevent duplicate bubbles after polling or reconnection
* Order messages by their stored timestamps and preserve them after refresh or reconnection
* Use an open-conversation heartbeat so on-screen messages become read without incorrectly increasing unread counts
* Other profiles use a Message button that opens the dedicated conversation screen
* Expandable comment composer with a compact send button
* Offensive comments are rejected with a community-guidelines error instead of being published

#### All Messages

All Messages contains accepted MyGeez conversations and accepted message requests. Conversation rows display only the username and unread count—message contents are not exposed in the list.

#### Unread

Unread contains accepted conversations with incoming messages that have not been opened. Opening a conversation marks its incoming messages as read and updates both the tab and navigation badge automatically.

#### Message Requests

Messages from people outside MyGeez remain in Requests. Recipients can accept a request while preserving its history, or decline it so the sender cannot immediately submit another unwanted request.

Individual messages display Today, Yesterday, or a full date when appropriate, plus the sent time. One gray check means sent, two gray checks mean delivered, and two blue checks mean read. Typing, new-message, and status updates use the same reconnecting polling channel.

### 😀 Reactions

* Tapping Like opens the complete reaction menu
* A selected reaction is stored in PostgreSQL and remains selected after refresh or login
* Selecting another reaction replaces the user's previous reaction instead of adding a duplicate

### ⚙️ Settings & Privacy

* Clean settings menu with a dedicated screen for each action
* Three-step name changes: enter names, choose a suggested display name, then approve with the current password
* Two-step password changes with current-password verification and matching new-password confirmation
* Location editing shows only Hometown for South Sudanese users and only Home Country for other users
* Search for users to block and choose a 24-hour, 48-hour, one-week, or custom block duration
* Review and remove active temporary blocks

The name workflow collects required first and last names plus an optional middle name, offers display-name arrangements, and requires the current password before saving. Password changes first verify the current password, then require matching new-password entries. Forgot Password sends an expiring code through the configured email or SMS delivery channel.

### 🆘 Support

The account menu links to a mobile-friendly support center with short account-creation and problem-reporting articles. Signed-in users can submit a title, app area, description, optional device information, and an optional validated screenshot up to 3 MB. Reports and attachments are stored in PostgreSQL and receive a confirmation screen.

### 💎 Premium

Premium remains visible as **Coming soon**. Payments, subscriptions, and incomplete payment pages are not enabled.

### 🎨 User Experience

* South Sudan-inspired color scheme
* Responsive navigation
* Account management menu
* Complete light and dark themes across pages, cards, conversations, forms, menus, and dialogs
* Readable dark-theme text, inputs, icons, tabs, reactions, notifications, and navigation
* Theme changes apply immediately and persist in browser storage across sessions
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
| PostgreSQL | Persistent production database     |
| SQLAlchemy | ORM and relational data model       |
| Alembic    | Database migrations                 |
| JavaScript | Interactive UI components         |
| Short polling | Live typing, messages, read state, and Update-count refresh |
| Render | Current web deployment |

---

## 📂 Project Structure

```text
Sudana/
│
├── app.py
├── database.py
├── models.py
├── alembic.ini
├── migrations/
│   └── versions/
├── tests/
│   └── test_app.py
├── data/
│   ├── sudana.db
│   └── users.json  # one-time legacy import
│
├── static/
│   ├── uploads/
│   ├── uploads/posts/
│   └── uploads/updates/
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── profile.html
│   ├── conversation.html
│   ├── update_view.html
│   └── update_viewers.html
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

On Windows:

```bash
.venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure and Run the Application

Create a PostgreSQL database and export its connection URL and a session secret. Ordinary `postgresql://` URLs from Render are accepted and the Psycopg driver is selected automatically:

```bash
export DATABASE_URL='postgresql://user:password@host:5432/sudana'
export SECRET_KEY='a-long-random-secret'
export VERIFICATION_MODE='console'
```

`VERIFICATION_MODE=console` is for local testing only. Leave `FLASK_ENV` unset locally; production must set `FLASK_ENV=production` and configure SMTP or SMS delivery.

Create or upgrade the schema:

```bash
alembic upgrade head
```

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
* Exchange direct messages and automatically track opened conversations
* Receive saved messages inside an open conversation without refreshing
* Accept and decline message requests
* View message timestamps, delivery/read checks, and typing indicators
* Publish moderated comments
* Receive persistent request and comment notifications
* Share text and image Updates
* See unique Update counts and an owner-only viewer list
* Manage names, passwords, account-aware locations, and temporary blocks from dedicated settings screens

---

## 🔒 Data Storage

Sudana uses PostgreSQL for production account and social data. `DATABASE_URL` is mandatory when `FLASK_ENV=production`. The legacy SQLite and JSON files are retained only as migration sources and local-development compatibility data.

Uploaded files are stored in:

```text
static/uploads/
static/uploads/posts/
static/uploads/updates/
```

For the first PostgreSQL deployment, set `IMPORT_LEGACY_ON_EMPTY=true` and run `python migrate_legacy_data.py` after `alembic upgrade head`. The importer refuses to run when PostgreSQL already contains account records and never modifies the SQLite/JSON source. Set the flag back to `false` after a successful import.

Stored data includes profiles, MyGeez connections and requests, notifications, messages and message requests, posts, comments, reactions, blocks, Updates, unique Update views, support reports, and account settings. Theme preferences are stored in the browser. Existing social routes currently use PostgreSQL-backed `account_states` compatibility records while normalized models are adopted incrementally. `UpdateView` is a normalized table with foreign keys to `updates` and `users`, a unique `(update_id, viewer_id)` constraint, and first/last-viewed timestamps.

Deleting a normalized Update or viewer account cascades its viewer records. New Updates expire after 24 hours; expired Updates are hidden and their private viewer records are purged when expiration is encountered. The owner viewing their own Update is never counted.

---

## ⚠️ Current Limitations

* Typing, new-message, and message-status updates use 1.2-second short polling rather than WebSockets; slow connections can therefore add a small delay
* Production email requires SMTP credentials; production SMS requires Twilio credentials
* Notifications update when a page is loaded rather than in real time
* Delivery status represents server/account delivery rather than confirmed physical-device delivery
* Uploaded files require persistent or cloud storage in production
* Support screenshots are currently stored in PostgreSQL for portability; object storage is recommended as usage grows
* The local compatibility path can still use SQLite for development and legacy import; production requires `DATABASE_URL`
* Cross-device browser testing and a live PostgreSQL restart test still need to be run against Render after migration `0002_update_views` is applied

---

## 🔮 Future Roadmap

### Community Features

* MyGeez request cancellation and connection removal
* Group discussions
* Community forums

### Content Features

* News feeds
* South Sudan news section
* Sports updates
* Educational resources

### Platform Improvements

* REST API
* Mobile responsiveness
* Notifications system
* Improved security
* Cloud deployment
* User analytics dashboard for profile views, post/video engagement, and account performance
* Cloud media and support-attachment storage
* Native mobile application
* Account recovery, two-factor authentication, and push notifications

---

## 🔧 Environment Variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Production | PostgreSQL connection URL |
| `SECRET_KEY` | Production | Flask session signing secret |
| `FLASK_ENV=production` | Production | Disables development-only storage/code display |
| `IMPORT_LEGACY_ON_EMPTY` | First migration only | Enables the guarded legacy import |
| `VERIFICATION_MODE=console` | Development only | Shows test codes in logs and the local verification screen |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, `SMTP_USERNAME`, `SMTP_PASSWORD` | Email delivery | Sends email verification/reset codes |
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` | SMS delivery | Sends phone verification/reset codes |
| `DEV_DATABASE_URL` | Optional local tooling | SQLAlchemy development database when `DATABASE_URL` is absent |
| `SUDANA_DATABASE` | Legacy/local only | SQLite compatibility/import file location |

Do not commit production secrets. Console verification is rejected in production unless a delivery provider is configured.

## 🚢 Render Deployment

Use this build command:

```bash
pip install -r requirements.txt && alembic upgrade head && python migrate_legacy_data.py
```

Use this start command:

```bash
gunicorn app:app
```

After the first successful import, set `IMPORT_LEGACY_ON_EMPTY=false`. Future deployments run Alembic migrations non-destructively and continue using the same PostgreSQL database.

### Database migration commands

Apply every committed migration locally or in production:

```bash
alembic upgrade head
```

After changing normalized models, generate and review a migration before committing it:

```bash
alembic revision --autogenerate -m "describe the schema change"
alembic upgrade head
```

The Update viewer change is migration `0002_update_views`. Render applies it during the build command before starting Gunicorn. Downgrades are intentionally non-destructive; use a reviewed forward migration to correct a production schema.

## ⚡ Real-time messaging notes

Sudana currently uses resilient short polling rather than Flask-SocketIO. The composer sends with `fetch`, and the server saves a message before returning its unique ID. The sender inserts that confirmed event immediately. An open recipient calls the conversation-events endpoint every 1.2 seconds; it receives ordered messages, typing state, and status changes and deduplicates bubbles using the stored ID. Failed polls retry automatically, and reconnecting returns the same IDs rather than creating new messages.

No WebSocket-specific Render configuration is required. Gunicorn can continue using `gunicorn app:app`. To test the behavior, sign in as two different users in separate browsers or devices, open the same conversation on both, send a message, and confirm that neither side refreshes the page.

## 🧪 Verification Testing

For local email or phone-flow testing, leave `FLASK_ENV` unset and set `VERIFICATION_MODE=console`. The six-digit development code appears in the server log and on the local verification page. This mode does not send email or SMS and is not accepted as production delivery.

To test real email, configure the SMTP variables and use an email-based account. To test real SMS, configure the Twilio variables and use an international-format phone number such as `+211...`. Provider charges and sender-verification rules may apply.

Run the automated suite with:

```bash
python -m unittest discover -s tests -v
```

The current suite covers signup and verification rules, password reset, posts/comments/reactions/sharing, MyG duplicate prevention, persisted messages, live message events and ordering, typing shutdown, open/closed unread behavior, Update viewer uniqueness, owner-only viewer authorization, no-username display, expired-view cleanup, support uploads, and the disabled dating route.

Manual message and Update checklist:

1. Create two verified accounts and connect them as MyGs.
2. Open the same conversation in two browsers or devices.
3. Type from one account and confirm the typing indicator appears and disappears after sending.
4. Confirm the saved message appears for the sender immediately and for the recipient without a refresh.
5. Close the recipient conversation, send again, and confirm its unread badge increases.
6. Create an Update from the first account.
7. Open it as the second account, then reopen it and confirm the count remains one.
8. Return as the owner, open the viewer count, and confirm the private viewer identity appears.
9. Try the viewer-list URL from the non-owner account and confirm access is denied.
10. Redeploy or restart the app and confirm the message and view record remain.

## 🔐 Security and privacy

Passwords use Werkzeug hashing and are never recoverable as plain text. Secrets and provider credentials come from environment variables. Update viewer identities are protected by server-side owner authorization, not only a hidden button. Viewer responses do not include email, phone, birth date, or other private account fields. Uploaded report files are restricted by extension, safe filename, and size. Production account and viewer data is stored in PostgreSQL.

## 🤝 Contributing

1. Create a branch from the current main branch.
2. Make a focused change without committing secrets or generated database files.
3. Run `python -m unittest discover -s tests -v` and review any migration you generated.
4. Push the branch and submit a pull request describing the behavior and manual checks.

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

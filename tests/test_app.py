import os
import tempfile
import unittest
import io
from datetime import date, datetime, timedelta

import app as sudana


class SudanaFlowsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        sudana.DATABASE_FILE = os.path.join(self.temp.name, "test.db")
        sudana.USERS_FILE = os.path.join(self.temp.name, "missing.json")
        sudana.USE_POSTGRES = False
        sudana.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = sudana.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def signup_data(self, **changes):
        data = {"first_name":"Amina", "middle_name":"Nyamal", "last_name":"Deng",
                "username":"amina", "contact":"amina@example.com", "password":"password1",
                "gender":"Female", "hometown":"Juba", "current_location":"Chicago", "dob":"2000-01-01"}
        data.update(changes)
        return data

    def create_verified(self, **changes):
        response = self.client.post("/signup", data=self.signup_data(**changes))
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as state:
            code = state["dev_verification_code"]
            key = state["pending_verification"]
        self.client.post("/verify-account", data={"code": code})
        return key

    def login_as(self, client, username):
        with client.session_transaction() as state:
            state["username"] = username

    def test_required_signup_fields(self):
        response = self.client.post("/signup", data={})
        self.assertIn(b"Please enter your first name", response.data)

    def test_optional_middle_name_and_username(self):
        key = self.create_verified(middle_name="", username="", contact="+15551234567")
        user = sudana.load_users()[key]
        self.assertTrue(user["username_auto"])
        self.assertEqual(sudana.identity_label(user), "Amina Deng")

    def test_email_and_phone_detection(self):
        email_key = self.create_verified()
        self.client.get("/logout")
        phone_key = self.create_verified(username="phoneuser", contact="+15557654321")
        users = sudana.load_users()
        self.assertEqual(users[email_key]["email"], "amina@example.com")
        self.assertEqual(users[phone_key]["phone"], "+15557654321")

    def test_duplicate_and_invalid_contact(self):
        self.create_verified()
        self.client.get("/logout")
        self.assertIn(b"email already exists", self.client.post("/signup", data=self.signup_data(username="other")).data)
        self.assertIn(b"valid email address or phone", self.client.post("/signup", data=self.signup_data(username="other", contact="bad")).data)

    def test_duplicate_username(self):
        self.create_verified()
        self.client.get("/logout")
        self.assertIn(b"username is already taken", self.client.post("/signup", data=self.signup_data(contact="other@example.com")).data)

    def test_under_sixteen(self):
        young = (date.today() - timedelta(days=15*365)).isoformat()
        self.assertIn(b"at least 16", self.client.post("/signup", data=self.signup_data(dob=young)).data)

    def test_verification_and_expiration(self):
        self.client.post("/signup", data=self.signup_data())
        with self.client.session_transaction() as state: key = state["pending_verification"]
        users = sudana.load_users(); users[key]["verification_code"]["expires_at"] = "2000-01-01T00:00:00"; sudana.save_users(users)
        self.assertIn(b"expired", self.client.post("/verify-account", data={"code":"000000"}).data)

    def test_password_reset(self):
        key = self.create_verified(); self.client.get("/logout")
        self.client.post("/forgot-password", data={"identifier":"amina@example.com"})
        with self.client.session_transaction() as state: code = state["dev_reset_code"]
        self.client.post("/forgot-password/verify", data={"code":code})
        self.client.post("/forgot-password/reset", data={"password":"newpassword","confirm_password":"newpassword"})
        self.assertTrue(sudana.check_password_hash(sudana.load_users()[key]["password_hash"], "newpassword"))

    def test_dating_unavailable(self):
        self.create_verified()
        self.assertEqual(self.client.get("/dating").status_code, 404)

    def test_support_report_and_persistence(self):
        key = self.create_verified()
        self.client.post("/support/report", data={"title":"Problem", "description":"Details", "app_area":"Profile"})
        self.assertEqual(len(sudana.load_users()[key]["support_reports"]), 1)
        self.assertEqual(len(sudana.load_users()[key]["support_reports"]), 1)

    def test_support_screenshot_validation(self):
        self.create_verified()
        response = self.client.post("/support/report", data={"title":"Problem", "description":"Details",
            "app_area":"Profile", "screenshot":(io.BytesIO(b"danger"), "payload.exe")},
            content_type="multipart/form-data")
        self.assertIn(b"must be PNG", response.data)

    def test_posts_comments_reactions_and_timeline_share(self):
        key = self.create_verified()
        self.client.post("/create-post", data={"post_text":"Original", "visibility":"public"})
        post_id = sudana.load_users()[key]["posts"][-1]["id"]
        self.client.post(f"/comment-post/{post_id}", data={"comment":"Hello"})
        self.client.post(f"/react-post/{post_id}", data={"reaction":"love"})
        self.client.post(f"/share-post/{post_id}/timeline", data={"commentary":"Sharing"})
        posts = sudana.load_users()[key]["posts"]
        self.assertEqual(posts[0]["comments"][-1]["text"], "Hello")
        self.assertEqual(posts[0]["reactions"][key], "love")
        self.assertEqual(posts[-1]["original_post_id"], post_id)

    def test_myg_duplicate_prevention_and_message_persistence(self):
        first = self.create_verified()
        self.client.get("/logout")
        second = self.create_verified(username="second", contact="second@example.com")
        self.client.post(f"/add-geez/{first}")
        self.client.post(f"/add-geez/{first}")
        self.assertEqual(sudana.load_users()[second]["pending_sent"].count(first), 1)
        self.client.post(f"/messages/send/{first}", data={"message":"Hello"})
        self.assertEqual(sudana.load_users()[first]["messages"][-1]["text"], "Hello")

    def test_sudana_post_message_share_and_notifications(self):
        first = self.create_verified()
        self.client.post("/create-post", data={"post_text":"Share me", "visibility":"public"})
        post_id = sudana.load_users()[first]["posts"][-1]["id"]
        self.client.get("/logout")
        second = self.create_verified(username="second", contact="second@example.com")
        self.client.post(f"/share-post/{post_id}/message", data={"recipients":[first]})
        self.client.post(f"/react-post/{post_id}", data={"reaction":"like"})
        users = sudana.load_users()
        self.assertEqual(users[first]["messages"][-1]["shared_post_id"], post_id)
        self.assertTrue(any(item.get("type") == "post_reaction" for item in users[first]["notifications"]))

    def test_live_message_events_are_saved_ordered_read_and_not_duplicated(self):
        first = self.create_verified()
        self.client.get("/logout")
        second = self.create_verified(username="second", contact="second@example.com")
        first_client = sudana.app.test_client()
        second_client = sudana.app.test_client()
        self.login_as(first_client, first)
        self.login_as(second_client, second)

        # The recipient opens the same conversation and establishes a heartbeat.
        self.assertEqual(second_client.get(f"/messages/conversation/{first}").status_code, 200)
        first_client.post(f"/messages/typing/{second}", json={"typing": True})
        typing_event = second_client.get(f"/messages/conversation/{first}/events").get_json()
        self.assertTrue(typing_event["typing"])

        response = first_client.post(
            f"/messages/send/{second}",
            data={"message": "First live message"},
            headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 201)
        sent = response.get_json()["message"]
        self.assertTrue(sent["mine"])
        self.assertEqual(sent["status"], "read")

        event = second_client.get(f"/messages/conversation/{first}/events").get_json()
        ids = [message["id"] for message in event["messages"]]
        self.assertEqual(ids.count(sent["id"]), 1)
        self.assertFalse(event["typing"])
        self.assertEqual(ids, [message["id"] for message in sorted(
            event["messages"], key=lambda item: (item["created_at"], item["id"])
        )])

        # Reconnection returns the same stable ID, allowing the client to dedupe.
        reconnected = second_client.get(f"/messages/conversation/{first}/events").get_json()
        self.assertEqual([item["id"] for item in reconnected["messages"]].count(sent["id"]), 1)
        stored = sudana.load_users()[second]["messages"]
        self.assertEqual([item["id"] for item in stored].count(sent["id"]), 1)

    def test_closed_conversation_increases_unread_open_conversation_does_not(self):
        first = self.create_verified()
        self.client.get("/logout")
        second = self.create_verified(username="second", contact="second@example.com")
        first_client = sudana.app.test_client()
        second_client = sudana.app.test_client()
        self.login_as(first_client, first)
        self.login_as(second_client, second)

        first_client.post(f"/messages/send/{second}", data={"message": "Unread while closed"})
        first_client.post(f"/messages/send/{second}", data={"message": "A second closed message"})
        closed_record = sudana.load_users()[second]
        self.assertFalse(closed_record["messages"][-1]["read"])
        self.assertFalse(closed_record["messages"][-2]["read"])
        self.assertEqual(len([item for item in closed_record["notifications"] if item.get("type") == "message" and not item.get("read")]), 1)
        second_client.get(f"/messages/conversation/{first}")
        opened_record = sudana.load_users()[second]
        self.assertTrue(all(item["read"] for item in opened_record["messages"][-2:]))
        self.assertFalse(any(item.get("type") == "message" and not item.get("read") for item in opened_record["notifications"]))
        first_client.post(f"/messages/send/{second}", data={"message": "Read while open"})
        open_record = sudana.load_users()[second]
        self.assertTrue(open_record["messages"][-1]["read"])
        self.assertFalse(any(item.get("type") == "message" and not item.get("read") for item in open_record["notifications"]))

    def test_update_views_are_unique_private_and_owner_is_not_counted(self):
        owner = self.create_verified()
        self.client.post("/updates/create", data={"text": "My temporary Update"})
        update_id = sudana.load_users()[owner]["updates"][-1]["id"]
        self.client.get("/logout")
        viewer = self.create_verified(username="", contact="viewer@example.com", first_name="No", last_name="Username")
        self.client.get("/logout")
        outsider = self.create_verified(username="outsider", contact="outsider@example.com")

        users = sudana.load_users()
        users[owner].setdefault("geez", []).append(viewer)
        users[viewer].setdefault("geez", []).append(owner)
        sudana.save_users(users)
        owner_client = sudana.app.test_client()
        viewer_client = sudana.app.test_client()
        outsider_client = sudana.app.test_client()
        self.login_as(owner_client, owner)
        self.login_as(viewer_client, viewer)
        self.login_as(outsider_client, outsider)

        self.assertEqual(viewer_client.get(f"/updates/{owner}/{update_id}").status_code, 200)
        self.assertEqual(viewer_client.post(f"/updates/{owner}/{update_id}/view").status_code, 200)
        self.assertEqual(viewer_client.post(f"/updates/{owner}/{update_id}/view").status_code, 200)
        self.assertEqual(owner_client.post(f"/updates/{owner}/{update_id}/view").get_json()["counted"], False)
        self.assertEqual(owner_client.get(f"/updates/{owner}/{update_id}/view-data").get_json()["count"], 1)
        viewer_page = owner_client.get(f"/updates/{owner}/{update_id}/viewers")
        self.assertIn(b"No Username", viewer_page.data)
        self.assertEqual(outsider_client.get(f"/updates/{owner}/{update_id}/viewers").status_code, 403)
        self.assertEqual(outsider_client.post(f"/updates/{owner}/{update_id}/view").status_code, 403)

    def test_expired_update_removes_private_view_records(self):
        owner = self.create_verified()
        self.client.post("/updates/create", data={"text": "Expiring"})
        self.client.get("/logout")
        viewer = self.create_verified(username="viewer", contact="viewer@example.com")
        users = sudana.load_users()
        update = users[owner]["updates"][-1]
        users[owner].setdefault("geez", []).append(viewer)
        users[viewer].setdefault("geez", []).append(owner)
        sudana.save_users(users)
        viewer_client = sudana.app.test_client()
        owner_client = sudana.app.test_client()
        self.login_as(viewer_client, viewer)
        self.login_as(owner_client, owner)
        viewer_client.post(f"/updates/{owner}/{update['id']}/view")
        users = sudana.load_users()
        users[owner]["updates"][-1]["expires_at"] = (datetime.now() - timedelta(seconds=1)).isoformat()
        sudana.save_users(users)
        self.assertEqual(owner_client.get(f"/updates/{owner}/{update['id']}/view-data").status_code, 410)
        with sudana.closing(sudana.database()) as connection:
            count = connection.execute("SELECT COUNT(*) FROM update_views WHERE update_id = ?", (update["id"],)).fetchone()[0]
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()

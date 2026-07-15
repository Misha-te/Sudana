import os
import tempfile
import unittest
import io
from datetime import date, timedelta

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


if __name__ == "__main__":
    unittest.main()

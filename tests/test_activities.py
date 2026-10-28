from copy import deepcopy
import unittest

from fastapi.testclient import TestClient

from src.app import activities, app


class ActivityRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.original_activities = deepcopy(activities)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.addCleanup(self.restore_activities)

    def restore_activities(self):
        activities.clear()
        activities.update(self.original_activities)

    def test_unregister_removes_only_selected_participant(self):
        response = self.client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "message": "Unregistered michael@mergington.edu from Chess Club"
        })
        expected = deepcopy(self.original_activities)
        expected["Chess Club"]["participants"].remove("michael@mergington.edu")
        self.assertEqual(self.client.get("/activities").json(), expected)

    def test_unregister_unknown_activity_does_not_change_data(self):
        response = self.client.delete(
            "/activities/Unknown/unregister", params={"email": "michael@mergington.edu"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Activity not found"})
        self.assertEqual(activities, self.original_activities)

    def test_unregister_nonparticipant_does_not_change_data(self):
        response = self.client.delete(
            "/activities/Chess%20Club/unregister", params={"email": "unknown@example.com"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            "detail": "Student is not signed up for this activity"
        })
        self.assertEqual(activities, self.original_activities)

    def test_unregister_requires_email(self):
        response = self.client.delete("/activities/Chess%20Club/unregister")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(activities, self.original_activities)

    def test_signup_unregister_and_signup_again_with_special_characters(self):
        email = "student+art&music@example.com"
        signup_url = "/activities/Art%20Club/signup"
        unregister_url = "/activities/Art%20Club/unregister"
        self.assertEqual(
            self.client.post(signup_url, params={"email": email}).status_code, 200
        )
        self.assertEqual(
            self.client.post(signup_url, params={"email": email}).status_code, 400
        )
        self.assertEqual(
            self.client.delete(unregister_url, params={"email": email}).status_code, 200
        )
        self.assertEqual(activities["Art Club"]["participants"], [])
        self.assertEqual(
            self.client.delete(unregister_url, params={"email": email}).status_code, 400
        )
        self.assertEqual(
            self.client.post(signup_url, params={"email": email}).status_code, 200
        )

    def test_signup_is_visible_in_fresh_uncached_activity_list(self):
        email = "newstudent@mergington.edu"
        response = self.client.post(
            "/activities/Chess%20Club/signup", params={"email": email}
        )
        self.assertEqual(response.status_code, 200)

        activities_response = self.client.get("/activities")
        self.assertEqual(activities_response.headers["cache-control"], "no-store")
        self.assertIn(email, activities_response.json()["Chess Club"]["participants"])

    def test_static_assets_must_be_revalidated(self):
        for path in ("/static/index.html", "/static/app.js", "/static/styles.css"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["cache-control"], "no-cache")

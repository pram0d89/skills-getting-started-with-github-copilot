import importlib
from fastapi.testclient import TestClient
import src.app as app_module


def make_client():
    """Reload app module to reset in-memory state."""
    importlib.reload(app_module)
    return TestClient(app_module.app), app_module.activities


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint."""

    def test_get_activities_contains_expected_activity(self):
        # Arrange
        client, _ = make_client()

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"

    def test_get_activities_includes_removed_participants_list(self):
        # Arrange
        client, _ = make_client()

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "removed_participants" in data["Chess Club"]
        assert isinstance(data["Chess Club"]["removed_participants"], list)


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_accepts_mergington_email(self):
        # Arrange
        client, activities = make_client()
        email = "alex@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 200
        assert email in activities[activity]["participants"]
        assert response.json()["message"] == f"Signed up {email} for {activity}"

    def test_signup_rejects_non_mergington_domain(self):
        # Arrange
        client, _ = make_client()
        email = "alex@example.com"
        activity = "Chess Club"

        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Only @mergington.edu email addresses are allowed"

    def test_signup_rejects_invalid_email_format(self):
        # Arrange
        client, _ = make_client()
        invalid_email = "notanemail"
        activity = "Chess Club"

        # Act
        response = client.post(f"/activities/{activity}/signup?email={invalid_email}")

        # Assert
        assert response.status_code == 400
        assert "valid email address" in response.json()["detail"].lower()

    def test_duplicate_signup_returns_400(self):
        # Arrange
        client, _ = make_client()
        email = "alex@mergington.edu"
        activity = "Chess Club"

        # Act
        first_response = client.post(f"/activities/{activity}/signup?email={email}")
        second_response = client.post(f"/activities/{activity}/signup?email={email}")

        # Assert
        assert first_response.status_code == 200
        assert second_response.status_code == 400
        assert second_response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_to_invalid_activity_returns_404(self):
        # Arrange
        client, _ = make_client()
        email = "alex@mergington.edu"
        invalid_activity = "Nonexistent Activity"

        # Act
        response = client.post(f"/activities/{invalid_activity}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_trims_email_whitespace(self):
        # Arrange
        client, activities = make_client()
        email_with_spaces = " alex@mergington.edu "
        activity = "Chess Club"

        # Act
        response = client.post(f"/activities/{activity}/signup?email={email_with_spaces}")

        # Assert
        assert response.status_code == 200
        assert "alex@mergington.edu" in activities[activity]["participants"]


class TestDeleteParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants endpoint."""

    def test_delete_participant_moves_to_removed(self):
        # Arrange
        client, activities = make_client()
        email = "michael@mergington.edu"
        activity = "Chess Club"
        assert email in activities[activity]["participants"]

        # Act
        response = client.delete(f"/activities/{activity}/participants?email={email}")

        # Assert
        assert response.status_code == 200
        assert email not in activities[activity]["participants"]
        assert email in activities[activity]["removed_participants"]
        assert response.json()["message"] == f"Removed {email} from {activity}"

    def test_delete_nonexistent_participant_returns_404(self):
        # Arrange
        client, _ = make_client()
        email = "nonexistent@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.delete(f"/activities/{activity}/participants?email={email}")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"

    def test_delete_from_invalid_activity_returns_404(self):
        # Arrange
        client, _ = make_client()
        email = "alex@mergington.edu"
        invalid_activity = "Nonexistent Activity"

        # Act
        response = client.delete(f"/activities/{invalid_activity}/participants?email={email}")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"


class TestRemovedParticipantsEndpoint:
    """Tests for GET /activities/{activity_name}/removed_participants endpoint."""

    def test_get_removed_participants_returns_removed_email(self):
        # Arrange
        client, _ = make_client()
        email = "michael@mergington.edu"
        activity = "Chess Club"
        client.delete(f"/activities/{activity}/participants?email={email}")

        # Act
        response = client.get(f"/activities/{activity}/removed_participants")

        # Assert
        assert response.status_code == 200
        payload = response.json()
        assert payload["activity"] == activity
        assert email in payload["removed_participants"]

    def test_get_removed_participants_initially_empty(self):
        # Arrange
        client, _ = make_client()
        activity = "Programming Class"

        # Act
        response = client.get(f"/activities/{activity}/removed_participants")

        # Assert
        assert response.status_code == 200
        payload = response.json()
        assert payload["activity"] == activity
        assert payload["removed_participants"] == []

    def test_get_removed_participants_invalid_activity_returns_404(self):
        # Arrange
        client, _ = make_client()
        invalid_activity = "Nonexistent Activity"

        # Act
        response = client.get(f"/activities/{invalid_activity}/removed_participants")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

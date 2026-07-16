"""
Tests for the Mergington High School Activities API

This module contains tests for the FastAPI backend using the AAA
(Arrange-Act-Assert) testing pattern.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

# Create a test client
client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities_returns_success(self):
        """
        Arrange: Set up the test client
        Act: Get the activities endpoint
        Assert: Verify the response status is 200 and contains activities
        """
        # Arrange
        expected_status = 200

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == expected_status
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0

    def test_activities_contain_required_fields(self):
        """
        Arrange: Get the activities from the API
        Act: Extract one activity
        Assert: Verify it has all required fields
        """
        # Arrange
        required_fields = {
            "description",
            "schedule",
            "max_participants",
            "participants",
        }

        # Act
        response = client.get("/activities")
        activities = response.json()
        first_activity = next(iter(activities.values()))

        # Assert
        assert all(field in first_activity for field in required_fields)


class TestSignupEndpoint:
    """Tests for the signup endpoint"""

    def test_signup_for_activity_success(self):
        """
        Arrange: Prepare a new student email and activity name
        Act: Sign up the student for an activity
        Assert: Verify the response is successful
        """
        # Arrange
        test_email = "test.student@mergington.edu"
        activity_name = "Chess Club"
        expected_status = 200

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={test_email}"
        )

        # Assert
        assert response.status_code == expected_status
        result = response.json()
        assert "message" in result
        assert test_email in result["message"]

    def test_signup_duplicate_registration_fails(self):
        """
        Arrange: Sign up a student for an activity
        Act: Try to sign up the same student again
        Assert: Verify the second attempt fails with 400 status
        """
        # Arrange
        test_email = "duplicate.student@mergington.edu"
        activity_name = "Art Club"
        expected_error_status = 400

        # Act - First signup
        response_first = client.post(
            f"/activities/{activity_name}/signup?email={test_email}"
        )
        assert response_first.status_code == 200

        # Act - Second signup (duplicate)
        response_duplicate = client.post(
            f"/activities/{activity_name}/signup?email={test_email}"
        )

        # Assert
        assert response_duplicate.status_code == expected_error_status
        error = response_duplicate.json()
        assert "detail" in error
        assert "already signed up" in error["detail"].lower()

    def test_signup_nonexistent_activity_fails(self):
        """
        Arrange: Prepare a non-existent activity name
        Act: Try to sign up for the non-existent activity
        Assert: Verify the response is 404 Not Found
        """
        # Arrange
        test_email = "student@mergington.edu"
        nonexistent_activity = "Fake Activity 123"
        expected_status = 404

        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup?email={test_email}"
        )

        # Assert
        assert response.status_code == expected_status
        error = response.json()
        assert "detail" in error
        assert "not found" in error["detail"].lower()


class TestActivityDetails:
    """Tests for activity details and participant tracking"""

    def test_participants_list_updated_after_signup(self):
        """
        Arrange: Get initial participant count for an activity
        Act: Sign up a new student
        Assert: Verify the participant list is updated
        """
        # Arrange
        test_email = "new.participant@mergington.edu"
        activity_name = "Programming Class"

        # Get initial state
        response_before = client.get("/activities")
        activities_before = response_before.json()
        initial_count = len(activities_before[activity_name]["participants"])

        # Act
        client.post(f"/activities/{activity_name}/signup?email={test_email}")

        # Assert
        response_after = client.get("/activities")
        activities_after = response_after.json()
        final_count = len(activities_after[activity_name]["participants"])

        assert final_count == initial_count + 1
        assert test_email in activities_after[activity_name]["participants"]

    def test_all_activities_have_valid_participant_count(self):
        """
        Arrange: Get all activities
        Act: Check participant counts
        Assert: Verify counts are valid (not exceeding max_participants)
        """
        # Arrange & Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            participant_count = len(activity_data["participants"])
            max_participants = activity_data["max_participants"]
            assert (
                participant_count <= max_participants
            ), f"{activity_name} has too many participants"

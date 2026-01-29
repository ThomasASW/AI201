"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {k: {"participants": v["participants"].copy()} 
                          for k, v in activities.items()}
    yield
    # Restore original state after test
    for activity_name, data in original_activities.items():
        activities[activity_name]["participants"] = data["participants"]


class TestGetActivities:
    """Tests for retrieving activities"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that get_activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that we have activities
        assert len(data) > 0
        
        # Check structure of activities
        for activity_name, activity_info in data.items():
            assert "description" in activity_info
            assert "schedule" in activity_info
            assert "max_participants" in activity_info
            assert "participants" in activity_info
            assert isinstance(activity_info["participants"], list)
    
    def test_get_activities_includes_chess_club(self, client):
        """Test that Chess Club is in the activities list"""
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data
        assert "Learn strategies" in data["Chess Club"]["description"]


class TestSignupForActivity:
    """Tests for signing up for activities"""
    
    def test_signup_new_participant(self, client, reset_activities):
        """Test signing up a new participant"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_duplicate_participant(self, client, reset_activities):
        """Test signing up a participant who is already registered"""
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_multiple_different_activities(self, client, reset_activities):
        """Test signing up for multiple different activities"""
        email = "multistudent@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify in both activities
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Programming Class"]["participants"]


class TestUnregisterFromActivity:
    """Tests for unregistering from activities"""
    
    def test_unregister_existing_participant(self, client, reset_activities):
        """Test unregistering a participant who is registered"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "michael@mergington.edu" in data["message"]
        assert "Removed" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant(self, client, reset_activities):
        """Test unregistering a participant who is not registered"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_unregister_from_nonexistent_activity(self, client, reset_activities):
        """Test unregistering from a non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_then_can_signup_again(self, client, reset_activities):
        """Test that a participant can sign up again after unregistering"""
        email = "michael@mergington.edu"
        
        # Remove from Chess Club
        client.delete(f"/activities/Chess Club/unregister?email={email}")
        
        # Should be able to sign up again
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response.status_code == 200
        
        # Verify they're back in the activity
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Chess Club"]["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestActivityConstraints:
    """Tests for activity constraints"""
    
    def test_activity_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity in data.items():
            assert isinstance(activity, dict)
            assert isinstance(activity["description"], str)
            assert isinstance(activity["schedule"], str)
            assert isinstance(activity["max_participants"], int)
            assert isinstance(activity["participants"], list)
            assert activity["max_participants"] > 0
            assert len(activity["participants"]) <= activity["max_participants"]

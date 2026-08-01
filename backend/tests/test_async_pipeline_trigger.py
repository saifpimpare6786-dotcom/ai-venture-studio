import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app
from app.core.security import get_current_user

# Mock user object for auth dependency
mock_user = MagicMock()
mock_user.id = "test-user-123"

def override_get_current_user():
    return mock_user

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

@patch("app.api.reports.get_supabase_client")
def test_trigger_generation_async_immediate_return(mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    # Mock project lookup
    mock_project = {
        "id": "proj-123",
        "user_id": "test-user-123",
        "name": "Test Startup",
        "industry": "Fintech",
        "idea_input": "An AI platform for automated financial auditing.",
        "status": "idle"
    }
    
    # Supabase table queries setup
    table_mock = MagicMock()
    mock_supabase.table.return_value = table_mock
    
    # Select response for projects table
    select_mock = MagicMock()
    select_mock.eq.return_value.execute.return_value.data = [mock_project]
    table_mock.select.return_value = select_mock
    
    # Update mock
    update_mock = MagicMock()
    update_mock.eq.return_value.execute.return_value.data = [mock_project]
    table_mock.update.return_value = update_mock

    # Patch background pipeline execution so it doesn't actually call LLM APIs during unit test
    with patch("app.api.reports.run_pipeline_background") as mock_background_runner:
        response = client.post("/api/reports/project/proj-123/generate")
        
        assert response.status_code == 202
        data = response.json()
        
        # 1. Immediate response assertions
        assert data["project_id"] == "proj-123"
        assert data["status"] == "running"
        assert "triggered" in data["message"]
        
        # 2. Verify Supabase update was called to set status='running'
        table_mock.update.assert_called_with({"status": "running"})

@patch("app.api.reports.get_supabase_client")
def test_get_project_status_and_reports(mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    # Setup mock responses for project select & reports select
    mock_project_select = MagicMock()
    mock_project_select.eq.return_value.execute.return_value.data = [{"user_id": "test-user-123", "status": "running"}]
    
    mock_reports_select = MagicMock()
    mock_reports_select.eq.return_value.execute.return_value.data = [
        {"id": "rep-1", "project_id": "proj-123", "report_type": "Executive Summary", "content": {}}
    ]
    
    def table_side_effect(table_name):
        t_mock = MagicMock()
        if table_name == "projects":
            t_mock.select.return_value = mock_project_select
        elif table_name == "reports":
            t_mock.select.return_value = mock_reports_select
        return t_mock
        
    mock_supabase.table.side_effect = table_side_effect

    response = client.get("/api/reports/project/proj-123/status")
    
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "proj-123"
    assert data["status"] == "running"
    assert len(data["reports"]) == 1
    assert data["reports"][0]["report_type"] == "Executive Summary"

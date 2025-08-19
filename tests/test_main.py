import pytest
from fastapi.testclient import TestClient
from AIDaily.main import app, background_runner, scheduler

#index route testing
def test_index_route():
	client = TestClient(app)
	response = client.get('/')
	assert response.status_code == 200
	assert "text/html" in response.headers["content-type"]


#background_runner testing

def test_background_runner(mocker):
	mock_fetch = mocker.patch("AIDaily.services.ArxivFetcher.fetch_one_paper")
	mock_fetch.return_value = None

	background_runner() #function call

	mock_fetch.assert_called()

#scheduler test
def test_scheduler_started():
    jobs = scheduler.get_jobs()
    assert any(job.id == "daily_paper_job" for job in jobs)
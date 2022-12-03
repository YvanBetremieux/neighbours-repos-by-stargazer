"""
Test module
"""
# -*- coding: utf-8 -*-
import pytest
from fastapi.testclient import TestClient

from stargazer.database.database import oauth2_scheme
from stargazer.main import app
from tests.resources.neighbours import neighbours

client = TestClient(app)


def test_healthz():
    """
    Test the endpoint to see if the api is running
    """
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == "The api is running"


def test_stargazer_not_authenticated():
    """
    Test main endpoint without authenticator user. Should reject the connexion with an error message
    """
    response = client.get("repos/tiangolo/alembic/starneighbours")
    assert response.json().get("detail") == "Not authenticated"


@pytest.fixture
def client_authenticated():
    """
    Returns an API client which skips the authentication
    """

    def skip_auth():
        pass

    app.dependency_overrides[oauth2_scheme] = skip_auth

    return TestClient(app)


def test_stargazer_authenticated(client_authenticated):
    """
    Test main endpoint with authenticator user. We mock the authentication for the test
    :param client_authenticated:
    """
    response = client_authenticated.get("repos/tiangolo/alembic/starneighbours")
    print(response.json())
    assert type(response.json()) == list
    assert len(response.json()) == 73
    assert response.json() == neighbours

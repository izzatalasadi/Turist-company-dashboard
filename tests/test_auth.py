import pytest
from name_search_engine.manage import app   # Import your Flask app creation logic

@pytest.fixture
def app():
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_login_success(client):
    """Test login with correct credentials."""
    response = client.post('/login', json={'username': 'admin', 'password': 'password'})
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_unauthorized_access(client):
    """Test accessing a protected route without a token."""
    response = client.get('/protected')
    assert response.status_code == 401

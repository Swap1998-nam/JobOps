from fastapi.testclient import TestClient
from app.main import app


def test_liveness_and_validation():
    with TestClient(app) as client:
        assert client.get('/health/live').json() == {'status': 'ok'}
        assert client.post('/api/applications', json={'company': '', 'role': 'DevOps'}).status_code == 422


def test_application_lifecycle():
    with TestClient(app) as client:
        result = client.post('/api/applications', json={'company': 'Example', 'role': 'Cloud Engineer'})
        assert result.status_code == 201
        item_id = result.json()['id']
        assert client.patch(f'/api/applications/{item_id}?status=interview').json()['status'] == 'interview'
        assert any(item['id'] == item_id and item['status'] == 'interview' for item in client.get('/api/applications').json())
        assert client.patch('/api/applications/0?status=offer').status_code == 404

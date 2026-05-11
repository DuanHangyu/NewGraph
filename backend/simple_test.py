"""简单测试"""
from app import create_app

app = create_app()

with app.test_client() as client:
    print("Testing GET /health:", client.get('/health').status_code)
    print("Testing GET /api/graph/project/list:", client.get('/api/graph/project/list').status_code)
    print("Testing POST /api/graph/ontology/generate:", client.post('/api/graph/ontology/generate').status_code)

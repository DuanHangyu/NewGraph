"""
测试API端点
"""
import sys
from app import create_app

def test_routes():
    app = create_app()

    with app.test_client() as client:
        # 测试health
        response = client.get('/health')
        print(f"GET /health: {response.status_code}")
        print(f"Response: {response.json}")

        # 测试project list
        response = client.get('/api/graph/project/list')
        print(f"\nGET /api/graph/project/list: {response.status_code}")
        print(f"Response: {response.json}")

        # 测试generate ontology (简化版，不传文件)
        response = client.post('/api/graph/ontology/generate')
        print(f"\nPOST /api/graph/ontology/generate: {response.status_code}")
        print(f"Response: {response.json}")

if __name__ == '__main__':
    test_routes()

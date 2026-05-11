"""
调试Flask路由
"""
import sys
from app import create_app

def debug_routes():
    app = create_app()

    print("=" * 60)
    print("All registered routes:")
    print("=" * 60)

    with app.app_context():
        for rule in app.url_map.iter_rules():
            print(f"{rule.rule:40} -> {rule.endpoint} ({', '.join(rule.methods - {'HEAD', 'OPTIONS'})})")

    print("\n" + "=" * 60)
    print("Testing with test client:")
    print("=" * 60)

    with app.test_client() as client:
        # Test routes
        routes_to_test = [
            '/health',
            '/api/graph/project/list',
            '/api/graph/ontology/generate'
        ]

        for route in routes_to_test:
            if 'POST' in [m for m in app.url_map.iter_rules() if route in r.rule for r in [r]][0] if any(route in r.rule for r in app.url_map.iter_rules()) else []:
                resp = client.post(route)
            else:
                resp = client.get(route)

            print(f"{route:40} -> {resp.status_code} {resp.data[:100] if resp.data else ''}")

if __name__ == '__main__':
    debug_routes()

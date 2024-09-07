import json
import json
import jwt
from datetime import datetime, timedelta, timezone

from app.user.model import User


def test_user_registration(test_client, init_database):
    response = test_client.post('/api/user/register',
                                data=json.dumps({
                                    'username': 'testuser',
                                    'first_name': 'Test',
                                    'last_name': 'User',
                                    'email': 'testuser@example.com',
                                    'password': 'testpassword'
                                }),
                                content_type='application/json')

    print(f"Status Code: {response.status_code}")
    print(f"Response Data: {response.data}")

    assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}"
    json_data = response.get_json()
    assert json_data['success'] == True, f"Expected 'success': True, but got {json_data.get('success')}"
    assert json_data[
               'message'] == 'Registered successfully!', f"Expected message 'Registered successfully!', but got '{json_data.get('message')}'"


def test_successful_registration(test_client, init_database):
    response = test_client.post('/api/user/register',
                                data=json.dumps({
                                    'username': 'testuser2',
                                    'first_name': 'Test2',
                                    'last_name': 'User2',
                                    'email': 'testuser2@test.com',
                                    'password': 'TestPassword123',
                                }),
                                content_type='application/json')
    assert response.status_code == 201
    assert b"Registered successfully" in response.data


def test_duplicate_registration(test_client, init_database):
    # First registration
    response1 = test_client.post('/api/user/register',
                                 data=json.dumps({
                                     'username': 'testuser2',
                                     'first_name': 'Test2',
                                     'last_name': 'User2',
                                     'email': 'testuser2@test.com',
                                     'password': 'TestPassword123',
                                 }),
                                 content_type='application/json')
    print(f"First registration response: {response1.status_code}, {response1.data}")

    # Second registration (duplicate)
    response2 = test_client.post('/api/user/register',
                                 data=json.dumps({
                                     'username': 'testuser2',
                                     'first_name': 'Test2',
                                     'last_name': 'User2',
                                     'email': 'testuser2@test.com',
                                     'password': 'TestPassword123',
                                 }),
                                 content_type='application/json')
    print(f"Second registration response: {response2.status_code}, {response2.data}")

    assert response2.status_code == 409
    assert b"Username or email already exists" in response2.data


def setup_test_user(test_client, init_database):
    test_client.post('/api/user/register',
                     data=json.dumps({
                         'username': 'testuser',
                         'first_name': 'Test',
                         'last_name': 'User',
                         'email': 'test@example.com',
                         'password': 'testpassword'
                     }),
                     content_type='application/json')


def test_successful_login(test_client, init_database):
    setup_test_user(test_client, init_database)
    response = test_client.post('/api/user/login',
                                data=json.dumps({
                                    'email': 'test@example.com',
                                    'password': 'testpassword'
                                }),
                                content_type='application/json')
    assert response.status_code == 200
    assert b"Successfully logged in" in response.data


def test_incorrect_login(test_client, init_database):
    setup_test_user(test_client, init_database)
    response = test_client.post('/api/user/login',
                                data=json.dumps({
                                    'email': 'test@example.com',
                                    'password': 'wrongpassword'
                                }),
                                content_type='application/json')
    assert response.status_code == 401
    assert b"Incorrect password" in response.data



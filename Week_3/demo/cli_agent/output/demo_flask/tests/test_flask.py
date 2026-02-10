import pytest
from flask import Flask
from src.flask import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_endpoint(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.data.decode('utf-8') == "Welcome to the minimal Flask project!"

def test_echo_get_endpoint(client):
    response = client.get('/echo?key1=value1&key2=value2')
    assert response.status_code == 200
    data = response.get_json()
    assert data['method'] == 'GET'
    assert data['data'] == {'key1': 'value1', 'key2': 'value2'}

def test_echo_get_endpoint_empty(client):
    response = client.get('/echo')
    assert response.status_code == 200
    data = response.get_json()
    assert data['method'] == 'GET'
    assert data['data'] == {}

def test_echo_post_endpoint_json(client):
    response = client.post('/echo', json={'key1': 'value1', 'key2': 'value2'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['method'] == 'POST'
    assert data['data'] == {'key1': 'value1', 'key2': 'value2'}

def test_echo_post_endpoint_form(client):
    response = client.post('/echo', data={'key1': 'value1', 'key2': 'value2'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['method'] == 'POST'
    assert data['data'] == {'key1': 'value1', 'key2': 'value2'}

def test_echo_post_endpoint_empty(client):
    response = client.post('/echo')
    assert response.status_code == 200
    data = response.get_json()
    assert data['method'] == 'POST'
    assert data['data'] is None

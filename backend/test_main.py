from fastapi.testclient import TestClient

from celery.result import AsyncResult
from app.celery_app import my_task, celery_app

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from db.models import User
from security.hashing import get_password_hash
from db.database import connect_to_db

import pytest

import base64
import json
import uuid

from .main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200

def test_celery_task_runs():
    result: AsyncResult = my_task.delay()

    completed = result.get(timeout=10)

    assert result.successful(), f"Task failed with state {result.state}"

def test_full_secure_aes_workflow(create_test_user):
    """
    Tests the entire secure flow using a user created by the fixture.
    """
    test_username, test_password = create_test_user

    client_private_key = x25519.X25519PrivateKey.generate()
    client_public_key = client_private_key.public_key()
    client_public_key_b64 = base64.b64encode(client_public_key.public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )).decode('utf-8')

    login_payload = {
        "username": test_username,
        "password": test_password,
        "client_public_key": client_public_key_b64
    }
    
    login_response = client.post("/api/auth/login", json=login_payload)
    assert login_response.status_code == 200, f"Secure login failed: {login_response.json()}"
    
    login_data = login_response.json()
    access_token = login_data["access_token"]
    server_public_key_b64 = login_data["server_public_key"]
    print("Step 1: Secure login successful.")

    # 2. DERIVE THE AES SESSION KEY (CLIENT-SIDE)
    server_public_key = x25519.X25519PublicKey.from_public_bytes(base64.b64decode(server_public_key_b64))
    shared_secret = client_private_key.exchange(server_public_key)
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'aes-session-key')
    aes_session_key = hkdf.derive(shared_secret)
    print("Step 2: AES session key derived successfully.")

    # 3. ACCESS A PROTECTED ENDPOINT WITH AES
    headers = {"Authorization": f"Bearer {access_token}", "X-ENFORCE-AES256": "1"}
    protected_response = client.get("/api/users/protected-data", headers=headers)
    assert protected_response.status_code == 200
    print("Step 3: Received encrypted response.")

    print(f"Server response: {protected_response.json()}")

    # 4. DECRYPT AND VERIFY THE RESPONSE
    decrypted_payload = decrypt_data(aes_session_key, protected_response.json())
    expected_payload = {"message": "This is some top secret protected data!"}
    assert decrypted_payload == expected_payload
    print(f"Step 4: Successfully decrypted response. Got: {decrypted_payload}")

def test_full_workflow_without_aes(create_test_user):
    """
    Tests the entire secure flow using a user created by the fixture.
    """
    test_username, test_password = create_test_user

    # the public key is not really needed but still have to pass it because its request requirement.
    client_private_key = x25519.X25519PrivateKey.generate()
    client_public_key = client_private_key.public_key()
    client_public_key_b64 = base64.b64encode(client_public_key.public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )).decode('utf-8')

    login_payload = {
        "username": test_username,
        "password": test_password,
        "client_public_key": client_public_key_b64
    }
    
    login_response = client.post("/api/auth/login", json=login_payload)
    assert login_response.status_code == 200, f"Secure login failed: {login_response.json()}"
    
    login_data = login_response.json()
    access_token = login_data["access_token"]
    server_public_key_b64 = login_data["server_public_key"]
    print("Step 1: Secure login successful.")

    # 3. ACCESS A PROTECTED ENDPOINT WITHOUT AES
    headers = {"Authorization": f"Bearer {access_token}", "X-ENFORCE-AES256": "1"}
    protected_response = client.get("/api/users/protected-data", headers=headers)
    assert protected_response.status_code == 200
    print("Step 3: Received encrypted response.")

    print(f"Server response: {protected_response.json()}")

    expected_payload = {"message": "This is some top secret protected data!"}
    assert protected_response.json() == expected_payload
    print(f"Step 4: Successfully decrypted response. Got: {protected_response.json()}")

def test_full_workflow_without_aes(create_test_user):
    """
    Tests the entire secure flow using a user created by the fixture.
    """
    test_username, test_password = create_test_user

    # the public key is not really needed but still have to pass it because its request requirement.
    client_private_key = x25519.X25519PrivateKey.generate()
    client_public_key = client_private_key.public_key()
    client_public_key_b64 = base64.b64encode(client_public_key.public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )).decode('utf-8')

    login_payload = {
        "username": test_username,
        "password": test_password,
        "client_public_key": client_public_key_b64
    }
    
    login_response = client.post("/api/auth/login", json=login_payload)
    assert login_response.status_code == 200, f"Secure login failed: {login_response.json()}"
    
    login_data = login_response.json()
    access_token = login_data["access_token"]
    server_public_key_b64 = login_data["server_public_key"]
    print("Step 1: Secure login successful.")


    # 3. ACCESS A PROTECTED ENDPOINT WITHOUT AES
    headers = {"Authorization": f"Bearer {access_token}", "X-ENFORCE-AES256": "0"}
    protected_response = client.get("/api/users/protected-data", headers=headers)
    assert protected_response.status_code == 200
    print("Step 3: Received encrypted response.")

    print(f"Server response: {protected_response.json()}")

    expected_payload = {"message": "This is some top secret protected data!"}
    assert protected_response.json() == expected_payload
    print(f"Step 4: Successfully decrypted response. Got: {protected_response.json()}")

def decrypt_data(aes_key: bytes, encoded_body: str) -> dict:
    """Decrypts a Base64 encoded string from the server."""
    try:
        encrypted_body = base64.b64decode(encoded_body)
        iv = encrypted_body[:16]
        encrypted_data = encrypted_body[16:]
        
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        decrypted_padded_data = cipher.decrypt(encrypted_data)
        decrypted_data = unpad(decrypted_padded_data, AES.block_size)
        
        return json.loads(decrypted_data.decode('utf-8'))
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        pytest.fail(f"Decryption failed: {e}")

@pytest.fixture(scope="function")
def create_test_user():
    connect_to_db()

    username = f"testuser_{uuid.uuid4().hex}"
    password = "a_very_strong_password"
    
    hashed_password = get_password_hash(password)
    test_user = User(username=username, hashed_password=hashed_password)
    test_user.merge()

    yield username, password

    User.delete(test_user.username)
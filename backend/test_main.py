from fastapi.testclient import TestClient

from celery.result import AsyncResult
from app.celery_app import my_task, celery_app

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from db.models import AuthUser
from security.hashing import get_password_hash
from db.database import connect_to_db

import pytest

import base64
import json
import uuid

from scanner_api_client.machine import Machine
from scanner_api_client.user import User
from scanner.vulnerabilities.password_too_old import PasswordTooOld
from scanner.vulnerabilities.weak_password import WeakPassword
from scanner.report import Report

from datetime import date
from db.db_service import load_report, persist_report

from main import app

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

    print(client_public_key_b64)

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

def test_save_report_in_db_and_make_sure_its_the_same_when_retrieved():
    connect_to_db()

    machine = Machine('WindowsXP-Living-Room', 'windows')
    user1 = User(machine, 'John', 'dasjioj23i', date(2025, 9, 22))
    user2 =  User(machine, 'Jackson', 'fasasdsi', date(2021, 2, 12))

    user1_vuln1 = WeakPassword(user1.ntlm_hash)
    user1_vuln2 = PasswordTooOld(user1.password_updated_at)

    user2_vuln1 = WeakPassword(user2.ntlm_hash)
    user2_vuln2 = PasswordTooOld(user2.password_updated_at)

    user1_vuln1._is_vulnrable = True
    user1_vuln2._is_vulnrable = True
    user2_vuln1._is_vulnrable = True
    user2_vuln2._is_vulnrable = True

    original_report_object = Report()
    original_report_object = original_report_object.add_result(user1, [user1_vuln1, user1_vuln2])
    original_report_object = original_report_object.add_result(user2, [user2_vuln1, user2_vuln2])

    report_node = persist_report(original_report_object)
    report_id = report_node.report_id

    report_entity_loaded_from_db = load_report(report_id)

    def remove_keys(d, ignore_keys):
        if isinstance(d, dict):
            return {k: remove_keys(v, ignore_keys) for k, v in d.items() if k not in ignore_keys}
        elif isinstance(d, list):
            return [remove_keys(i, ignore_keys) for i in d]
        else:
            return d
        
    def unorder(data, is_dict=False):
        if is_dict:
            return set(frozenset(frozenset(d.items()) for d in sublist) for sublist in data) # d is dict here
        else:
            return set(frozenset(sublist) for sublist in data)
    
    keys_to_ignore = {'id', 'uuid', 'created_at'}

    original_json = unorder(remove_keys(original_report_object.to_json(), keys_to_ignore))
    db_json = unorder(remove_keys(report_entity_loaded_from_db.to_json(), keys_to_ignore))

    assert original_json == db_json

@pytest.fixture(scope="function")
def create_test_user():
    connect_to_db()

    username = f"testuser_{uuid.uuid4().hex}"
    password = "a_very_strong_password"
    
    hashed_password = get_password_hash(password)
    test_user = AuthUser(username=username, hashed_password=hashed_password)
    test_user.merge()

    yield username, password

    AuthUser.delete(test_user.username)


# from unittest.mock import patch, MagicMock

# from db.models import ScheduledScan

# @patch('celery_app.redis_client')
# def test_schedule_pending_scans_acquires_lock_and_dispatches_task(mock_redis_client):
#     """
#     Tests that `schedule_pending_scans` correctly acquires a lock for a pending scan
#     and dispatches the `run_scheduled_scan` task.
#     """
#     # Arrange
#     # Configure the mock that was directly injected by the patcher
#     mock_redis_client.set.return_value = True  # Simulate successful lock acquisition

#     mock_scan = MagicMock(spec=ScheduledScan)
#     mock_scan.uuid = "test-uuid-1"

#     with patch('celery_app.ScheduledScan.match_nodes', return_value=[mock_scan]):
#         with patch('celery_app.run_scheduled_scan.delay') as mock_delay:
#             from celery_app import schedule_pending_scans

#             # Act
#             schedule_pending_scans()

#             # Assert
#             # Verify that we attempted to set the lock
#             mock_redis_client.set.assert_called_once_with(
#                 f"scan_lock:{mock_scan.uuid}", "locked", ex=600, nx=True
#             )

#             # Verify that the task was dispatched
#             mock_delay.assert_called_once_with(mock_scan.uuid)


# @patch('celery_app.redis_client')
# def test_schedule_pending_scans_skips_locked_scan(mock_redis_client):
#     """
#     Tests that `schedule_pending_scans` skips dispatching a task if the lock
#     is already held.
#     """
#     # Arrange
#     mock_redis_client.set.return_value = False  # Simulate that the lock is already taken

#     mock_scan = MagicMock(spec=ScheduledScan)
#     mock_scan.uuid = "test-uuid-2"

#     with patch('celery_app.ScheduledScan.match_nodes', return_value=[mock_scan]):
#         with patch('celery_app.run_scheduled_scan.delay') as mock_delay:
#             from celery_app import schedule_pending_scans

#             # Act
#             schedule_pending_scans()

#             # Assert
#             mock_redis_client.set.assert_called_once_with(
#                 f"scan_lock:{mock_scan.uuid}", "locked", ex=600, nx=True
#             )
#             mock_delay.assert_not_called()


# # Note the change in the first decorator and the last argument of the function
# @patch('celery_app.redis_client')
# @patch('celery_app.init_neontology')
# @patch('celery_app.ScheduledScan')
# @patch('celery_app.ReportNode')
# @patch('celery_app.CompletedAsRel')
# @patch('celery_app.scan_all_machines')
# def test_run_scheduled_scan_releases_lock_on_success(
#     mock_scan_all_machines,
#     mock_completed_as_rel,
#     mock_report_node,
#     mock_scheduled_scan,
#     mock_init_neontology,
#     mock_redis_client  # Corrected argument name
# ):
#     """
#     Tests that `run_scheduled_scan` releases the Redis lock after a successful scan.
#     """
#     # Arrange
#     scan_uuid = "test-uuid-3"
#     report_id = "report-123"

#     mock_scan_instance = MagicMock()
#     mock_scan_instance.completed_scan_id = None
#     mock_scheduled_scan.match.return_value = mock_scan_instance

#     mock_scan_all_machines.return_value = report_id

#     from celery_app import run_scheduled_scan

#     # Act
#     run_scheduled_scan(scan_uuid)

#     # Assert
#     mock_init_neontology.assert_called_once()
#     mock_scheduled_scan.match.assert_called_once_with(scan_uuid)
#     mock_scan_all_machines.assert_called_once()
#     mock_scan_instance.merge.assert_called()
#     mock_report_node.assert_called_with(report_id=report_id)
#     mock_report_node.return_value.merge.assert_called_once()
#     mock_completed_as_rel.assert_called_once()
#     mock_completed_as_rel.return_value.merge.assert_called_once()

#     # Crucially, assert that the lock was deleted
#     mock_redis_client.delete.assert_called_once_with(f"scan_lock:{scan_uuid}")


# # Note the change in the first decorator and the last argument of the function
# @patch('celery_app.redis_client')
# @patch('celery_app.init_neontology')
# @patch('celery_app.ScheduledScan')
# @patch('celery_app.scan_all_machines', side_effect=Exception("Scan failed"))
# def test_run_scheduled_scan_releases_lock_on_failure(
#     mock_scan_all_machines,
#     mock_scheduled_scan,
#     mock_init_neontology,
#     mock_redis_client  # Corrected argument name
# ):
#     """
#     Tests that `run_scheduled_scan` releases the Redis lock even when an exception occurs.
#     """
#     # Arrange
#     scan_uuid = "test-uuid-4"

#     mock_scan_instance = MagicMock()
#     mock_scan_instance.completed_scan_id = None
#     mock_scan_instance.retry_on_fail = False  # Disable retry for this test case
#     mock_scheduled_scan.match.return_value = mock_scan_instance

#     from celery_app import run_scheduled_scan

#     # Act
#     run_scheduled_scan(scan_uuid)

#     # Assert
#     mock_init_neontology.assert_called_once()
#     mock_scheduled_scan.match.assert_called_once_with(scan_uuid)
#     mock_scan_all_machines.assert_called_once()

#     # Crucially, assert that the lock was deleted even on failure
#     mock_redis_client.delete.assert_called_once_with(f"scan_lock:{scan_uuid}")


# @patch('celery_app.redis_client')
# def test_no_pending_scans(mock_redis_client):
#     """
#     Tests that `schedule_pending_scans` does nothing when there are no pending scans.
#     """
#     # Arrange
#     with patch('celery_app.ScheduledScan.match_nodes', return_value=[]):
#         with patch('celery_app.run_scheduled_scan.delay') as mock_delay:
#             from celery_app import schedule_pending_scans

#             # Act
#             schedule_pending_scans()

#             # Assert
#             mock_redis_client.set.assert_not_called()
#             mock_delay.assert_not_called()
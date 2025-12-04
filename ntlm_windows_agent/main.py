import os
import subprocess
import ctypes
import random
import string
import base64
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from waitress import serve
import logging
import socket
from scapy.all import sniff, IP
import threading
from datetime import datetime, timezone
import csv
import winreg

logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

load_dotenv()

SECRET = os.getenv("SECRET")
PORT = int(os.getenv("PORT", "8000"))
OS = "windows"
FRIENDLY_NAME = os.getenv("FRIENDLY_NAME")

DUO_RESULTS_FILENAME = "duo_results.txt"

app = Flask(__name__)

TARGET_DOMAINS = [
    "api.security.com",
    "api-1.duosecurity.com",
    "api-2.duosecurity.com",
    "api-3.duosecurity.com",
    "frame.duosecurity.com",
    "frame.duo.com",
    "duofederal.com",
    "duoauth.com",
    "okta.com",
    "auth0.com",
    "device.login.microsoftonline.com",
    "login.microsoftonline.com"
]

def safe_resolve(d):
    try: return socket.gethostbyname(d)
    except: return None

TARGET_IPS = [ip for ip in (safe_resolve(d) for d in TARGET_DOMAINS) if ip]

def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return False

def run_as_admin(command: str) -> str:
    try:
        prefix = (
            "[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false; "
            "$OutputEncoding = [Console]::OutputEncoding; "
        )
        full = prefix + command

        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", full],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False
        )
        if result.returncode != 0:
            raise RuntimeError(f"PowerShell error ({result.returncode}): {result.stderr.strip()}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def generate_random_string(length: int) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def get_file_contents(file_name: str) -> str:
    with open(file_name, "rb") as f:
        raw_bytes = f.read()

    return base64.b64encode(raw_bytes).decode("ascii")

@app.route("/", methods=["GET"])
def main():
    header_secret = request.headers.get("X-SECRET")

    if header_secret is None:
        return jsonify({"success": False, "error": "Missing authentication header"}), 400

    if header_secret != SECRET:
        return jsonify({"success": False, "error": "Invalid secret"}), 403

    sam_file_name = generate_random_string(10) 
    system_file_name = generate_random_string(10)

    run_as_admin(f"reg save HKLM\SAM {sam_file_name}")
    run_as_admin(f"reg save HKLM\SYSTEM {system_file_name}")

    sam_contents = get_file_contents(sam_file_name)
    system_contents = get_file_contents(system_file_name)

    os.remove(sam_file_name)
    os.remove(system_file_name)

    ps_command = r"Get-LocalUser | Select-Object Name,@{Name='PasswordLastSet';Expression={if ($_.PasswordLastSet) { $_.PasswordLastSet.ToString('yyyy-MM-dd HH:mm:ss') } else { $null }}} | ConvertTo-Json"
    passwords_last_updated_output = json.loads(run_as_admin(ps_command))

    return jsonify({
        "OS": OS,
        "friendly_name": FRIENDLY_NAME,
        "success": True, 
        "sam": sam_contents, 
        "system": system_contents, 
        "last_password_updated_dates": passwords_last_updated_output,
        "duo_last_time_detected": get_last_time_duo_was_used(),
        "is_windows_hello_enabled": windows_hello_enabled_for_each_user_results()
    })

def get_real_user_profiles():
    """
    Return list of (username, profile_path) for 'normal' users, profiles under C:\\Users\\
    """
    profiles = []
    key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"

    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
        i = 0
        while True:
            try:
                sid = winreg.EnumKey(key, i)
                with winreg.OpenKey(key, sid) as subkey:
                    profile_path, _ = winreg.QueryValueEx(subkey, "ProfileImagePath")
                    profile_path = os.path.expandvars(profile_path)

                    parent = os.path.basename(os.path.dirname(profile_path))
                    if parent.lower() != "users":
                        i += 1
                        continue

                    username = os.path.basename(profile_path)
                    profiles.append((username, profile_path))
                i += 1
            except OSError:
                break

    return profiles


def hello_enabled(profile_path):
    """
    Check if NGC folder exists & is non-empty (PIN/Hello enabled).
    Returns True / False.
    Any permission issue is treated as False.
    """
    ngc = os.path.join(profile_path, r"AppData\Local\Microsoft\Ngc")

    try:
        if not os.path.isdir(ngc):
            return False

        with os.scandir(ngc) as it:
            for _ in it:
                return True

        return False
    except PermissionError:
        return False

def windows_hello_enabled_for_each_user_results():
    result = []

    for username, path in get_real_user_profiles():
        enabled = hello_enabled(path)
        result.append({
            "Name": username,
            "WindowsHelloEnabled": enabled
        })

    return result

# returns False if duo was never detected or last time it was detected as a date in isoformat as a string
def get_last_time_duo_was_used():
    try:
        with open(DUO_RESULTS_FILENAME, newline="") as f:
            reader = csv.reader(f)
            first_row = next(reader, None)
            if first_row is None or len(first_row) < 2:
                return False
            else:
                return first_row[1]
    except FileNotFoundError:
        return False

def save_duo_result():
    dt = datetime.now(timezone.utc)
    iso = dt.isoformat()

    with open(DUO_RESULTS_FILENAME, 'w') as file:
        file.write(f"1,{iso}")

def check(pkt):
    if IP in pkt:
        if pkt[IP].src in TARGET_IPS:
            save_duo_result()
            
def sniff_duo():
    print(f"Monitoring traffic for duo multi-factor authentication...")
    sniff(prn=check, store=False)

if __name__ == "__main__":
    if not is_admin():
        raise PermissionError("You must run this application as an admin.")

    t = threading.Thread(target=sniff_duo, daemon=True)
    t.start()

    serve(
        app,
        host="0.0.0.0",
        port=PORT,
    )
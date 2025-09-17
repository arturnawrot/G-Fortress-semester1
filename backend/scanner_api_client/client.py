import requests
import base64

from scanner_api_client.windows_adapter import extract_sam_hashes

def get_machine_data(url: str, secret: str):
    res = requests.get(url, headers={'X-SECRET': secret}).json()

    if res['OS'] == 'windows':
        sam_contents = base64.b64decode(res['sam'])
        system_contents = base64.b64decode(res['system'])
        return extract_sam_hashes(sam_contents, system_contents)
    
    raise Exception(f"Your NTLM agent is misconfigured. It has an unsupported operating system: {res['OS']}")
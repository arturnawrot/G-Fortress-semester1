import requests
import base64
from scanner_api_client.user import User
from scanner_api_client.windows_adapter import extract_sam_hashes, parse_windows_ntlm_agent_response_into_user_list
from exceptions.ntlm_agent_bad_response import NTLMAgentBadResponse
from exceptions.ntlm_agent_connectivity_exception import NTLMAgentConnectivityException
from requests.exceptions import ConnectionError
from datetime import datetime
from typing import List

def get_machine_data(uri: str, secret: str) -> List[User]:
    try:
        res = requests.get(uri, headers={'X-SECRET': secret}).json()
    except ConnectionError:
        raise NTLMAgentConnectivityException(f"Failed to reach the NTLM agent '{uri}'. Check connectivity and configuration.")

    operating_system = res['OS']

    if operating_system == 'windows':
        return parse_windows_ntlm_agent_response_into_user_list(res)

    raise NTLMAgentBadResponse(f"Your NTLM agent is misconfigured. It has an unsupported operating system: {res['OS']}")
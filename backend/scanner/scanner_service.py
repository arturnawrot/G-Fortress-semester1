from config import settings
from scanner_api_client import client
from scanner.vulnerabilities.vulnerability_service import scan_user
from scanner.pdf_report import build_report_for_users

def scan_machine(machine_URI: str):
    return client.get_machine_data(machine_URI, settings.NTLM_AGENTS_SECRET)

def scan_all_machines():
    # machine_uris = settings.ntlm_agents_uris

    # for machine_uri in machine_uris:
    #     users = scan_machine(machine_uri)

    #     for user in users:
    #         print(user)
    #         print(scan_user(user))
    machine_uris = settings.ntlm_agents_uris
    users = [user for machine_uri in machine_uris for user in scan_machine(machine_uri)]
    build_report_for_users(users)
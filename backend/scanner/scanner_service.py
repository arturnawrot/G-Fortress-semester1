from config import settings
from scanner_api_client import client
from scanner.vulnerabilities.vulnerability_service import scan_user
from scanner.report import Report
from scanner.pdf_report import build_report_as_pdf

def scan_machine(machine_URI: str):
    return client.get_machine_data(machine_URI, settings.NTLM_AGENTS_SECRET)

def scan_all_machines():
    machine_uris = settings.ntlm_agents_uris
    users = [user for machine_uri in machine_uris for user in scan_machine(machine_uri)]

    report = Report()

    for user in users:
        report = report.add_result(user, scan_user(user))

    build_report_as_pdf(report, "test.pdf")
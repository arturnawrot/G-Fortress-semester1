from datetime import date
from scanner.vulnerabilities.vulnerability_interface import VulnerabilityInterface
import random

class PasswordTooOld(VulnerabilityInterface):

    def __init__(self, password_updated_at: date):
        self.date = password_updated_at

    def get_vulnerability_name(self) -> str:
        return "Password Too Old"

    def get_vulnerability_description(self) -> str:
        return "Too old passwords are dangerous because they have had more time to be exposed through data breaches, phishing attacks, or brute-force attempts, increasing the risk of unauthorized access."
    
    def check(self) -> bool:
        # @TODO to actually implement
        return random.choice([True, False])
    
    def get_description_of_the_detected_vulnerability(self) -> str:
        return "This password was updated 10 years ago last time. It's very likely it was breached somewhere meanwhile."
    
    def get_severity_score(self) -> int:
        return 6
        
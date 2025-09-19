from scanner.vulnerabilities.vulnerability_interface import VulnerabilityInterface
import random

class WeakPassword(VulnerabilityInterface):

    def __init__(self, ntlm_hash: str):
        self.ntlm_hash = ntlm_hash
    
    def get_vulnerability_name(self) -> str:
        return "Password Too Weak"

    def get_vulnerability_description(self) -> str:
        return "This password is too easy to guess or already leaked."
    
    def check(self) -> bool:
        # @TODO to actually implement
        return random.choice([True, False])
    
    def get_description_of_the_detected_vulnerability(self) -> str:
        return "This password is in one of the databases of breached or weak passwords."
    
    def get_severity_score(self) -> int:
        return 10
        
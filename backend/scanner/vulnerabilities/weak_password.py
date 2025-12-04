from scanner.vulnerabilities.vulnerability_interface import VulnerabilityInterface
from config import settings
from pathlib import Path
import random

class WeakPassword(VulnerabilityInterface):

    def __init__(self, ntlm_hash: str, is_vulnerable: bool | None = None):
        super().__init__(is_vulnerable=is_vulnerable)
        self.ntlm_hash = ntlm_hash
    
    def get_vulnerability_name(self) -> str:
        return "Password Too Weak"

    def get_vulnerability_description(self) -> str:
        return "This password is too easy to guess or already leaked."
    
    def ntlm_hash_in_wordlist(self) -> bool:
        win_ntlm_hashed_wordlist = settings.WIN_NTLM_HASHED_WORDLIST

        if not win_ntlm_hashed_wordlist.exists():
            raise FileNotFoundError(f"Wordlist not found: {win_ntlm_hashed_wordlist}")

        with win_ntlm_hashed_wordlist.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.strip().lower() == self.ntlm_hash.lower():
                    return True

        return False
    
    def check(self) -> bool:
        if settings.IS_DEMO_MODE:
            return random.choice([True, False])
        
        return self.ntlm_hash_in_wordlist()

    def get_description_of_the_detected_vulnerability(self) -> str:
        return "This password is in one of the databases of breached or weak passwords."
    
    def get_severity_score(self) -> int:
        return 10
        
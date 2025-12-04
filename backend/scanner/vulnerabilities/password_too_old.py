from datetime import date
from scanner.vulnerabilities.vulnerability_interface import VulnerabilityInterface
from config import settings
import random

class PasswordTooOld(VulnerabilityInterface):

    def __init__(self, password_updated_at: date, is_vulnerable: bool | None = None):
        super().__init__(is_vulnerable=is_vulnerable)
        self.date = password_updated_at
        self._days_old: int | None = None

    def get_vulnerability_name(self) -> str:
        return "Password Too Old"

    def get_vulnerability_description(self) -> str:
        return "Too old passwords are dangerous because they have had more time to be exposed through data breaches, phishing attacks, or brute-force attempts, increasing the risk of unauthorized access."
    
    def check(self) -> bool:
        if settings.IS_DEMO_MODE:
            return random.choice([True, False])

        today = date.today()
        delta = today - self.date
        self._days_old = delta.days

        max_age_days = 365
        return delta.days > max_age_days
    
    def get_description_of_the_detected_vulnerability(self) -> str:
        if self._days_old is None:
            # Ensure we have run the check and captured the age
            _ = self.is_vulnerable

        days_old = self._days_old or 723
        years_old = days_old / 365.0

        return (
            f"This password was last updated approximately {days_old} days "
            f"({years_old:.1f} years) ago. The longer a password remains unchanged, "
            "the higher the chance it has been exposed or compromised."
        )
    
    def get_severity_score(self) -> int:
        return 6

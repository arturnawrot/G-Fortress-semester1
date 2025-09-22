from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Mapping
from scanner.vulnerabilities.vulnerability_interface import VulnerabilityInterface
from scanner_api_client.user import User
from datetime import date, datetime
from enum import Enum
from decimal import Decimal
from typing import Any
import json

class ReportEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, User):
            return {
                "name": obj.name,
                "machine": {
                    "friendly_name": obj.machine.friendly_name,
                    "operating_system": obj.machine.operating_system
                },
                "ntlm_hash": obj.ntlm_hash,
                "password_updated_at": obj.password_updated_at.isoformat() if obj.password_updated_at else None,
                "uuid": obj.uuid
            }
        if isinstance(obj, VulnerabilityInterface):
            return {
                "name": obj.get_vulnerability_name(),
                "description": obj.get_vulnerability_description(),
                "detected_description": obj.get_description_of_the_detected_vulnerability(),
                "severity_score": obj.get_severity_score(),
                "is_vulnerable": obj.is_vulnerable
            }
        return super().default(obj)

# frozen set to True makes the class truly immutable
@dataclass(frozen=True)
class Report:

    users_to_vulnerabilities: Dict[User, Tuple[VulnerabilityInterface, ...]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now())

    @staticmethod
    def from_dict(data: Dict[User, List[VulnerabilityInterface]]) -> "Report":
        immutable_map: Dict[User, Tuple[VulnerabilityInterface, ...]] = {
            user: tuple(vulns) for user, vulns in data.items()
        }
        return Report(users_to_vulnerabilities=immutable_map)

    def add_result(self, user: User, vulns: List[VulnerabilityInterface]) -> "Report":
        new_map = dict(self.users_to_vulnerabilities)
        new_map[user] = tuple(vulns)
        return Report(users_to_vulnerabilities=new_map)

    def users(self) -> Tuple[User, ...]:
        return tuple(self.users_to_vulnerabilities.keys())

    def vulnerabilities_for(self, user: User) -> Tuple[VulnerabilityInterface, ...]:
        return self.users_to_vulnerabilities.get(user, tuple())

    def to_dict(self):
        return {
            "created_at": self.created_at.isoformat(),
            "users": [
                {
                    "user": user,  # ReportEncoder already knows how to serialize User
                    "vulnerabilities": list(vulns)  # and VulnerabilityInterface
                }
                for user, vulns in self.users_to_vulnerabilities.items()
            ]
        }

    def to_json(self):
        return json.dumps(self.to_dict(), cls=ReportEncoder, indent=2)
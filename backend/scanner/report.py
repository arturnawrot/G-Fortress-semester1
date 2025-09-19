from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Mapping
from scanner.vulnerabilities.vulnerability_interface import VulnerabilityInterface
from scanner_api_client.user import User

# frozen set to True makes the class truly immutable
@dataclass(frozen=True)
class Report:

    users_to_vulnerabilities: Dict[User, Tuple[VulnerabilityInterface, ...]] = field(default_factory=dict)

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
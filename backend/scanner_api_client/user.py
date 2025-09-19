from scanner_api_client.machine import Machine
from datetime import date
import uuid

class User:
    def __init__(self, machine: Machine, name: str, ntlm_hash: str, password_updated_at: date | None):
        self.machine = machine
        self.name = name
        self.ntlm_hash = ntlm_hash
        self.password_updated_at = password_updated_at
        self.uuid = self._generate_uuid()

    def __str__(self):
        return f"{self.name}:{self.machine.friendly_name}:{self.ntlm_hash[:6]}:{self.password_updated_at}:{self.uuid}"

    def _generate_uuid(self) -> str:
        password_date_str = self.password_updated_at.isoformat() if self.password_updated_at else "None"
        
        unique_string = f"{self.machine.friendly_name}:{self.name}:{password_date_str}"
        
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))
    
    def get_ntlm_hash(self):
        return self.ntlm_hash
    
    def get_password_updated_at(self):
        return self.password_updated_at

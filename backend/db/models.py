from __future__ import annotations
from typing import ClassVar, Optional
from datetime import datetime, date
from uuid import uuid4

from pydantic import Field, field_validator
from neontology import (
    BaseNode,
    BaseRelationship,
    related_nodes,
    related_property,
)

class AuthUser(BaseNode):
    __primarylabel__ = "User"
    __primaryproperty__ = "username"
    username: str
    hashed_password: str

class MachineNode(BaseNode):
    """
    (Machine)-[:HAS_USER]->(User)
    (Report)-[:SCANNED_MACHINE]->(Machine)
    """
    __primarylabel__: ClassVar[str] = "Machine"
    __primaryproperty__: ClassVar[str] = "friendly_name"

    friendly_name: str
    operating_system: Optional[str] = None

    # Convenience queries
    @related_nodes
    def users(self):
        return "MATCH (#ThisNode)-[:HAS_USER]->(u:User) RETURN u"

    @property
    @related_property
    def user_count(self) -> int:
        return "MATCH (#ThisNode)-[:HAS_USER]->(u:User) RETURN COUNT(DISTINCT u)"


class UserNode(BaseNode):
    """
    (Machine)-[:HAS_USER]->(User)-[:HAS_VULNERABILITY { ... }]->(Vulnerability)
    (Report)-[:INCLUDES_USER]->(User)
    """
    __primarylabel__: ClassVar[str] = "User"
    __primaryproperty__: ClassVar[str] = "uuid"

    # Keep your domain fields
    uuid: str = Field(default_factory=lambda: uuid4().hex)  # primary key
    name: str
    ntlm_hash: str
    password_updated_at: date | None = None
    # denormalized convenience
    machine_friendly_name: Optional[str] = None

    @field_validator("password_updated_at", mode="before")
    @classmethod
    def _coerce_date(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            # try datetime first, then date
            try:
                return datetime.fromisoformat(v).date()
            except ValueError:
                return date.fromisoformat(v)
        return v

    # Convenience queries
    @related_nodes
    def machine(self):
        return "MATCH (m:Machine)-[:HAS_USER]->(#ThisNode) RETURN m"

    @related_nodes
    def vulnerabilities(self):
        return "MATCH (#ThisNode)-[:HAS_VULNERABILITY]->(v:Vulnerability) RETURN v"

    @property
    @related_property
    def vulnerability_count(self) -> int:
        return "MATCH (#ThisNode)-[:HAS_VULNERABILITY]->(v:Vulnerability) RETURN COUNT(DISTINCT v)"


class VulnerabilityNode(BaseNode):
    """
    Generic vulnerability catalog node.
    Example kinds: 'WeakPassword', 'PasswordTooOld'
    """
    __primarylabel__: ClassVar[str] = "Vulnerability"
    __primaryproperty__: ClassVar[str] = "key"

    key: str  # e.g. "WeakPassword", "PasswordTooOld"
    name: str
    description: Optional[str] = None

    # Convenience queries
    @related_nodes
    def affected_users(self):
        return "MATCH (u:User)-[:HAS_VULNERABILITY]->(#ThisNode) RETURN u"

    @property
    @related_property
    def affected_user_count(self) -> int:
        return "MATCH (u:User)-[:HAS_VULNERABILITY]->(#ThisNode) RETURN COUNT(DISTINCT u)"


class ReportNode(BaseNode):
    """
    Represents one scan/report run.
    (Report)-[:SCANNED_MACHINE]->(Machine)
    (Report)-[:INCLUDES_USER]->(User)
    (User)-[:HAS_VULNERABILITY {detected_at, severity_score, is_vulnerable, description, report_id}]->(Vulnerability)
    """
    __primarylabel__: ClassVar[str] = "Report"
    __primaryproperty__: ClassVar[str] = "report_id"

    report_id: str = Field(default_factory=lambda: uuid4().hex)

    # timestamps (from Neontology cookbook pattern)
    merged: datetime = Field(default_factory=datetime.now)
    created: Optional[datetime] = Field(
        default=None,
        validate_default=True,
        json_schema_extra={"set_on_create": True},
    )

    # Convenience queries
    @related_nodes
    def machines(self):
        return "MATCH (#ThisNode)-[:SCANNED_MACHINE]->(m:Machine) RETURN m"

    @related_nodes
    def users(self):
        return "MATCH (#ThisNode)-[:INCLUDES_USER]->(u:User) RETURN u"

    @related_nodes
    def vulnerabilities(self):
        return """
        MATCH (#ThisNode)-[:INCLUDES_USER]->(u:User)-[:HAS_VULNERABILITY {report_id: #ThisNode.report_id}]->(v:Vulnerability)
        RETURN DISTINCT v
        """

    @property
    @related_property
    def finding_count(self) -> int:
        return """
        MATCH (#ThisNode)-[:INCLUDES_USER]->(u:User)-[hv:HAS_VULNERABILITY {report_id: #ThisNode.report_id}]->(v:Vulnerability)
        RETURN COUNT(hv)
        """


# ---------------------------
# Relationships
# ---------------------------

class HasUserRel(BaseRelationship):
    """
    (Machine)-[:HAS_USER]->(User)
    """
    __relationshiptype__: ClassVar[str] = "HAS_USER"
    source: MachineNode
    target: UserNode


class ScannedMachineRel(BaseRelationship):
    """
    (Report)-[:SCANNED_MACHINE]->(Machine)
    """
    __relationshiptype__: ClassVar[str] = "SCANNED_MACHINE"
    source: ReportNode
    target: MachineNode


class IncludesUserRel(BaseRelationship):
    """
    (Report)-[:INCLUDES_USER]->(User)
    """
    __relationshiptype__: ClassVar[str] = "INCLUDES_USER"
    source: ReportNode
    target: UserNode


class HasVulnerabilityRel(BaseRelationship):
    """
    (User)-[:HAS_VULNERABILITY { ... }]->(Vulnerability)

    We store per-scan (per-report) context as relationship properties:
    - detected_at: when this was detected
    - is_vulnerable: result of the check() for that scan
    - severity_score: 0-10 at detection time
    - description: finding-specific blurb
    - report_id: which report produced this finding (joins back to ReportNode)
    """
    __relationshiptype__: ClassVar[str] = "HAS_VULNERABILITY"

    source: UserNode
    target: VulnerabilityNode

    detected_at: datetime = Field(default_factory=datetime.utcnow)
    is_vulnerable: bool
    severity_score: int
    description: Optional[str] = None
    report_id: str

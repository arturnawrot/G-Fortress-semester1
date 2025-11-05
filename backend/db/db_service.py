from __future__ import annotations

import neo4j
from neontology import GraphConnection
from db.models import (
    MachineNode, UserNode, VulnerabilityNode, ReportNode,
    HasUserRel, ScannedMachineRel, IncludesUserRel, HasVulnerabilityRel
)
from scanner.report import Report
from typing import Dict, List, Optional
from datetime import date, datetime

from scanner_api_client.machine import Machine as DomainMachine
from scanner_api_client.user import User as DomainUser
from scanner.report import Report as DomainReport

from scanner.vulnerabilities.password_too_old import PasswordTooOld
from scanner.vulnerabilities.weak_password import WeakPassword
from scanner.vulnerabilities.vulnerability_interface import VulnerabilityInterface

def _vuln_catalog_key(v) -> str:
    """
    Stable catalog key for vulnerability nodes.
    Prefer the explicit name, fall back to class name.
    """
    try:
        name = v.get_vulnerability_name()
        if name and name.strip():
            return name.replace(" ", "")
    except Exception:
        pass
    return type(v).__name__

def persist_report(
    domain_report: Report,
    include_non_vulnerable: bool = False,
) -> ReportNode:
    report = ReportNode()
    report.merge()

    seen_machines = {}
    
    for domain_user, vulns in domain_report.users_to_vulnerabilities.items():
        mkey = domain_user.machine.friendly_name
        if mkey in seen_machines:
            machine_node = seen_machines[mkey]
        else:
            machine_node = MachineNode(
                friendly_name=domain_user.machine.friendly_name,
                operating_system=getattr(domain_user.machine, "operating_system", None),
            )
            machine_node.merge()
            ScannedMachineRel(source=report, target=machine_node).merge()
            seen_machines[mkey] = machine_node

        user_node = UserNode(
            uuid=domain_user.uuid,
            name=domain_user.name,
            ntlm_hash=domain_user.ntlm_hash,
            password_updated_at=domain_user.password_updated_at,
            machine_friendly_name=machine_node.friendly_name,
        )
        user_node.merge()

        HasUserRel(source=machine_node, target=user_node).merge()
        IncludesUserRel(source=report, target=user_node).merge()

        for v in vulns:
            is_vuln = v.is_vulnerable

            # if not include_non_vulnerable and not is_vuln:
            #     continue

            key = _vuln_catalog_key(v)
            v_node = VulnerabilityNode(
                key=key,
                name=getattr(v, "get_vulnerability_name", lambda: key)(),
                description=getattr(v, "get_vulnerability_description", lambda: None)(),
            )
            v_node.merge()

            severity_score = int(v.get_severity_score())

            finding_desc = v.get_description_of_the_detected_vulnerability()


            HasVulnerabilityRel(
                source=user_node,
                target=v_node,
                is_vulnerable=bool(is_vuln),
                severity_score=severity_score,
                description=finding_desc,
                report_id=report.report_id,
            ).merge()

    return report


def _instantiate_domain_vuln(
    key_or_name: str,
    user_ntlm_hash: str,
    user_password_date: Optional[date],
    is_vulnerable: Optional[bool],
    severity_score: Optional[int],
    finding_desc: Optional[str],
) -> VulnerabilityInterface:
    norm = (key_or_name or "").replace(" ", "").lower()
    if norm in ("weakpassword", "passwordtooweak"):
        v: VulnerabilityInterface = WeakPassword(ntlm_hash=user_ntlm_hash, is_vulnerable=is_vulnerable)
    elif norm in ("passwordtooold",):
        v = PasswordTooOld(password_updated_at=user_password_date, is_vulnerable=is_vulnerable)
    else:
        class _Generic(VulnerabilityInterface):
            def __init__(self, name: str, is_vulnerable: Optional[bool]):
                super().__init__(is_vulnerable=is_vulnerable); self._name = name
            def get_vulnerability_name(self) -> str: return key_or_name or "UnknownVuln"
            def get_vulnerability_description(self) -> str: return "Imported from catalog."
            def check(self) -> bool: return bool(self._is_vulnerable)
            def get_description_of_the_detected_vulnerability(self) -> str: return finding_desc or ""
            def get_severity_score(self) -> int: return int(severity_score or 0)
        v = _Generic(key_or_name or "UnknownVuln", is_vulnerable)

    if severity_score is not None:
        v.get_severity_score = (lambda s=severity_score: int(s))     # type: ignore[attr-defined]
    if finding_desc is not None:
        v.get_description_of_the_detected_vulnerability = (lambda d=finding_desc: d)  # type: ignore[attr-defined]

    return v


def load_report(report_id: str) -> DomainReport:
    gc = GraphConnection()

    cypher = """
    MATCH (r:Report {report_id: $rid})-[:INCLUDES_USER]->(u:User)
    MATCH (m:Machine)-[:HAS_USER]->(u)
    OPTIONAL MATCH (u)-[hv:HAS_VULNERABILITY {report_id: $rid}]->(v:Vulnerability)
    RETURN
      m.friendly_name           AS machine_name,
      m.operating_system        AS machine_os,
      u.uuid                    AS user_uuid,
      u.name                    AS user_name,
      u.ntlm_hash               AS user_ntlm,
      u.password_updated_at     AS user_pwd_date,
      u.hash_algorithm          AS user_hash_algorithm,
      u.salt                    AS user_salt,
      u.rounds                  AS user_rounds,
      v.key                     AS v_key,
      v.name                    AS v_name,
      hv.is_vulnerable          AS hv_is_vuln,
      hv.severity_score         AS hv_severity,
      hv.description            AS hv_desc
    ORDER BY user_name ASC
    """

    # evaluate_query returns a NeontologyResult; use .records_raw for driver rows
    result = gc.evaluate_query(cypher, {"rid": report_id})
    rows = result.records_raw  # list[neo4j.Record]

    users_map: Dict[str, Dict] = {}
    for row in rows:
        m_name = row["machine_name"]
        m_os   = row["machine_os"]
        u_uuid = row["user_uuid"]
        u_name = row["user_name"]
        u_ntlm = row["user_ntlm"]
        u_hash_algorithm = row['user_hash_algorithm']
        u_salt = row['user_salt']
        u_rounds = row['user_rounds']

        u_pwd_date = row["user_pwd_date"]
        if isinstance(u_pwd_date, datetime):
            u_pwd_date = u_pwd_date.date()

        if u_uuid not in users_map:
            d_machine = DomainMachine(friendly_name=m_name, operating_system=m_os)
            d_user = DomainUser(
                machine=d_machine,
                name=u_name,
                ntlm_hash=u_ntlm,
                password_updated_at=u_pwd_date,
                hash_algorithm=u_hash_algorithm,
                salt=u_salt,
                rounds=u_rounds
            )
            users_map[u_uuid] = {"domain_user": d_user, "vulns": []}

        v_key = row["v_key"]
        v_name = row["v_name"]
        if v_key or v_name:
            raw_hv_is_vuln = row["hv_is_vuln"]
            hv_is_vuln_bool = raw_hv_is_vuln if isinstance(raw_hv_is_vuln, bool) else str(raw_hv_is_vuln).lower() == 'true' if raw_hv_is_vuln is not None else None

            v = _instantiate_domain_vuln(
                key_or_name=v_key or v_name,
                user_ntlm_hash=u_ntlm,
                user_password_date=u_pwd_date,
                is_vulnerable=hv_is_vuln_bool,
                severity_score=row["hv_severity"],
                finding_desc=row["hv_desc"],
            )
            users_map[u_uuid]["vulns"].append(v)

    domain_map = {info["domain_user"]: info["vulns"] for info in users_map.values()}

    created_at = ReportNode.match(report_id).merged

    return DomainReport.from_dict(domain_map, id=report_id, created_at=created_at)


def load_latest_report() -> DomainReport:
    gc = GraphConnection()
    rid = gc.evaluate_query_single("""
        MATCH (r:Report)
        RETURN r.report_id
        ORDER BY r.merged DESC
        LIMIT 1
    """)

    return load_report(rid)

def list_reports(order, page_size, skip):
    gc = GraphConnection()
    
    cypher = f"""
    MATCH (r:Report)
    WITH COUNT(r) AS total
    MATCH (r:Report)
    WITH total, r,
         (CASE WHEN r.merged IS NULL THEN
              (CASE WHEN '{order}' = 'ASC' THEN datetime({{epochMillis:0}}) ELSE datetime() END)
              ELSE r.merged END) AS created_sort
    ORDER BY created_sort {order}, r.report_id ASC
    SKIP $skip
    LIMIT $limit
    RETURN total,
           COLLECT({{ report_id: r.report_id, created: r.created }}) AS items
    """

    result = gc.engine.driver.execute_query(
        cypher,
        parameters_={"skip": skip, "limit": page_size},
        result_transformer_=neo4j.Result.single,
    )

    if result == None:
        return []
    
    data = result.data()
    total = data.get("total", 0)

    if total and skip >= total:
        return []

    items = data.get("items", [])
    return [load_report(item["report_id"]).to_json() for item in items]
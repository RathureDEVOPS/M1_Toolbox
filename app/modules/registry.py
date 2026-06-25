from dataclasses import dataclass

from app.modules.auth_audit import MODULE as AUTH_AUDIT_MODULE
from app.modules.base import ModuleDescriptor
from app.modules.gobuster import MODULE as GOBUSTER_MODULE
from app.modules.hydra import MODULE as HYDRA_MODULE
from app.modules.nikto import MODULE as NIKTO_MODULE
from app.modules.nmap import MODULE as NMAP_MODULE
from app.modules.sqlmap import MODULE as SQLMAP_MODULE
from app.modules.sslyze import MODULE as SSLYZE_MODULE
from app.modules.theharvester import MODULE as THEHARVESTER_MODULE
from app.modules.whatweb import MODULE as WHATWEB_MODULE
from app.modules.wireshark import MODULE as WIRESHARK_MODULE


@dataclass(frozen=True)
class ModulePoleGroup:
    identifier: str
    label: str
    needs: str
    modules: list[ModuleDescriptor]


def list_modules() -> list[ModuleDescriptor]:
    return [
        NMAP_MODULE,
        HYDRA_MODULE,
        WIRESHARK_MODULE,
        WHATWEB_MODULE,
        THEHARVESTER_MODULE,
        GOBUSTER_MODULE,
        SSLYZE_MODULE,
        NIKTO_MODULE,
        SQLMAP_MODULE,
        AUTH_AUDIT_MODULE,
    ]


def list_module_groups() -> list[ModulePoleGroup]:
    modules_by_id = {module.identifier: module for module in list_modules()}
    group_definitions = (
        (
            "security",
            "Securite (SOC, EDR, XDR)",
            "Tests cibles sur les systemes de detection et les flux",
            ("nmap", "wireshark"),
        ),
        (
            "saas",
            "Developpement SaaS",
            "Tests d'applications web et API",
            ("whatweb", "theharvester", "gobuster", "sqlmap"),
        ),
        (
            "infrastructure",
            "Infrastructure",
            "Evaluation des systemes internes et reseaux",
            ("hydra",),
        ),
        (
            "support-client",
            "Support client",
            "Tests de securite des outils de communication",
            ("nikto", "sslyze"),
        ),
        (
            "rh-admin",
            "RH / Administration",
            "Pentest des outils internes de gestion",
            ("auth-audit",),
        ),
    )

    groups: list[ModulePoleGroup] = []
    for identifier, label, needs, module_ids in group_definitions:
        groups.append(
            ModulePoleGroup(
                identifier=identifier,
                label=label,
                needs=needs,
                modules=[modules_by_id[module_id] for module_id in module_ids if module_id in modules_by_id],
            )
        )
    return groups

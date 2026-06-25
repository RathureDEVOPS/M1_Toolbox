from dataclasses import dataclass

from app.modules.base import ModuleDescriptor


@dataclass(frozen=True)
class NmapScriptOption:
    key: str
    label: str
    description: str


MODULE = ModuleDescriptor(
    identifier="nmap",
    name="Nmap",
    description="Reconnaissance et scan reseau via CLI securisee.",
    category="reconnaissance",
    source="builtin",
)

SCRIPT_OPTIONS = (
    NmapScriptOption("http-title", "http-title", "Recupere le titre de la page exposee."),
    NmapScriptOption("http-headers", "http-headers", "Affiche les en-tetes HTTP retournes."),
    NmapScriptOption("ssl-cert", "ssl-cert", "Inspecte le certificat TLS si disponible."),
    NmapScriptOption("ssh-hostkey", "ssh-hostkey", "Liste les cles publiques exposees par SSH."),
    NmapScriptOption("banner", "banner", "Recupere les bannieres de service accessibles."),
    NmapScriptOption("vuln", "vuln", "Lance la categorie NSE orientee vulnerabilites."),
)

ALLOWED_SCRIPT_KEYS = {option.key for option in SCRIPT_OPTIONS}

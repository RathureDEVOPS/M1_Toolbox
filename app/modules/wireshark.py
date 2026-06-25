from app.modules.base import ModuleDescriptor


MODULE = ModuleDescriptor(
    identifier="wireshark",
    name="Wireshark",
    description="Capture reseau courte via tshark avec resume des trames et statistiques de flux.",
    category="network",
    source="builtin",
)

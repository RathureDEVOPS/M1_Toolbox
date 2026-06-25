from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleDescriptor:
    identifier: str
    name: str
    description: str
    category: str
    source: str

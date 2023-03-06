from dataclasses import dataclass, field


@dataclass
class Device:
    name: str = field(init=False)
    fqdn: str = field(repr=False)
    vendor: str
    model: str
    tenant: str | None
    location: str
    ip: str | None

    def __post_init__(self):
        self.name = self.fqdn.split(".")[0]


@dataclass
class Vlans:
    setup: int | None
    untagged: int | None
    tagged: list[int] = field(default_factory=list)


@dataclass
class Interface:
    name: str
    vlans: Vlans
    description: str = ""

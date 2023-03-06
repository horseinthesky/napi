from dataclasses import dataclass, field
from enum import StrEnum, auto


class AutoName(StrEnum):
    def _generate_next_value_(name, *_):
        return name.lower()


class LinkType(AutoName):
    ACCESS = auto()
    TRUNK = auto()


@dataclass
class BaseL2Interface:
    name: str
    mode: LinkType | None = LinkType.ACCESS
    pvid: int | None = 1
    trunk_allowed_vlans: list[int] = field(default_factory=lambda: [1])

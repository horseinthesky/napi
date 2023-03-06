from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Any, Self

from napi.driver.abstract import BaseL2Interface, LinkType
from napi.lib import _flatten


class AutoName(StrEnum):
    def _generate_next_value_(name, *_):
        return name.lower()


class L2(AutoName):
    ENABLE = auto()
    DISABLE = auto()


@dataclass
class L2Interface(BaseL2Interface):
    def __post_init__(self) -> None:
        self._l2: L2 | None = L2.ENABLE

    def empty(self) -> Self:
        instance = self.__class__(
            name=self.name,
            mode=None,
        )
        instance._l2 = None

        return instance

    def as_dict(self) -> dict[str, Any]:
        r: dict[str, Any] = {
            "ifName": self.name,
            "l2Enable": self._l2,
            "l2Attribute": {},
        }

        if self.mode is not None:
            r["l2Attribute"] = {
                "linkType": self.mode,
                "pvid": str(self.pvid),
            }

        if self.mode is LinkType.TRUNK:
            r["l2Attribute"]["trunkVlans"] = ",".join(str(v) for v in self.trunk_allowed_vlans)

        return r

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> Self:
        interface = cls(
            name=data["ifName"],
            mode=LinkType.ACCESS if data["l2Attribute"]["linkType"] == "access" else LinkType.TRUNK,
            pvid=int(data["l2Attribute"]["pvid"]),
        )

        if interface.mode is LinkType.TRUNK:
            interface.trunk_allowed_vlans = [
                int(vlan) for vlan in _flatten(data["l2Attribute"]["trunkVlans"])
            ]

        return interface


@dataclass
class InterfaceTree:
    interfaces: list[L2Interface] = field(default_factory=list)

    def __post_init__(self):
        self.xmlns = "http://www.huawei.com/netconf/vrp/huawei-ethernet"

    def as_dict(self) -> dict[str, Any]:
        return {
            "ethernet": {
                "@xmlns": self.xmlns,
                "ethernetIfs": {
                    "ethernetIf": [interface.as_dict() for interface in self.interfaces],
                },
            },
        }

    def add_interface(self, interface: L2Interface) -> None:
        self.interfaces.append(interface)


@dataclass
class Peer:
    address: str

    def __post_init__(self):
        self.is_ignored = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "bgpPeer": {
                "peerAddr": self.address,
                "isIgnore": self.is_ignored,
            },
        }


@dataclass
class VRF:
    name: str
    peers: list[Peer] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "bgpVrf": {
                "vrfName": self.name,
                "bgpPeers": [peer.as_dict() for peer in self.peers],
            }
        }

    def add_peer(self, peer: Peer) -> None:
        self.peers.append(peer)


@dataclass
class BGPTree:
    vrfs: list[VRF] = field(default_factory=list)

    def __post_init__(self):
        self.xmlns = "http://www.huawei.com/netconf/vrp/huawei-bgp"

    def as_dict(self) -> dict[str, Any]:
        return {
            "bgp": {
                "@xmlns": self.xmlns,
                "bgpcomm": {
                    "bgpVrfs": [vrf.as_dict() for vrf in self.vrfs],
                },
            },
        }

    def add_vrf(self, vrf: VRF) -> None:
        self.vrfs.append(vrf)

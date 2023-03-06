from typing import Protocol, Self, Type

from napi.inventory import Device

from .ce import CEDriver
from .cumulus import CumulusDriver


class SupportsGetMacs(Protocol):
    def __init__(self, device: Device) -> None:
        ...

    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(self, *_) -> None:
        ...

    async def get_macs(self, vlan_id: str | None = None) -> list[dict[str, str]]:
        ...


driver_map: dict[str, Type[SupportsGetMacs]] = {
    "huawei": CEDriver,
    "nvidia": CumulusDriver,
}

__all__ = [
    "CEDriver",
    "CumulusDriver",
    "driver_map",
]

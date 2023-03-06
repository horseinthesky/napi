from typing import Protocol, Type, Self

from .exceptions import InventoryException, inventory_http_code_map
from .inventory import Device, Interface, Vlans
from .netbox import Netbox


class SupportsGetDeviceInterface(Protocol):
    def __init__(self, api_url: str) -> None:
        ...

    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(self, *_) -> None:
        ...

    async def get_device(self, name: str, domains: list[str], roles: list[str] | None) -> Device:
        ...

    async def get_interface(self, name: str, device: Device) -> Interface:
        ...


inventory_map: dict[str, Type[SupportsGetDeviceInterface]] = {
    "netbox": Netbox,
}


def inventory_handler(kind: str, *args, **kwargs) -> SupportsGetDeviceInterface:
    return inventory_map[kind](*args, **kwargs)


__all__ = [
    "Device",
    "Interface",
    "Vlans",
    "InventoryException",
    "inventory_http_code_map",
    "inventory_hander",
]

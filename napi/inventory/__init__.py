from typing import Protocol, Type, Self

from .exceptions import InventoryException, inventory_http_code_map
from .inventory import Device, Interface, Vlans
from .netbox import Netbox


class SupportsGetDeviceInterface(Protocol):
    """
    SupportsGetDeviceInterface is an interface any SoT must support.

    It must support an async context manager and implement two main methods:
        get_device: returns a Device object from the SoT
        get_interface: returns an Interface object from the SoT

    """
    def __init__(self, api_url: str) -> None:
        """
        Args:
            api_url: url to reach API of the SoT

        Returns:
            None

        Raises:
            N/A
        """
        ...

    async def __aenter__(self) -> Self:
        """
        Enter method for context manager

        Args:
            N/A

        Returns:
            Self: an instance of SoT object

        Raises:
            N/A
        """
        ...

    async def __aexit__(self, *_) -> None:
        """
        Exit method to cleanup for context manager

        Args:
            exception_type: exception type being raised
            exception_value: message from exception being raised
            traceback: traceback from exception being raised

        Returns:
            None

        Raises:
            N/A
        """
        ...

    async def get_device(self, name: str, domains: list[str], roles: list[str] | None) -> Device:
        """
        Grabs the device information from the SoT using its name.
        Checks every domain in the domains list and has one of the roles provided.

        Args:
            name: name of the device
            domains: a list of domains to fqdn might be end with
            roles: a list of roles to look for (might save some compute on the backend)

        Returns:
            Device: a bundled device information

        Raises:
            N/A
        """
        ...

    async def get_interface(self, name: str, device: Device) -> Interface:
        """
        Grabs the devices interface information from the SoT using the interface name and the device it belongs to.

        Args:
            name: name of the interface
            device: a device object which is expected to have the interface

        Returns:
            Interface: a bundled interface information

        Raises:
            N/A
        """
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

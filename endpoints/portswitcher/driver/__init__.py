from typing import Protocol, Type, Self

from napi.inventory import Device, Interface

from .ce import CEDriver
from .cumulus import CumulusDriver


class SupportsGetSetState(Protocol):
    def __init__(self, device: Device, interface: Interface) -> None:
        ...

    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(self, *_) -> None:
        ...

    async def get_state(self) -> str:
        ...

    async def set_state(self, desired_state: str) -> None:
        ...


driver_map: dict[str, Type[SupportsGetSetState]] = {
    "huawei": CEDriver,
    "nvidia": CumulusDriver,
}

__all__ = [
    "CEDriver",
    "MellanoxDriver",
    "driver_map",
]

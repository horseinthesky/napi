import json
from typing import Any

from napi.driver import CLIDriver
from napi.driver.cli.cumulus import L2Interface, LinkType
from napi.inventory import Device, Interface

from .exceptions import ConfigurationError


class CumulusDriver(CLIDriver):
    """
    CEDriver is the portswitcher API driver class for CLI-only devices.

    It provides the network device interaction for this API.
    """
    def __init__(self, device: Device, interface: Interface) -> None:
        """
        The constructor method.

        Sets "state" mapping - what L2 mode and VLANs are valid for what "state"

        Args:
            device: inventory device object has all necessary info about the device
            interface: inventory interface object has all necessary info about the interface

        Returns:
            None

        Raises:
            N/A
        """
        super().__init__(device.ip or device.fqdn, device.vendor)

        self.device = device
        self.interface = interface

        self.config_map = {
            "prod": L2Interface(
                name=self.interface.name,
                mode=LinkType.TRUNK,
                pvid=self.interface.vlans.untagged,
                trunk_allowed_vlans=self.interface.vlans.tagged,
            ),
            "setup": L2Interface(
                name=self.interface.name,
                mode=LinkType.ACCESS,
                pvid=self.interface.vlans.setup,
            ),
        }

    async def _get_interface_vlans(self) -> dict[str, Any]:
        """
        Actually sends the commands for get_state/set_state methods
        to avoid code duplication.

        Args:
            None

        Returns:
            dict[str, Any]: any JSON response converted to native python object

        Raises:
            ValueError: the device response is an empty string
        """
        command = f"bridge -j vlan show dev {self.interface.name}"

        intf_state_json = await self.send_command(command)
        if intf_state_json == "":
            raise ValueError("no interface data")

        intf_info = json.loads(intf_state_json)

        return intf_info[0]

    async def set_state(self, desired_state: str) -> None:
        """
        Configure the device interface to the desired state

        Args:
            desired_state: desired stare - "prod" or "setup"

        Returns:
            None

        Raises:
            N/A
        """
        try:
            actual_interface_state = await self._get_interface_vlans()
        except ValueError:
            raise ConfigurationError(
                f"no interface {self.interface.name} on the box {self.device.fqdn}"
            )

        response = await self.send_commands(
            cmds=self.config_map[desired_state].to_cmd(clear=actual_interface_state)
        )

        if "No such device" in response:
            raise ConfigurationError(
                f"no interface {self.interface.name} on the box {self.device.fqdn}"
            )

    async def get_state(self) -> str:
        """
        Get the device real interface state from the network device

        Args:
            None

        Returns:
            str: the network device interface state - "prod"/"setup"/"unknown"

        Raises:
            ConfigurationError: the real device does not has an interface it has in the inventory
        """
        try:
            actual_interface_state = await self._get_interface_vlans()
        except ValueError:
            raise ConfigurationError(
                f"no interface {self.interface.name} on the box {self.device.fqdn}"
            )

        actual_interface_config = L2Interface.from_data(
            self.interface.name, actual_interface_state
        )

        for state, desired_interface_config in self.config_map.items():
            if desired_interface_config == actual_interface_config:
                return state

        return (
            "unknown: "
            f"mode={actual_interface_config.mode}, "
            f"pvid={actual_interface_config.pvid}, "
            f"allowed vlans={actual_interface_config.trunk_allowed_vlans}"
        )

    # NVUE version
    # async def set_state(self, desired_state: str) -> None:
    #     response = await self.send_commands(cmds=self.config_map[desired_state])
    #
    #     if "INTERNAL SERVER ERROR" in response:
    #         raise ConfigurationError("NVUE error")
    #
    #     if "Invalid config" in response:
    #         raise ConfigurationError("attempt to apply an invalid config")

    # async def get_state(self) -> str:
    #     command = f"net show interface {self.interface.name} json"
    #     intf_state_json = await self.send_command(command)
    #     intf_info = json.loads(intf_state_json)
    #
    #     if intf_info["mode"] == "NotConfigured":
    #         raise ConfigurationError(
    #             f"no interface {self.interface.name} on the box {self.device.fqdn}"
    #         )
    #
    #     if "L2" not in intf_info["mode"]:
    #         return "l3"
    #
    #     actual_interface_config = L2Interface.from_data(self.interface.name, intf_info)
    #
    #     for state_name, desired_interface_config in self.config_map.items():
    #         if desired_interface_config == actual_interface_config:
    #             return state_name
    #
    #     return (
    #         "unknown: "
    #         f"mode={actual_interface_config.mode}, "
    #         f"pvid={actual_interface_config.pvid}, "
    #         f"allowed vlans={actual_interface_config.trunk_allowed_vlans}"
    #     )

from napi.driver import NetconfDriver
from napi.driver.netconf.ce import InterfaceTree, L2Interface, LinkType
from napi.inventory import Device, Interface

from .exceptions import ConfigurationError


class CEDriver(NetconfDriver):
    """
    CEDriver is the portswitcher API driver class for NETCONF-enabled devices.

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
        super().__init__(device.ip or device.fqdn)

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
        config = InterfaceTree(interfaces=[self.config_map[desired_state]])
        await self.edit_config(config=config)

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
        filter_ = InterfaceTree(
            interfaces=[
                L2Interface(name=self.interface.name).empty(),
            ],
        )
        rpc_reply = await self.get_config(filter_=filter_)

        ethernet = rpc_reply["rpc-reply"]["data"]
        if ethernet is None:
            raise ConfigurationError(
                f"no interface {self.interface.name} on the box {self.device.fqdn}"
            )

        interface_info = ethernet["ethernet"]["ethernetIfs"]["ethernetIf"]
        if interface_info["l2Enable"] == "disable":
            return "l3"

        actual_interface_config = L2Interface.from_data(interface_info)

        for state, desired_interface_config in self.config_map.items():
            if desired_interface_config == actual_interface_config:
                return state

        return (
            "unknown: "
            f"mode={actual_interface_config.mode}, "
            f"pvid={actual_interface_config.pvid}, "
            f"allowed vlans={actual_interface_config.trunk_allowed_vlans}"
        )

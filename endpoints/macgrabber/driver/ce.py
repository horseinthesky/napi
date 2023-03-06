from napi.driver import NetconfDriver
from napi.inventory import Device
from napi.lib import _mac_dash_to_column

from .exceptions import ConfigurationError


class CEDriver(NetconfDriver):
    def __init__(self, device: Device) -> None:
        super().__init__(device.ip or device.fqdn)
        self.device = device

    async def get_macs(self, vlan_id: str | None = None) -> list[dict[str, str]]:
        data = {
            "mac": {
                "@xmlns": "http://www.huawei.com/netconf/vrp/huawei-mac",
                "vlanFdbDynamics": {
                    "vlanFdbDynamic": {
                        "vlanId": vlan_id,
                        "macAddress": None,
                        "outIfName": None,
                    }
                },
            }
        }

        rpc_reply = await self.get(filter_=data)

        mac_tree = rpc_reply["rpc-reply"]["data"]

        mac_tree = {
            "mac": {
                "vlanFdbDynamics": {
                    "vlanFdbDynamic": [
                        {
                            "vlanId": "104",
                            "macAddress": "529a-0097-e41b",
                            "outIfName": "100GE1/0/1:1",
                        },
                        {
                            "vlanId": "104",
                            "macAddress": "529a-0097-e41c",
                            "outIfName": "100GE1/0/1:2",
                        },
                        {
                            "vlanId": "106",
                            "macAddress": "629a-0097-e41c",
                            "outIfName": "100GE1/0/1:5",
                        },
                    ],
                },
            },
        }

        if mac_tree is None:
            raise ConfigurationError(f"no mac-address data on {self.device.fqdn}")

        vlan_db_dynamic = mac_tree["mac"]["vlanFdbDynamics"]["vlanFdbDynamic"]
        if not isinstance(vlan_db_dynamic, list):
            vlan_db_dynamic = [vlan_db_dynamic]

        return [
            {
                "vlan": entry["vlanId"],
                "mac": _mac_dash_to_column(entry["macAddress"]),
                "interface": entry["outIfName"],
            }
            for entry in vlan_db_dynamic
        ]

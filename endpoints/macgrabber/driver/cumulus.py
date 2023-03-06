import json

from napi.driver import CLIDriver
from napi.inventory import Device


class CumulusDriver(CLIDriver):
    def __init__(self, device: Device) -> None:
        super().__init__(device.ip or device.fqdn, device.vendor)
        self.device = device

    async def get_macs(self, vlan_id: str | None = None) -> list[dict[str, str]]:
        command = "net show bridge macs"
        if vlan_id is not None:
            command += f" vlan {vlan_id} json"
        else:
            command += " dynamic json"

        mac_table_json = await self.send_command(command)
        if mac_table_json == "":
            return []

        mac_table = json.loads(mac_table_json)

        return [
            {
                "vlan": entry["vlan"],
                "mac": entry["mac"],
                "interface": entry["ifname"],
            }
            for entry in mac_table
        ]

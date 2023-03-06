from typing import Any, Self

from napi.driver.abstract import BaseL2Interface, LinkType
# from napi.lib import _flatten


class L2Interface(BaseL2Interface):
    def to_cmd(self, clear: dict[str, Any] | None = None) -> list[str]:
        cmds = []

        if clear is not None:
            cmds.extend(
                [
                    f"sudo bridge vlan delete dev {self.name} vid {vlan['vlan']}"
                    for vlan in clear["vlans"]
                ]
            )

        if self.mode is LinkType.ACCESS:
            cmds.append(f"sudo bridge vlan add dev {self.name} vid {self.pvid} pvid untagged")

        if self.mode is LinkType.TRUNK:
            cmds.extend(
                [
                    f"sudo bridge vlan add dev {self.name} vid {vlan}"
                    for vlan in self.trunk_allowed_vlans
                ]
            )
            cmds.append(f"sudo bridge vlan add dev {self.name} vid {self.pvid} pvid untagged")

        return cmds

    @classmethod
    def from_data(cls, name: str, interface_info: dict[str, Any]) -> Self:
        for vlan_info in interface_info["vlans"]:
            if "flags" in vlan_info and "PVID" in vlan_info["flags"]:
                pvid = vlan_info["vlan"]
                break
        else:
            pvid = None

        interface = cls(
            name=name,
            mode=LinkType.ACCESS
            if len(interface_info["vlans"]) == 1 and pvid is not None
            else LinkType.TRUNK,
            pvid=pvid,
        )

        if interface.mode is LinkType.TRUNK:
            interface.trunk_allowed_vlans = [
                vlan_info["vlan"] for vlan_info in interface_info["vlans"]
            ]

        return interface

    # NVUE version
    # def to_cmd(self) -> list[str]:
    #     cmds = []
    #     if self.mode is LinkType.ACCESS:
    #         cmds.extend(
    #             [
    #                 f"nv unset interface {self.name} bridge domain br_default access",
    #                 f"nv unset interface {self.name} bridge domain br_default untagged",
    #                 f"nv unset interface {self.name} bridge domain br_default vlan",
    #                 f"nv set interface {self.name} bridge domain br_default access {self.pvid}",
    #             ]
    #         )
    #
    #     if self.mode is LinkType.TRUNK:
    #         cmds.extend(
    #             [
    #                 f"nv unset interface {self.name} bridge domain br_default access",
    #                 f"nv unset interface {self.name} bridge domain br_default untagged",
    #                 f"nv unset interface {self.name} bridge domain br_default vlan",
    #                 f"nv set interface {self.name} bridge domain br_default untagged {self.pvid}",
    #                 f"nv set interface {self.name} bridge domain br_default vlan {','.join([str(v) for v in self.trunk_allowed_vlans])}",
    #             ]
    #         )
    #
    #     cmds.append(
    #         "nv config apply",
    #     )
    #
    #     return cmds
    #
    # @classmethod
    # def from_data(cls, name: str, interface_info: dict[str, Any]) -> Self:
    #     interface = cls(
    #         name=name,
    #         mode=LinkType.ACCESS
    #         if interface_info["mode"].split("/")[0].lower() == "access"
    #         else LinkType.TRUNK,
    #         pvid=interface_info["iface_obj"]["native_vlan"],
    #     )
    #
    #     if interface.mode is LinkType.TRUNK:
    #         interface.trunk_allowed_vlans = [
    #             int(vlan) for vlan in _flatten(interface_info["iface_obj"]["vlan_list"])
    #         ]
    #
    #     return interface

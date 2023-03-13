from dataclasses import dataclass
from typing import Self

import httpx

from napi.logger import core_logger as logger
from napi.settings import settings

from .exceptions import InventoryException
from .inventory import Device, Interface, Vlans

NETBOX_DEVICE_SUFFIX = "/dcim/devices/"
NETBOX_INTERFACES_SUFFIX = "/dcim/interfaces/"
NETBOX_VLANS_SUFFIX = "/ipam/vlans/"

_translations = str.maketrans(
    {
        "/": "%2F",
        ":": "%3A",
    }
)


@dataclass
class Netbox:
    """
    Netbox gets network devices information from Netbox.
    """
    api_url: str = settings.nb_api_url

    def __post_init__(self):
        self.client = httpx.AsyncClient(verify=False)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_) -> None:
        await self.client.aclose()

    async def get_device(
        self,
        name: str,
        domains: list[str],
        roles: list[str] | None,
    ) -> Device:
        hostname = name.split(".")[0]

        if roles is not None:
            roles_str = "".join([f"&role={role}" for role in roles])
        else:
            roles = []

        for domain in domains:
            try:
                responce = (
                    await self.client.get(
                        f"{self.api_url}{NETBOX_DEVICE_SUFFIX}"
                        f"?name={hostname}.{domain}&status=active{roles_str}"
                    )
                ).json()
            except httpx.ConnectError as e:
                logger.critical(repr(e), exc_info=True)
                raise InventoryException("failed to connect to Netbox", element="connect")
            except Exception as e:
                logger.critical(repr(e), exc_info=True)
                raise InventoryException("unknown error", element="connect")

            devices = responce.get("results")
            if devices is None:
                msg = f"Invalid choices for fields {', '.join(responce)}"
                logger.critical(msg)
                raise InventoryException(msg, element="inventory")

            if devices:
                break
        else:
            raise InventoryException("there is no such switch in Netbox", element="switch")

        device = devices[0]

        return Device(
            fqdn=device["name"],
            vendor=device["device_type"]["manufacturer"]["slug"],
            model=device["device_type"]["slug"],
            tenant=device["tenant"]["slug"] if device["tenant"] else None,
            location=device["site"]["slug"],
            ip=device["primary_ip"]["address"].split("/")[0] if device["primary_ip"] else None,
        )

    async def get_interface(
        self,
        name: str,
        device: Device,
    ) -> Interface:
        normilized_name = name.translate(_translations)

        try:
            responce = (
                await self.client.get(
                    f"{self.api_url}{NETBOX_INTERFACES_SUFFIX}?name={normilized_name}&device={device.fqdn}"
                )
            ).json()
        except httpx.ConnectError as e:
            logger.critical(repr(e), exc_info=True)
            raise InventoryException("failed to connect to Netbox", element="connect")
        except Exception as e:
            logger.critical(repr(e), exc_info=True)
            raise InventoryException("unknown error", element="connect")

        interfaces = responce.get("results")
        if interfaces is None:
            msg = f"invalid choices for fields {', '.join(responce)}"
            logger.critical(msg)
            raise InventoryException(msg, element="inventory")

        if not interfaces:
            raise InventoryException(
                "there is no such interface on this switch in Netbox", element="interface"
            )

        interface = interfaces[0]

        responce = (
            await self.client.get(
                f"{self.api_url}{NETBOX_VLANS_SUFFIX}?role=setup&site={device.location}"
            )
        ).json()

        setup_vlans = responce.get("results")
        if setup_vlans is None:
            msg = f"invalid choices for fields {', '.join(responce)}"
            logger.critical(msg)
            raise InventoryException(msg, element="inventory")

        setup_vlan = setup_vlans[0]["vid"] if setup_vlans else None
        untagged_vlan = interface["untagged_vlan"]["vid"] if interface["untagged_vlan"] else None
        tagged_vlans = [vlan["vid"] for vlan in interface["tagged_vlans"]]

        return Interface(
            name=interface["name"],
            description=interface["description"],
            vlans=Vlans(
                setup=setup_vlan,
                untagged=untagged_vlan,
                tagged=tagged_vlans,
            ),
        )

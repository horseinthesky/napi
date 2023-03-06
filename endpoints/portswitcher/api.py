from fastapi import Depends
from fastapi.routing import APIRoute, APIRouter
from starlette.requests import Request
from starlette.responses import JSONResponse

from napi.auth import Bearer, User, get_user_from_request
from napi.driver.netconf.exceptions import netconf_http_code_map
from napi.inventory import (
    Device,
    Interface,
    InventoryException,
    inventory_handler,
    inventory_http_code_map,
)
from napi.settings import settings

from . import docs, models
from .driver import driver_map
from .driver.exceptions import portswitcher_http_code_map
from .logger import logger

CODES = {
    **portswitcher_http_code_map,
    **netconf_http_code_map,
}


async def _grab_inventory(
    switch_name: str, interface_name: str, user: User, request: Request
) -> tuple[Device, Interface]:
    async with inventory_handler("netbox") as inventory:
        try:
            device = await inventory.get_device(
                switch_name, domains=settings.domains, roles=["tor"]
            )
            interface = await inventory.get_interface(interface_name, device)
        except InventoryException as e:
            logger.warning(
                f"{user.name}'s ({request.client.host}) "
                f"request for {switch_name} {interface_name} "
                f"failed due to {e.message}"
            )

            result = {
                "code": inventory_http_code_map.get(e.element, 520),
                "status": "error",
                "message": str(e),
            }

            return JSONResponse(status_code=result["code"], content=result)

    # Validation
    if device.tenant not in settings.tenants:
        result = {
            "code": 403,
            "status": "error",
            "message": f"Access to switch in tenant '{device.tenant}' is "
            "prohibited from current deployment.",
        }

        logger.warning(
            f"{user.name}'s ({request.client.host}) "
            f"request for {switch_name} {interface_name} "
            f"failed due to {result['message']}"
        )

        return JSONResponse(status_code=result["code"], content=result)

    if interface.description != "Downlink":
        result = {
            "code": 403,
            "status": "error",
            "message": "You have no permission to switch a non-server-faced interface",
        }

        logger.warning(
            f"{user.name}'s ({request.client.host}) "
            f"request for {switch_name} {interface_name} "
            f"failed due to {result['message']}"
        )

        return JSONResponse(status_code=result["code"], content=result)

    if interface.vlans.setup is None:
        result = {
            "code": 404,
            "status": "error",
            "message": "there is no setup VLAN for switch location",
        }

        logger.warning(
            f"{user.name}'s ({request.client.host}) "
            f"request for {switch_name} {interface_name} "
            f"failed due to {result['message']}"
        )

        return JSONResponse(status_code=result["code"], content=result)

    if interface.vlans.untagged is None:
        result = {
            "code": 404,
            "status": "error",
            "message": "there is no native VLAN for this interface",
        }

        logger.warning(
            f"{user.name}'s ({request.client.host}) "
            f"request for {switch_name} {interface_name} "
            f"failed due to {result['message']}"
        )

        return JSONResponse(status_code=result["code"], content=result)

    if not interface.vlans.tagged:
        result = {
            "code": 404,
            "status": "error",
            "message": "there is no tagged VLANS for this interface",
        }

        logger.warning(
            f"{user.name}'s ({request.client.host}) "
            f"request for {switch_name} {interface_name} "
            f"failed due to {result['message']}"
        )

        return JSONResponse(status_code=result["code"], content=result)

    return device, interface


async def check(data: models.GetDeviceData, request: Request) -> JSONResponse:
    user: User = get_user_from_request(request)
    logger.info(f"Got a request from {user.name}: {data}")

    switch_name = data.switch.replace(" ", "")
    interface_name = data.interface.replace(" ", "")

    # Grabbing inventory
    inventory_response = await _grab_inventory(switch_name, interface_name, user, request)
    if isinstance(inventory_response, JSONResponse):
        return inventory_response

    device, interface = inventory_response

    # Device setup
    device_driver = driver_map.get(device.vendor)
    if device_driver is None:
        logger.warning(
            f"{user.name} ({request.client.host}) "
            f"failed to get {switch_name} {interface_name} state "
            f"due to {device.name} has {device.vendor} vendor "
            "which is not supported yet."
        )

        result = {
            "code": 501,
            "status": "error",
            "message": f"vendor {device.vendor} is not supported yet",
        }

        return JSONResponse(status_code=result["code"], content=result)

    try:
        async with device_driver(device=device, interface=interface) as d:
            state = await d.get_state()
    except Exception as e:
        code = CODES.get(e.__class__.__name__, 520)

        logger.warning(
            f"{user.name} ({request.client.host}) "
            f"failed to get {switch_name} {interface_name} state "
            f"due to {repr(e)}",
            exc_info=True,
        )

        result = {
            "code": code,
            "status": "error",
            "message": str(e)
            if code != 520
            else "unknownError: please contact your favorite networking dude",
        }

        return JSONResponse(status_code=result["code"], content=result)

    logger.info(
        f"{user.name} ({request.client.host}) "
        f"successfully got {switch_name} {interface_name} state"
    )

    result = {
        "code": 200,
        "status": "ok",
        "result": {
            "switch": device.fqdn,
            "interface": interface.name,
            "state": state,
        },
    }

    return JSONResponse(status_code=result["code"], content=result)


async def switch(data: models.PostDeviceData, request: Request) -> JSONResponse:
    """
    Examples:
    - (xh): **xh post http://{url}/api/portswitcher switch=leaf1 interface=100GE1/0/1:4 state=setup**
    - (httpie): **http POST http://{url}/api/portswitcher switch=leaf1 interface=100GE1/0/1:4 state=setup**
    - (curl): **curl -i -H "Content-Type: application/json" -X POST -d '{"switch":"leaf1", "interface":"100GE1/0/1:4", "state":"setup"}' http://{url}/api/portswitcher**
    """
    user: User = get_user_from_request(request)
    logger.info(f"Got a request from {user.name}: {data}")

    switch_name = data.switch.replace(" ", "")
    interface_name = data.interface.replace(" ", "")
    state = data.state

    inventory_response = await _grab_inventory(switch_name, interface_name, user, request)
    if isinstance(inventory_response, JSONResponse):
        return inventory_response

    device, interface = inventory_response

    device_driver = driver_map.get(device.vendor)
    if device_driver is None:
        logger.warning(
            f"{user.name} ({request.client.host}) "
            f"failed to get {switch_name} {interface_name} state "
            f"due to {device.name} has {device.vendor} vendor "
            "which is not supported yet."
        )

        result = {
            "code": 501,
            "status": "error",
            "message": f"{device.vendor} is not supported yet",
        }

        return JSONResponse(status_code=result["code"], content=result)

    try:
        async with device_driver(device=device, interface=interface) as d:
            await d.set_state(state)
    except Exception as e:
        code = CODES.get(e.__class__.__name__, 520)

        logger.warning(
            f"{user.name} ({request.client.host}) "
            f"failed to get {switch_name} {interface_name} state "
            f"due to {str(e)}",
            exc_info=True,
        )

        result = {
            "code": code,
            "status": "error",
            "message": str(e)
            if code != 520
            else "UnknownError: please contact your favorite netinfra dude",
        }

        return JSONResponse(status_code=result["code"], content=result)

    logger.info(
        f"{user.name} ({request.client.host}) "
        f"successfully switched {switch_name} {interface_name} to {state} state"
    )

    result = {
        "code": 200,
        "status": "ok",
        "result": {
            "switch": device.fqdn,
            "interface": interface.name,
            "state": state,
        },
    }

    return JSONResponse(status_code=result["code"], content=result)


portswitcher_router = APIRouter(
    routes=[
        APIRoute(
            "/portswitcher",
            check,
            methods=["GET"],
            tags=["PortSwitcher"],
            dependencies=[Depends(Bearer("portswitcher"))],
            summary="Get current interface state",
            description="Switch and Interface names are validated and current interface state is returned",
            response_description="Successfully got interface state",
            response_class=JSONResponse,
            response_model=docs.Success,
            responses={**docs.get_responses},
        ),
        APIRoute(
            "/portswitcher",
            switch,
            methods=["POST"],
            tags=["PortSwitcher"],
            dependencies=[Depends(Bearer("portswitcher"))],
            summary="Switch interface state",
            # description="Switch and Interface names are validated and switch interface is switched to desired state",
            response_description="Interface successfully switched",
            response_class=JSONResponse,
            response_model=docs.Success,
            responses={**docs.post_responses},
        ),
    ],
)

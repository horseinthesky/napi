from fastapi import Depends
from fastapi.routing import APIRoute, APIRouter
from starlette.requests import Request
from starlette.responses import JSONResponse

from napi.auth import Bearer, User, get_user_from_request
from napi.driver.netconf.exceptions import netconf_http_code_map
from napi.inventory import InventoryException, inventory_handler, inventory_http_code_map
from napi.settings import settings

from . import docs, models
from .driver import driver_map
from .driver.exceptions import macgrabber_http_code_map
from .logger import logger

CODES = {
    **macgrabber_http_code_map,
    **netconf_http_code_map,
}


async def get(data: models.GetDeviceData, request: Request):
    user: User = get_user_from_request(request)
    logger.info(f"Got a request from {user.name}: {data}")

    switch_name = data.switch.replace(" ", "")
    vlan = data.vlan

    async with inventory_handler("netbox") as inventory:
        try:
            device = await inventory.get_device(
                switch_name, domains=settings.domains, roles=["tor"]
            )
        except InventoryException as e:
            logger.warning(
                f"{user.name}'s ({request.client.host}) "
                f"request for {switch_name} "
                f"failed due to {e.message}"
            )

            result = {
                "code": inventory_http_code_map.get(e.element, 520),
                "status": "error",
                "message": str(e),
            }

            return JSONResponse(status_code=result["code"], content=result)

    # Device setup
    device_driver = driver_map.get(device.vendor)
    if device_driver is None:
        logger.warning(
            f"{user.name} ({request.client.host}) "
            f"failed to get {switch_name} mac-addresses "
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
        async with device_driver(device=device) as d:
            macs = await d.get_macs(vlan)
    except Exception as e:
        code = CODES.get(e.__class__.__name__, 520)

        logger.warning(
            f"{user.name} ({request.client.host}) "
            f"failed to get {switch_name} mac-addresses "
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

    logger.debug("{} successfully got {} macs".format(request.client.host, switch_name))

    result = {
        "code": 200,
        "status": "ok",
        "result": {
            "switch": switch_name,
            "macs": macs,
        },
    }

    return JSONResponse(status_code=result["code"], content=result)


macgrabber_router = APIRouter(
    routes=[
        APIRoute(
            "/macgrabber",
            get,
            methods=["GET"],
            tags=["MacGrubber"],
            dependencies=[Depends(Bearer("macgrabber"))],
            summary="Get switch dynamic mac-addresses table",
            description="Switch hostname is validated and dynamic mac-address table is returned",
            response_description="Successfully got mac-addresses",
            response_class=JSONResponse,
            response_model=docs.Success,
            responses={**docs.get_responses},
        ),
    ],
)

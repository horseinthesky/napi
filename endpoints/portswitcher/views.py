import datetime
from dataclasses import dataclass

import typesystem
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates, _TemplateResponse

from napi.inventory import InventoryException, inventory_handler
from napi.settings import settings

from .driver import driver_map
from .logger import logger

forms = typesystem.Jinja2Forms(package="bootstrap4")
templates = Jinja2Templates(directory="endpoints/portswitcher/templates")
statics = StaticFiles(directory="endpoints/portswitcher/statics", packages=["bootstrap4"])


form_schema = typesystem.Schema(
    fields={
        "switch": typesystem.String(title="Switch name", max_length=50),
        "interface": typesystem.String(title="Interface name", max_length=15),
        "state": typesystem.Choice(
            title="Desired state",
            choices=[
                ("prod", "prod"),
                ("setup", "setup"),
            ],
        ),
    }
)


@dataclass
class Toggling:
    switch: str
    interface: str
    state: str

    def __post_init__(self):
        self.toggle_time = datetime.datetime.now().strftime("%H:%M:%S (%Y-%m-%d)")

    def __repr__(self) -> str:
        return f'{self.switch} {self.interface} was switched to "{self.state}" state at {self.toggle_time}'


togglings: list[Toggling] = []


def render(
    request: Request, form=forms.create_form(form_schema), ps_status: str | None = None
) -> _TemplateResponse:
    context = {
        "request": request,
        "form": form,
        "togglings": togglings,
        "ps_status": ps_status,
    }

    return templates.TemplateResponse("index.html", context)


async def switch(request: Request) -> _TemplateResponse:
    if request.method == "GET":
        return render(request)

    global togglings

    data = await request.form()

    form = forms.create_form(form_schema)
    form.validate(data)
    if form.errors:
        return render(request, form)

    toggling = Toggling(**data)
    switch_name = toggling.switch.replace(" ", "")
    interface_name = toggling.interface.replace(" ", "")
    state = toggling.state

    # Grabbing inventory
    async with inventory_handler("netbox") as inventory:
        try:
            device = await inventory.get_device(
                switch_name, roles=["tor"], domains=settings.domains
            )
            interface = await inventory.get_interface(interface_name, device)
        except InventoryException as e:
            logger.warning(
                f"request from {request.client.host} "
                f"for {switch_name} {interface_name} "
                f"failed due to {e.message}"
            )

            if e.element in ["switch", "interface"]:
                form.errors = {e.element: e.message}
                return render(request, form)

            return render(request, form, e.message)

    # Validation
    if device.tenant not in settings.tenants:
        msg = (
            f"access to switch in tenant '{device.tenant}' is "
            "prohibited from current deployment."
        )

        form.errors = {"switch": msg}

        logger.warning(
            f"request from {request.client.host} "
            f"for {switch_name} {interface_name} "
            f"failed due to {msg}"
        )

        return render(request, form)

    if interface.description != "Downlink":
        msg = "you have no permission to switch a non-server-faced interface"

        form.errors = {"interface": msg}

        logger.warning(
            f"request from {request.client.host} "
            f"for {switch_name} {interface_name} "
            f"failed due to {msg}"
        )

        return render(request, form)

    if interface.vlans.setup is None:
        msg = "there is no setup VLAN for switch location"
        form.errors = {"switch": msg}

        logger.warning(
            f"request from {request.client.host} "
            f"for {switch_name} {interface_name} "
            f"failed due to {msg}"
        )

        return render(request, form)

    if interface.vlans.untagged is None:
        msg = "there is no native VLAN for this interface"
        form.errors = {"interface": msg}

        logger.warning(
            f"request from {request.client.host} "
            f"for {switch_name} {interface_name} "
            f"failed due to {msg}"
        )

        return render(request, form)

    if not interface.vlans.tagged:
        msg = "there is no tagged VLANS for this interface"
        form.errors = {"interface": msg}

        logger.warning(
            f"request from {request.client.host} "
            f"for {switch_name} {interface_name} "
            f"failed due to {msg}"
        )

        return render(request, form)

    # Device setup
    device_driver = driver_map.get(device.vendor)
    if device_driver is None:
        logger.warning(
            f"{request.client.host} "
            f"failed to get {switch_name} {interface_name} state "
            f"due to {device.name} has {device.vendor} vendor "
            "which is not supported yet."
        )

        form.errors = {"switch": f"vendor {device.vendor} is not supported yet"}

        return render(request, form)

    try:
        async with device_driver(device=device, interface=interface) as d:
            await d.set_state(state)
    except Exception as e:
        logger.warning(
            f"{request.client.host} failed to get {switch_name} {interface_name} state due to {str(e)}"
        )

        return render(request, form, str(e))

    logger.info(
        f'{request.client.host} successfully switched {switch_name} {interface_name} to "{state}" state'
    )
    toggling.toggle_time = datetime.datetime.now().strftime("%H:%M:%S (%Y-%m-%d)")
    togglings.append(toggling)
    togglings = togglings[-5:]

    return render(request)


portswitcher_app = Starlette(
    routes=[
        Route("/", switch, methods=["GET", "POST"]),
        Mount("/statics", statics, name="static"),
    ],
)

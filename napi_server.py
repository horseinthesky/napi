import importlib
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from endpoints.ping import ping_router
from napi.auth import init_auth_database
from napi.custom_handlers import http422_error_handler
from napi.logger import core_logger
from napi.settings import ENDPOINTS_DIR, ENV, settings

app = FastAPI(
    title="Network API",
    description="An API for managing your network",
    version="0.0.1",
    swagger_ui_parameters={"syntaxHighlight.theme": "nord"},
)

app.add_exception_handler(RequestValidationError, http422_error_handler)
app.on_event("startup")(init_auth_database)
app.include_router(ping_router)

for endpoint in settings.endpoints:
    module_path = Path(f"{ENDPOINTS_DIR}/{endpoint}")
    if not module_path.is_dir() and not module_path.with_suffix(".py").is_file():
        msg = f"endpoint '{endpoint}' not found"
        core_logger.error(msg)
        raise ModuleNotFoundError(msg)

    module = importlib.import_module(f"{ENDPOINTS_DIR}.{endpoint}")

    try:
        router = getattr(module, f"{endpoint}_router")
    except AttributeError:
        core_logger.error(f"endpoint '{endpoint}' router not found")
        raise

    app.include_router(router, prefix="/api")
    core_logger.info(f"included endpoint '{endpoint}' router")

    try:
        view = getattr(module, f"{endpoint}_app")
    except AttributeError:
        core_logger.warning(f"endpoint '{endpoint}' view not found")
        continue
    else:
        core_logger.info(f"mounted endpoint '{endpoint}' view")

    app.mount(f"/{endpoint}", view)


core_logger.info(f"running napi in _{ENV}_ configuration")

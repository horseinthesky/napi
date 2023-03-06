from enum import StrEnum

from fastapi.routing import APIRoute, APIRouter
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse


class Status(StrEnum):
    ok = "ok"


class Success(BaseModel):
    code: int = 200
    status: Status = Status.ok


async def ping(request: Request) -> JSONResponse:
    result = {
        "code": 200,
        "status": "ok",
    }
    return JSONResponse(status_code=200, content=result)


ping_router = APIRouter(
    routes=[
        APIRoute(
            "/ping",
            ping,
            methods=["GET"],
            tags=["Ping"],
            summary="Check API health",
            response_description="API is operational",
            response_class=JSONResponse,
            response_model=Success,
        ),
    ],
)

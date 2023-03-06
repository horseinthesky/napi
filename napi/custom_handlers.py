from typing import Union

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError, ValidationError
from starlette.responses import JSONResponse


async def http422_error_handler(
    _: Request,
    exc: Union[RequestValidationError, ValidationError],
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "status": "error",
            "message": "; ".join([f"{e['loc'][-1]}: {e['msg']}" for e in exc.errors()]),
        },
    )

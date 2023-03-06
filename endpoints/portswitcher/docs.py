from enum import StrEnum

from pydantic import BaseModel


class Status(StrEnum):
    ok = "ok"
    error = "error"


class State(StrEnum):
    prod = "prod"
    setup = "setup"
    unknown = "unknown"
    l3 = "l3"


class Result(BaseModel):
    switch: str
    interface: str
    state: State


class Error(BaseModel):
    code: int
    status: Status = Status.error
    message: str


class Success(BaseModel):
    code: int
    status: Status = Status.ok
    result: Result


get_responses = {
    400: {
        "description": "Switch configuration issue",
        "model": Error,
    },
    403: {
        "description": "Invalid token"
        " or User has no permissions to work with this endpoint"
        " or Attempt to switch non-server-faced interface"
        " or prohibited tenant",
        "model": Error,
    },
    404: {
        "description": "Some Netbox data is missing",
        "model": Error,
        "content": {
            "application/json": {
                "example": {
                    "code": 404,
                    "status": "error",
                    "message": "There is no such interface on this switch in Netbox",
                }
            }
        },
    },
    507: {
        "description": "Switch commit error",
        "model": Error,
    },
    509: {
        "description": "Switch NETCONF session limit exceeded",
        "model": Error,
    },
    511: {
        "description": "Failed to authenticate on the switch",
        "model": Error,
    },
    520: {
        "description": "Unknown error",
        "model": Error,
    },
    522: {
        "description": "Switch connection timeout",
        "model": Error,
    },
    523: {
        "description": "Failed to connect to switch",
        "model": Error,
    },
}

post_responses = {
    403: {
        "description": "No permission to switch a non-server-faced interface",
        "model": Error,
    },
    **get_responses,
}

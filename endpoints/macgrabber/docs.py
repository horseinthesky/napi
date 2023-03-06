from enum import StrEnum

from pydantic import BaseModel


class Status(StrEnum):
    ok = 'ok'
    error = 'error'


class Mac(BaseModel):
    vlan: str
    mac: str
    interface: str


class Result(BaseModel):
    switch: str
    macs: list[Mac]


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
        'description': 'Switch configuration issue',
        'model': Error
    },
    401: {
        'description': 'Failed to authenticate on switch',
        'model': Error
    },
    404: {
        'description': 'Some Netbox data is missing',
        'model': Error,
        'content': {
            'application/json': {
                'example': {
                    'code': 404,
                    'status': 'error',
                    'message': 'There is no such swtch in Netbox'
                }
            }
        }
    },
    408: {
        'description': 'Connection to switch timed out',
        'model': Error
    },
    422: {
        'description': 'Validation Error',
        'model': Error
    },
    503: {
        'description': 'Failed to connect to Netbox or switch',
        'model': Error
    },
    520: {
        'description': 'Unknown error',
        'model': Error
    },
}

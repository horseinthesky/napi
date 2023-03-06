from enum import StrEnum, auto

from pydantic import BaseModel, validator


class AutoName(StrEnum):
    def _generate_next_value_(name, *_):
        return name.lower()


class DesiredState(AutoName):
    PROD = auto()
    SETUP = auto()


def switch_name_len(name):
    if len(name) > 50:
        raise ValueError("switch name is too long")
    return name


def interface_name_len(name):
    if len(name) > 15:
        raise ValueError("interface name is too long")
    return name


class GetDeviceData(BaseModel):
    switch: str
    interface: str

    _validate_switch_name = validator("switch", allow_reuse=True)(switch_name_len)
    _validate_interface_name = validator("interface", allow_reuse=True)(interface_name_len)


class PostDeviceData(BaseModel):
    switch: str
    interface: str
    state: DesiredState

    _validate_switch_name = validator("switch", allow_reuse=True)(switch_name_len)
    _validate_interface_name = validator("interface", allow_reuse=True)(interface_name_len)

from pydantic import BaseModel, validator


def is_digit(name):
    if not name.isdigit():
        raise ValueError("vlan must be a digit")
    return name


class GetDeviceData(BaseModel):
    switch: str
    vlan: str | None = None

    _validate_vlan = validator("vlan", allow_reuse=True)(is_digit)
